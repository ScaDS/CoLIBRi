import logging
import os
import sys

from chatbot_logic import Chatbot
from dotenv import load_dotenv
from flask import Flask
from flask_restful import Api, Resource, request
from search_engine import EmbeddingSearchEngine, RemoteEmbeddingSearchEngine

# --- logging setup: do this only once ---
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
# remove default interfering logging handlers that gunicorn might have added
for h in list(root_logger.handlers):
    root_logger.removeHandler(h)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter(
    "[%(asctime)s +0000] [%(process)d] [%(levelname)s] [%(name)s] %(message)s",
    "%Y-%m-%d %H:%M:%S",
))
root_logger.addHandler(handler)
# --- end logging setup ---

LOGGER = logging.getLogger(__name__)

app = Flask(__name__)
api = Api(app)


load_dotenv()
retrieval_method = os.getenv("RETRIEVAL_METHOD")
search_engine_instance = None
chatbot_instance = None

try:
    if retrieval_method == "LOCAL":
        search_engine_instance = EmbeddingSearchEngine()
    elif retrieval_method == "REMOTE":
        search_engine_instance = RemoteEmbeddingSearchEngine()
    else:
        raise ValueError(f"Can not infer search engine type for unknown RETRIEVAL_METHOD: {retrieval_method}")
    search_engine_instance.create_index()
except Exception as e:
    LOGGER.error("Error while initializing search engine: %s", e if isinstance(e, str) else repr(e))

try:
    chatbot_instance = Chatbot(search_engine_instance)
except Exception as e:
    LOGGER.error("Error while initializing chatbot: %s", e if isinstance(e, str) else repr(e))

def build_error_response(error: str, messages=None) -> dict[str, str]:
    if messages is None:
        messages = []
    messages.append({ "role": "assistant", "content": error })
    return messages

class Retrieval(Resource):
    """
    API Endpoint for performing pure retrieval.
    The request must contain the 'query' field, and it will return a list of the IDs of the 10 best matching drawings,
    according to the search engine.
    """
    def post(self):
        try:
            data = request.get_json()
            query = data["query"]
            retrieved_drawing_ids = search_engine_instance.retrieve_drawings(query)
            return {"results": retrieved_drawing_ids}, 200
        except Exception as e:
            return {"error": "internal error " + str(e)}, 500

class ChatbotResponse(Resource):
    """
    Combined API Endpoint for the chatbot backend.
    It supports performing a new retrieval, or answering questions about the results of a previous retrieval.
    Args:
        - messages: Complete list of the previous chat in the OpenAI message format.
        - technical_drawing_ids: List of the IDs of the 10 drawings from the previous retrieval.
    Returns:
        - messages: List of chat messages with a new Assistant response appended at the end.
        - technical_drawing_ids: List of new IDs in case a new search was performed, previous list of IDs otherwise.
        - update:
    """
    def post(self):
        try:
            data = request.get_json()
            messages = data["messages"]
            drawing_ids = data["technical_drawing_ids"]
        except Exception as e:
            LOGGER.error("Error while parsing the request data: %s", e if isinstance(e, str) else repr(e))
            return {
                "messages": build_error_response("Internal error while parsing the request data.", messages),
                "technical_drawing_ids": [],
                "update": False
            }

        if not chatbot_instance:
            return {
                "messages": build_error_response("Internal error while initializing the chatbot.", messages),
                "technical_drawing_ids": drawing_ids,
                "update": False
            }

        try:
            user_message = messages[-1]["content"]
            response, updated_drawing_ids, update = chatbot_instance.execute_with_tool_calls(
                user_message=user_message,
                drawing_ids=drawing_ids,
            )
            messages.append({ "role": "assistant", "content": response })
            return {"messages": messages, "technical_drawing_ids": updated_drawing_ids, "update": update}
        except Exception as e:
            LOGGER.error("Error while generating the chatbot response: %s", e if isinstance(e, str) else repr(e))
            return {
                "messages": build_error_response("Internal error while generating the chatbot response.", messages),
                "technical_drawing_ids": drawing_ids,
                "update": False
            }

class ChatbotResponseWithDrawing(Resource):
    def post(self):
        raise NotImplementedError
        # TODO Endpoint for requests with both a user message and a drawing

api.add_resource(Retrieval, "/retrieve")
api.add_resource(ChatbotResponse, "/chatbot")
api.add_resource(ChatbotResponseWithDrawing, "/chatbotdrawing")

LOGGER.info("ConvSearch backend initialized successfully.")

if __name__ == "__main__":
    app.run()
