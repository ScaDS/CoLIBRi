import logging
import os

from langchain.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from search_engine import SearchEngine
from utils import send_request_to_database

LOGGER = logging.getLogger(__name__)


class Chatbot:
    """
    Methods and logic for chatbot functionalities, using a defined LLM backend.
    """
    def __init__(self, search_engine: SearchEngine) -> None:
        self._search_engine = search_engine
        self._llm = self._resolve_llm()
        LOGGER.info("Resolved LLM for Chatbot: %s", repr(self._llm))

    def _resolve_llm(self) -> BaseChatModel:
        llm_type = os.getenv("LLM_TYPE")
        if llm_type == "OLLAMA":
            return ChatOllama(
                model=os.getenv("OLLAMA_MODEL"),
                base_url=os.getenv("OLLAMA_URL"),
            )
        if llm_type == "REMOTE":
            return ChatOpenAI(
                model=os.getenv("REMOTE_MODEL"),
                api_key=os.getenv("REMOTE_API_KEY"),
                base_url=os.getenv("REMOTE_URL"),
            )
        raise ValueError(f"Unsupported LLM_TYPE '{llm_type}'")

    def _retrieve_text_for_drawing(self, drawing_id: str) -> str:
        """
        For a drawing id, retrieves the generated text representation of the drawing.
        Args:
            drawing_id: The id of the drawing in the database
        Returns:
            The previously extracted text representation containing information about the drawing.
        """
        response, is_ok = send_request_to_database(f"/drawing/get/{drawing_id}", type="get")
        return response["searchdata"]["llm_text"] if is_ok else ""

    def _convert_drawings_to_message(self, drawing_ids) -> HumanMessage:
        """
        Converts a list of drawing ids into a chat message containing text representation about the drawings.
        Args:
            drawing_ids : List of integers representing technical drawing ids
        Returns:
            A string containing descriptions of all the drawings.
        """
        if not drawing_ids:
            return HumanMessage("No previous search has been performed, so there are no search results yet.")
        drawings_texts = [self._retrieve_text_for_drawing(drawing_id) for drawing_id in drawing_ids]
        joined = "\n".join(f"Teil: {text}" for text in drawings_texts if text)
        return HumanMessage(f"Here are the retrieved results from the previous search:\n{joined}".strip())

    def _answer_question_about_retrival_results(self, drawings_message: HumanMessage, question: str) -> str:
        """
        Uses an LLM to answer a single question about a list of previously retrieved drawings.
        Args:
            drawings_message: Message in the OpenAI message format, containing text descriptions for retrieved drawings.
            question: A string containing a question about the drawings.
        Returns:
            The assistants answer as string.
        """
        messages = [
            SystemMessage(
                "You are a helpful assistant for a retrieval system on technical drawings of mechanical components. "
                "You will be given a list of previously retrieved drawings, represented as textual descriptions. "
                "You will also be given a related user question. "
                "Your task is to answer the user question based on the provided retrieval results. "
            ),
            drawings_message,
            HumanMessage(question),
        ]

        try:
            response = self._llm.invoke(messages)
            return response.content
        except Exception as e:
            LOGGER.error("Error while invoking the LLM backend: %s", e if isinstance(e, str) else repr(e))
            return f"Error while invoking the LLM backend: {type(e).__name__}: {e}"

    def execute_with_tool_calls(self, user_message: str, drawing_ids: list[str]) -> tuple[str, list[str], bool]:
        """
        Executes LLM call with tools for provided user message and technical drawing ids.
        Args:
            user_message: User message from the frontend chat
            drawing_ids: List of IDs from previously retrieved technical drawings
        Returns:
            assistant_response: Message in the OpenAI message format containing the response to the user message
            update: Boolean, flags whether to redraw the results in the frontend (when new drawings were found)
        """

        # Create basic tool schemas and bind them to the model. The schemas are used by the model to decide for a tool
        # without the actual need for tool calling capabilities and tool code execution on a remote LLM backend.
        class search_parts(BaseModel):
            """
            Searches for technical drawings based on a query provided by the user.
            """
            query: str = Field(
                ...,
                description="Minimal query to search for relevant technical drawings in the database. "
                            "It should only include a few keywords that precisely describe the parts to search for. "
                            "If the query mentions specific features with specific values, include this in the search."
            )
        class answer_question(BaseModel):
            """
            Answers a question about previously retrieved technical drawings. This will not perform a new retrieval.
            """
            question: str = Field(
                ...,
                description="Question about the previously retrieved technical drawings."
            )

        llm_with_tools = self._llm.bind_tools(tools=[search_parts, answer_question], tool_choice="any")

        messages = [
            SystemMessage(
                "You are a helpful assistant for a retrieval system on technical drawings of mechanical components. "
                "Your job is to decide whether the user is asking to do a new search on the database, "
                "or whether the user is asking a question about the previously retrieved results. "
                "You have access to a tool called search_parts. "
                "Use the tool search_parts to search the database for a given user query. "
                "You have access to a tool called answer_question. "
                "Use the tool answer_question to answer a users question about previously retrieved results. "
                "You can only decide for one tool call. Remember to correctly include your tool calls in the metadata. "
            ),
            HumanMessage(user_message),
        ]

        return_tuple = None
        tool_calls = None

        try:
            response = llm_with_tools.invoke(messages)
            tool_calls = response.tool_calls
        except Exception as e:
            LOGGER.error("Error while invoking the LLM backend with tools: %s", e if isinstance(e, str) else repr(e))
            return_tuple = (
                f"Error while invoking the LLM backend: {type(e).__name__}: {e}",
                drawing_ids,
                False
            )

        if not tool_calls or not all(tc["name"] in ("search_parts", "answer_question") for tc in tool_calls):
            return_tuple = (
                "Unfortunately, I can't help you with that.",
                drawing_ids,
                False
            )
        tool_call = tool_calls[0]
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        if tool_name == "search_parts":
            updated_drawing_ids = self._search_engine.retrieve_drawings(**tool_args)
            return_tuple = (
                "I found the following technical drawings.",
                updated_drawing_ids,
                True,
            )
        if tool_name == "answer_question":
            drawings_message = self._convert_drawings_to_message(drawing_ids)
            response = self._answer_question_about_retrival_results(drawings_message=drawings_message, **tool_args)
            return_tuple = (
                response,
                drawing_ids,
                False,
            )
        return return_tuple
