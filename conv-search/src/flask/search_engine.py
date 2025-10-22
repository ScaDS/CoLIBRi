import json
import logging
import os

import requests
from llama_index.core import Settings
from llama_index.core.indices import VectorStoreIndex, load_index_from_storage
from llama_index.core.schema import ImageNode, TextNode
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.core.vector_stores.types import VectorStoreQuery, VectorStoreQueryMode, VectorStoreQueryResult
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from utils import get_remote_api_key, send_request_to_database


LOGGER = logging.getLogger(__name__)

class SearchEngine:
    """
    Base Class for all the different search engines that may be used for retrieval.
    Main methods are create_index and retrieve_drawings.
    """

    def create_index(self):
        """
        Abstract method, where different search engines create the index in different ways.
        Creates an index for the specific type of retrieval of the search engine and saves the index to
        disk (inside the docker container).
        """
        pass

    def retrieve_drawings(self, query: str):
        """
        Performs a retrieval on the index using the retrieval method specified in .env
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
        assistant_response = {"role": "assistant", "content": "I found these drawings."}
        return assistant_response, updated_technical_drawing_ids

    def _retrieve(self, query: str):
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
        LOGGER.info(f"Retrieved text nodes from database searchdata: {len(text_nodes)}")
        return text_nodes

    def _fetch_docs_as_image_nodes(self):
        response, is_ok = send_request_to_database("/searchdata/get-all", type="get")
        image_nodes = []
        if is_ok:
            for d in response:
                node = ImageNode(metadata={"drawing_id": d["drawing_id"]})
                # manually set the image str attribute of the ImageNode because we can't pass it in the constructor
                node.image = d["original_drawing"]
                image_nodes.append(node)
        LOGGER.info(f"Retrieved image nodes from database searchdata: {len(image_nodes)}")
        return image_nodes


class EmbeddingSearchEngine(SearchEngine):
    """
    Search Engine that uses local text embedding model for the retrieval.
    """

    def __init__(self):
        self.storage_context = None

    def create_index(self):
        """
        Set global embed model, this model will be used for the embedding similarity search.
        Create and save VectorStoreIndex for embedding-based retrieval.
        Then keep it in memory in self.storage_context for fast retrieval times.
        """
        local_embed_model = os.getenv("LOCAL_EMBED_MODEL")
        if local_embed_model is None:
            raise ValueError("LOCAL_EMBED_MODEL environment variable is not set")
        Settings.embed_model = HuggingFaceEmbedding(model_name=local_embed_model)
        text_nodes = self._fetch_docs_as_text_nodes()
        file_dir = os.path.dirname(os.path.abspath(__file__))
        index_dir = os.path.join(file_dir, "index")
        vector_store = SimpleVectorStore()
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex(text_nodes, storage_context=storage_context)
        index.storage_context.persist(persist_dir=index_dir)

        self.storage_context = StorageContext.from_defaults(persist_dir=index_dir)

    def _retrieve(self, query: str):
        """
        Retrieves top 10 drawings using embedding similarity of text representations of drawing.
        Args:
            query: Retrieval query, should contain information about drawings, does not need technical keywords.
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
    """
    Search Engine that uses remote text embedding model for the retrieval.
    """

    def __init__(self):
        self.storage_context = None

    def create_index(self):
        """
        Sets global embed_model to None, because we do not need a local embed model, as we use the Remote API for this.
        Create and save VectorStoreIndex for embedding-based retrieval.
        Then keep it in memory in self.storage_context for fast retrieval times.
        """
        Settings.embed_model = None
        text_nodes = self._fetch_docs_as_text_nodes()
        file_dir = os.path.dirname(os.path.abspath(__file__))
        index_dir = os.path.join(file_dir, "index")
        vector_store = SimpleVectorStore()
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex(text_nodes, storage_context=storage_context)
        index.storage_context.persist(persist_dir=index_dir)

        self.storage_context = StorageContext.from_defaults(persist_dir=index_dir)

    def _embed_query_remote(self, query: str):
        """
        Call remote embedding model to create an embedding for the query.
        Args:
            query: Retrieval query, should contain information about drawings, does not need technical keywords.
        Returns:
            Embedded query
        """
        remote_embed_model = os.getenv("REMOTE_EMBED_MODEL")
        if remote_embed_model is None:
            raise ValueError("REMOTE_EMBED_MODEL environment variable is not set")

        token = get_remote_api_key()
        url = os.getenv("REMOTE_URL") + "/embeddings"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "model": remote_embed_model,
            "input": query,
        }
        # API Request
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=600)
        if response.ok:
            embedding = response.json()["data"][0]["embedding"]
        else:
            raise ValueError("No valid response from remote embedding model", response)
        return embedding

    def _retrieve(self, query: str):
        """
        Retrieves top 10 drawings using embedding similarity of text representations of drawing.
        Args:
            query: Retrieval query, should contain information about drawings, does not need technical keywords.
        Returns:
            List of dicts containing "drawing_id" and "text" fields, in order of search matching
        """
        vector_store: SimpleVectorStore = self.storage_context.vector_store
        docstore = self.storage_context.docstore
        # Use Remote API to create embedding
        embedding = self._embed_query_remote(query)
        vs_query = VectorStoreQuery(
            query_embedding=embedding,
            similarity_top_k=10,
            mode=VectorStoreQueryMode.DEFAULT,
        )
        result: VectorStoreQueryResult = vector_store.query(vs_query)  # Search on the vector store
        # result only contains Document IDs, use docstore to map back to our nodes for drawing_ids
        nodes = [docstore.get_node(node_id) for node_id in result.ids]
        output = [
            {"drawing_id": n.metadata["drawing_id"], "text": n.text, "score": s}
            for n, s in zip(nodes, result.similarities, strict=True)
        ]
        return output
