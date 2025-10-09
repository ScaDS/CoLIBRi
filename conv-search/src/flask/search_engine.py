"""
This file contains all the different SearchEngine classes, that will be used for the retrieval,
as well as the method to instantiate a given SearchEngine.
"""

import os

import requests
import Stemmer
from llama_index.core import Settings
from llama_index.core.indices import MultiModalVectorStoreIndex, VectorStoreIndex, load_index_from_storage
from llama_index.core.schema import ImageNode, TextNode
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.vector_stores import SimpleVectorStore

# from llama_index.core.vector_stores import VectorStoreQuery, VectorStoreQueryMode, VectorStoreQueryResult
from llama_index.core.vector_stores.types import VectorStoreQuery, VectorStoreQueryMode, VectorStoreQueryResult
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.multi_modal_llms.ollama import OllamaMultiModal
from llama_index.retrievers.bm25 import BM25Retriever
from utils import get_remote_api_key, send_request_to_database


class SearchEngine:
    """
    Base Class for all the different search engines.
    Main methods are create_index and retrieve_drawings.
    """

    def create_index(self):
        """
        Abstract method, where different search engines create the index in different ways.
        Creates an index for the specific type of retrieval of the search engine and saves the index to
        disk (inside the docker container).
        """
        pass

    def retrieve_drawings(self, query):
        """
        Performs a retrieval on the index using the retrieval method specified in .env
        (either bm25 or embedding search or CLIP).
        Results are in the form of the drawing_ids of the 10 best matches.

        Args:
            query: Text query for the retrieval.

        Returns:
            assistant_response: A message in the OpenAI message format containing the text response that the assistant
                                should give along with the search.
            updated_technical_drawing_ids: List of 10 drawing_ids of the best retrieval results.
        """
        results = self._retrieve(query)
        print("Retrieved the following drawings:\n" + str(results))
        updated_technical_drawing_ids = [drawing["drawing_id"] for drawing in results]
        assistant_response = {"role": "assistant", "content": "Ich habe diese 10 Zeichnungen gefunden."}
        return assistant_response, updated_technical_drawing_ids

    def _retrieve(self, query):
        """
        Abstract method for retrieving drawings based on a query from the index.
        """
        pass

    def _fetch_docs_as_text_nodes(self):
        # Fetch all SearchDatas from the database
        response, is_ok = send_request_to_database("/searchdata/get-all", type="get")

        # Construct list of TextNodes from the drawings, these will be used for the index creation
        text_nodes = []
        if is_ok:
            for d in response:
                new_node = TextNode(
                    text=d["llm_text"], embedding=d["llm_vector"], metadata={"drawing_id": d["drawing_id"]}
                )
                text_nodes.append(new_node)
        return text_nodes

    def _fetch_docs_as_image_nodes(self):
        response, is_ok = send_request_to_database("/searchdata/get-all", type="get")
        print("Fetched", flush=True)
        image_nodes = []
        if is_ok:
            for d in response:
                print("a", flush=True)
                # new_node = uri_to_image_node(d["original_drawing"], d["drawing_id"])
                node = ImageNode(metadata={"drawing_id": d["drawing_id"]})
                node.image = d[
                    "original_drawing"
                ]  # manually set the image str attribute of the ImageNode because we can't pass it in the constructor
                image_nodes.append(node)

            print(image_nodes[0], flush=True)
        return image_nodes


class BM25SearchEngine(SearchEngine):
    """
    Search Engine that uses BM25 (normal tf-idf like retrieval) for the retrieval.
    """

    def create_index(self):
        """
        Create DocumentStore and BM25Retriever for BM25 retrieval on the given text_nodes; save both to disk
        """
        text_nodes = self._fetch_docs_as_text_nodes()
        file_dir = os.path.dirname(os.path.abspath(__file__))
        docstore = SimpleDocumentStore()
        docstore.add_documents(text_nodes)
        bm25_retriever = BM25Retriever.from_defaults(
            docstore=docstore, similarity_top_k=10, stemmer=Stemmer.Stemmer("german"), language="german"
        )
        docstore.persist(os.path.join(file_dir, "docstore"))
        bm25_retriever.persist(os.path.join(file_dir, "bm25_retriever"))

    def _retrieve(self, query):
        """
        Retrieves top 10 drawings using BM25 algorithm.

        Args:
            query: Text query for the retrieval, should include technical keywords that appear in the database

        Returns:
            List of dicts containing "drawing_id" and "text" fields, in order of search matching
        """
        file_dir = os.path.dirname(os.path.abspath(__file__))
        retriever_dir = os.path.join(file_dir, "bm25_retriever")
        bm25_retriever = BM25Retriever.from_persist_dir(retriever_dir)
        nodes = bm25_retriever.retrieve(query)
        return [{"drawing_id": n.node.metadata["drawing_id"], "text": n.node.text} for n in nodes]


