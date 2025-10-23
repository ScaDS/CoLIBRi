import os

import requests
from langchain_ollama.chat_models import ChatOllama
from langchain_openai import ChatOpenAI
from ollama import Client
from pydantic import BaseModel, Field
from utils import get_remote_api_key, send_request_to_database


def drawing_to_string(drawing_id):
    """
    Converts a drawing id into the string representation of the drawing.
    Args:
        drawing_id: The id of the drawing in the database
    Returns:
        The previously extracted text representation containing information about the drawing.
    """
    response, is_ok = send_request_to_database(f"/drawing/get/{drawing_id}", type="get")
    drawing_text = response["searchdata"]["llm_text"] if is_ok else ""
    return drawing_text


def convert_drawings_to_message(drawing_ids):
    """
    Converts a list of technical drawing ids into a chat message containing text information about the drawings.
    Args:
        drawing_ids : List of integers representing technical drawing ids
    Returns:
        A string containing descriptions of all the drawings.
    """
    if drawing_ids and drawing_ids != []:
        drawings_list = [drawing_to_string(drawing_id) for drawing_id in drawing_ids]
        message_content = "Hier sind die Ergebnisse der vorherigen Suche:\n"
        for drawing in drawings_list:
            message_content += "Teil: " + drawing + "\n"
        message = {"role": "user", "content": message_content}
    else:
        message = {
            "role": "user",
            "content": "Es wurde bisher keine vorherige Suche getätigt, weswegen es noch keine Suchergebnisse gibt.",
        }
    return message


def answer_question_about_retrieved_drawings(drawings_message, question):
    """
    Uses an LLM to answer a single question about a list of previously retrieved drawings.
    Args:
        drawings_message: Message in the OpenAI message format, containing text descriptions for 10 retrieved drawings.
        question: A string containing a question about the drawings.
    Returns:
        assistant_response: Message in the OpenAI message format containing the assistants answer.
    """
    llm_type = os.getenv("LLM_TYPE")
    messages = [
        {
            "role": "system",
            "content": "You are an assistant for a retrieval system on technical drawings of mechanical components."
                       "User questions and your answers will be in German." 
                       "You will be given a list of previously retrieved drawings, and a related user question."
                       "Your task is to answer the question based on the provided retrieval results.",
        },
        drawings_message,
        {
            "role": "user",
            "content": question
        },
    ]

    assistant_message: str

    if llm_type == "OLLAMA":
        ollama_url = os.getenv("OLLAMA_URL")
        ollama_model = os.getenv("OLLAMA_MODEL")
        client = Client(host=ollama_url)
        response = client.chat(
            model=ollama_model,
            messages=messages,
        )
        assistant_message = response["message"].content
    elif llm_type == "REMOTE":
        token = get_remote_api_key()
        model_name = os.getenv("REMOTE_MODEL")
        url = os.getenv("REMOTE_URL") + "/chat/completions"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        data = {"model": model_name, "messages": messages}
        try:
            response = requests.post(url, headers=headers, json=data, timeout=600)
            response.raise_for_status() # Exception for 4xx/5xx HTML codes
            try:
                assistant_message = response.json()["choices"][0]["message"]["content"]
            except Exception as e:
                assistant_message = f"Antwort des LLM ist kein valides JSON: {e}"
        except requests.exceptions.HTTPError as e:
            assistant_message = f"Fehler beim Aufruf des LLM: {e}"
    else:
        assistant_message = f"Fehler in der internen Konfiguration. Unbekannter Wert für LLM_TYPE: {llm_type}."

    assistant_response = {"role": "assistant", "content": assistant_message}
    return assistant_response


def answer_unrelated_question_or_message():
    """
    Respond to an unrelated question.
    Returns:
        assistant_response: A message in the OpenAI message format telling the user to try a different query.
    """
    assistant_response = {
        "role": "assistant",
        "content": "Damit kann ich leider nicht helfen. Ich kann aber gerne nach neuen Zeichnungen suchen.",
    }
    return assistant_response


