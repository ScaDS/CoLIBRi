import logging
import os

from chatbot_logic import convert_drawings_to_message, execute_tool_calls, get_tool_calls
from dotenv import load_dotenv
from flask_restful import Api, Resource, request
from search_engine import EmbeddingSearchEngine, RemoteEmbeddingSearchEngine

from flask import Flask

LOGGER = logging.getLogger(__name__)

app = Flask(__name__)
api = Api(app)


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
            _, retrieved_drawing_ids = search_engine_instance.retrieve_drawings(query)
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
        - messages: The list of chat messages with a new Assistant response appended at the end.
        - technical_drawing_ids: The list of new IDs in case a new search was performed, otherwise the previous list
        of IDs
    """

    def post(self):
        try:
            data = request.get_json()
            messages = data["messages"]
            technical_drawing_ids = data["technical_drawing_ids"]
            print("drawing ids ", technical_drawing_ids)
        except Exception as e:
            return "Error unpacking request data" + str(e)

        try:
            user_message_text = messages[-1]["content"]
            drawing_message = convert_drawings_to_message(technical_drawing_ids)
            tool_calls, content = get_tool_calls(user_message_text)
            assistant_response, updated_technical_drawing_ids, update = execute_tool_calls(
                tool_calls=tool_calls,
                technical_drawing_ids=technical_drawing_ids,
                drawings_message=drawing_message,
                search_engine=search_engine_instance,
            )
            messages.append(assistant_response)
            return {"messages": messages, "technical_drawing_ids": updated_technical_drawing_ids, "update": update}
        except Exception:
            messages.append(
                {
                    "role": "assistant",
                    "content": "Es gab einen internen Fehler. Bitte laden Sie die Seite neu oder wenden sich an einen "
                    "Administrator.",
                }
            )
            return {"messages": messages, "technical_drawing_ids": technical_drawing_ids, "update": False}


class ChatbotResponseWithDrawing(Resource):
    def post(self):
        raise NotImplementedError
        # TODO make endpoint for when user sends both a drawing and a message


api.add_resource(Retrieval, "/retrieve")
api.add_resource(ChatbotResponse, "/chatbot")
api.add_resource(ChatbotResponseWithDrawing, "/chatbotdrawing")

load_dotenv()
retrieval_method = os.getenv("RETRIEVAL_METHOD")
search_engine_instance = None
if retrieval_method == "LOCAL":
    search_engine_instance = EmbeddingSearchEngine()
elif retrieval_method == "REMOTE":
    search_engine_instance = RemoteEmbeddingSearchEngine()
else:
    raise ValueError(f"Can not infer search engine type for unknown RETRIEVAL_METHOD: {retrieval_method}")
search_engine_instance.create_index()
LOGGER.info("Search engine created", search_engine_instance)

if __name__ == "__main__":
    app.run()