class CLIPSearchEngine(SearchEngine):
    """
    Search Engine that uses CLIP image embeddings for the retrieval.
    """

    def create_index(self):
        print("Creating index. This may take a few minutes.", flush=True)
        image_nodes = self._fetch_docs_as_image_nodes()
        vector_store = SimpleVectorStore()
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        mm_llm = OllamaMultiModal(model="gemma3:12b", request_timeout=300, base_url="http://172.26.44.37:11434")
        index = MultiModalVectorStoreIndex(nodes=image_nodes, multi_modal_llm=mm_llm, storage_context=storage_context)
        file_dir = os.path.dirname(os.path.abspath(__file__))
        index_dir = os.path.join(file_dir, "index")
        index.storage_context.persist(persist_dir=index_dir)

    def _retrieve(self, query):
        file_dir = os.path.dirname(os.path.abspath(__file__))
        index_dir = os.path.join(file_dir, "index")
        storage_context = StorageContext.from_defaults(persist_dir=index_dir)
        index = load_index_from_storage(storage_context)
        retriever_engine = index.as_retriever(similarity_top_k=10, image_similarity_top_k=10)

        retrieval_results = retriever_engine.text_to_image_retrieve(query)

        results = [
            {
                "drawing_id": n.node.metadata["drawing_id"],
            }
            for n in retrieval_results
        ]
        return results


class EmbeddingSearchEngine(SearchEngine):
    """
    Search Engine that uses text embeddings for the retrieval.
    """

    def create_index(self):
        """
        Set global embed model, this model will be used for the embedding similarity search.
        Create and save VectorStoreIndex for embedding-based retrieval
        """
        text_nodes = self._fetch_docs_as_text_nodes()
        LOCAL_EMBED_MODEL = os.getenv("LOCAL_EMBED_MODEL")
        Settings.embed_model = HuggingFaceEmbedding(model_name=LOCAL_EMBED_MODEL)
        file_dir = os.path.dirname(os.path.abspath(__file__))
        vector_store = SimpleVectorStore()
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex(text_nodes, storage_context)
        index_dir = os.path.join(file_dir, "index")
        index.storage_context.persist(persist_dir=index_dir)

        self.storage_context = StorageContext.from_defaults(persist_dir=index_dir)

    def _retrieve(self, query):
        """
        Retrieves top 10 drawings using embedding similarity of text representations of drawing.

        Args:
            query: Query for the retrieval, should contain information about wanted drawings, does not need to contain
                   technical keywords.

        Returns:
            List of dicts containing "drawing_id" and "text" fields, in order of search matching
        """
        index = load_index_from_storage(self.storage_context)
        retriever_engine = index.as_retriever(similarity_top_k=10)
        retrieval_results = retriever_engine.retrieve(query)
        results = [
            {
                "drawing_id": n.node.metadata["drawing_id"],
                "text": n.node.text,
            }
            for n in retrieval_results
        ]
        return results


class RemoteEmbeddingSearchEngine(SearchEngine):
    def create_index(self):
        """
        Sets global embed_model to None, because we do not need a local embed model, as we use the Remote API for this.
        Create and save VectorStoreIndex for embedding-based retrieval. Then keep it in memory in self.storage_context
        for fast retrieval times
        """
        text_nodes = self._fetch_docs_as_text_nodes()
        Settings.embed_model = None
        file_dir = os.path.dirname(os.path.abspath(__file__))
        index_dir = os.path.join(file_dir, "index")
        vector_store = SimpleVectorStore()
        self.storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex(text_nodes, self.storage_context)
        # For some reason, we have to save and load the index again, otherwise it will be empty
        index.storage_context.persist(persist_dir=index_dir)
        self.storage_context = StorageContext.from_defaults(
            persist_dir=index_dir
        )  # Save index in variable in memory, so it's faster when we don't have to load it from disk during retrieval

    def _retrieve(self, query):
        vector_store: SimpleVectorStore = self.storage_context.vector_store
        docstore = self.storage_context.docstore
        embedding = embed_query_remote(query)  # Use Remote API to embed model
        vs_query = VectorStoreQuery(
            query_embedding=embedding,
            similarity_top_k=10,
            mode=VectorStoreQueryMode.DEFAULT,
        )
        result: VectorStoreQueryResult = vector_store.query(vs_query)  # Search on the vector store
        nodes = [
            docstore.get_node(node_id) for node_id in result.ids
        ]  # result only contains Document IDs, use docstore to map back to our nodes for drawing_ids
        output = [
            {"drawing_id": n.metadata["drawing_id"], "text": n.text, "score": s}
            for n, s in zip(nodes, result.similarities, strict=True)
        ]
        return output


class ColpaliSearchEngine(SearchEngine):
    """
    We can try using the Byaldi library for the Colpali-based retrieval. Not sure if it would perform any good.
    """

    def create_index(self):
        raise NotImplementedError("ColpaliSearchEngine has not been implemented yet.")

    def _retrieve(self, query):
        raise NotImplementedError("ColpaliSearchEngine has not been implemented yet.")


def create_search_engine(retrieval_method):
    if retrieval_method == "EMBEDDING":
        search_engine = EmbeddingSearchEngine()
    elif retrieval_method == "BM25":
        search_engine = BM25SearchEngine()
    elif retrieval_method == "CLIP":
        search_engine = CLIPSearchEngine()
    elif retrieval_method == "COLPALI":
        search_engine = ColpaliSearchEngine()
    elif retrieval_method == "REMOTE_EMBEDDING":
        search_engine = RemoteEmbeddingSearchEngine()
    else:
        raise ValueError(f"Unknown Search engine type {retrieval_method}")
    return search_engine


def embed_query_remote(query: str):
    REMOTE_EMBED_MODEL = os.getenv("REMOTE_EMBED_MODEL")
    import json

    payload = {
        "model": REMOTE_EMBED_MODEL,
        "input": query,
    }
    token = get_remote_api_key()
    url = os.getenv("REMOTE_URL") + "/embeddings"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    # API Request
    response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=600)
    if response.ok:
        embedding = response.json()["data"][0]["embedding"]
    else:
        raise ValueError("No valid response from Remote")
    return embedding