def get_tool_calls(user_message_text):
    """
    Uses an LLM to understand what the user asks the system to do (either perform a new search, or answer a question).
    Creates according tool calls in the OpenAI tool call format.
    Args:
        user_message_text: The plain string text of the last message sent by the user
    Returns:
        tool_calls: The extracted tool calls in the OpenAI tool call format
        content: The answer generated by the LLM, minus the extracted tool call.
    """
    llm_type = os.getenv("LLM_TYPE")
    if llm_type == "OLLAMA":
        ollama_url = os.getenv("OLLAMA_URL")
        ollama_model = os.getenv("OLLAMA_MODEL")
        llm = ChatOllama(model=ollama_model, base_url=ollama_url)
    elif llm_type == "REMOTE":
        remote_api_key = get_remote_api_key()
        remote_model = os.getenv("REMOTE_MODEL")
        remote_url = os.getenv("REMOTE_URL")
        llm = ChatOpenAI(model=remote_model, api_key=remote_api_key, base_url=remote_url)
    else:
        raise ValueError(f"Can not load LLM for unknown LLM_TYPE: {llm_type}")

    # Create tool schemas and bind them to our model
    class search_parts_german(BaseModel):
        """
        Search for relevant technical drawings of mechanical components in the database based on a german query
        provided by the user.
        """
        query: str = Field(
            ...,
            description="Minimal german query to search for relevant parts. It should only include a few keywords that"
            " precisely describe the parts we are searching for, so if the user is looking for parts where"
            " a specific feature has a specific value, include the feature and the value.",
        )

    class answer_question_about_previous_results(BaseModel):
        """
        Answer a question about the results of the previous retrieval. This will not perform a new retrieval,
        but leaves the results unchanged and answer a question about the results of the retrieval.
        """
        question: str = Field(
            ...,
            description="The german question about the retrieval results to be answered."
        )

    tools = [search_parts_german, answer_question_about_previous_results]
    llm_with_tools = llm.bind_tools(tools, tool_choice="any")

    # Invoke LLM to get tool calls
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant for a retrieval system on technical drawings of mechanical components."
            "The user will provide queries in German." 
            "Your job is to decide whether the user is asking to do a new search on the database, in which case you "
            "should extract an optimal german query to use for the retrieval."
            "Or whether the user is asking a question about the previous retrieval results, in which case you should "
            "just pass the question to the correct tool."
            "You have access to a tool called SearchPartsGerman. You will call this tool every time the "
            "user asks to search the database."
            "You also have access to a tool called AnswerQuestionAboutPreviousResults. "
            "You will call this tool every time the user asks a question related to previous retrieval results "
            " instead of a new retrieval search. Remember to correctly include your tool calls in the metadata.",
        },
        {"role": "user", "content": user_message_text},
    ]
    # TODO here we could prepend the full message history, or append it
    #  Or maybe just use the last 5 message from the user and assistant
    ans = llm_with_tools.invoke(messages)
    return ans.tool_calls, ans.content


def execute_tool_calls(tool_calls, drawings_message, technical_drawing_ids, search_engine):
    """
    Executes the given tool calls.

    Args:
        tool_calls: List of tool calls in the OpenAI too call format, as returned by LangChain for example
        drawing_message: Message in OpenAI message format that contains descriptions of the search results from the
                         last search
        technical_drawing_ids: IDs of drawings from last search results

    Returns:
        assistant_response: Message in the OpenAI message format containing the assistant response to the user message
                            and tool calls
        updated_technical_drawing_ids: New list of IDs of technical drawings, in case a new search was conducted
        update: Boolean, flags whether to redraw the results in the frontend (when new drawings were found)
    """
    update = False
    if not tool_calls or len(tool_calls) == 0:
        assistant_response, updated_technical_drawing_ids = (
            answer_unrelated_question_or_message(),
            technical_drawing_ids,
        )
    else:
        tool_call = tool_calls[
            0
        ]  # TODO decide how to handle multiple tool calls, currently we only process the first one
        fn_name = tool_call["name"]
        fn_args = tool_call["args"]
        if fn_name == "search_parts_german":
            assistant_response, updated_technical_drawing_ids = search_engine.retrieve_drawings(**fn_args)
            update = True
        elif fn_name == "answer_question_about_previous_results":
            assistant_response = answer_question_about_retrieved_drawings(drawings_message=drawings_message, **fn_args)
            updated_technical_drawing_ids = technical_drawing_ids
        else:
            raise ValueError(f"Function {fn_name} not found.")
    return assistant_response, updated_technical_drawing_ids, update
