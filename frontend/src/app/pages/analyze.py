import logging
import math
from datetime import datetime

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import MATCH, Input, Output, State, callback, callback_context, dcc, exceptions, html, register_page
from dash_chat import ChatComponent
from requests.exceptions import JSONDecodeError, RequestException, Timeout

from app.cache import cache
from app.search_engine import SearchEngine
from app.technical_drawing import (
    TechnicalDrawing,
    convert_database_response_to_technical_drawing,
    convert_preprocessor_response_to_technical_drawing,
)
from app.utils import (
    convert_bytestring_to_cv2,
    get_drawing_data_for_drawing_ids,
    send_request_to_database,
    send_request_to_llm_backend,
    send_request_to_preprocessor,
)

LOGGER = logging.getLogger(__name__)

register_page(__name__, path="/")

CLIP_SEARCH_ENGINE = None
COLIBRI_SEARCH_ENGINE = None
SHAPE_SCALE_FACTOR = 6  # this represents how much more the shape information is weighted in the search engine


def get_inspect_modal_content(technical_drawing: TechnicalDrawing, input_drawing: TechnicalDrawing):
    result = []
    if input_drawing is not None:
        result.append(
            dbc.Col(
                dcc.Graph(
                    figure=px.imshow(
                        img=convert_bytestring_to_cv2(input_drawing.get_drawing_image()), binary_string=True
                    )
                    .update_layout(
                        showlegend=False,
                        # margin=dict(l=0, r=0, t=0, b=0),
                        plot_bgcolor="rgba(0,0,0,0)",  # Make the background fully transparent
                        paper_bgcolor="#8cadbf",
                        dragmode="pan",
                    )
                    .update_xaxes(
                        showticklabels=False,
                    )
                    .update_yaxes(
                        showticklabels=False,
                    )
                    .update_traces(
                        hoverinfo="skip",  # disable hover events & tooltip
                        hovertemplate=None,  # ensure no hovertemplate is applied
                    ),
                    config={"displayModeBar": False, "scrollZoom": True},
                    className="inspectModalImage",
                ),
                className="inspectModalLeft",
            ),
        )
    result.append(
        dbc.Col(
            dcc.Graph(
                figure=px.imshow(
                    img=convert_bytestring_to_cv2(technical_drawing.get_drawing_image()), binary_string=True
                )
                .update_layout(
                    showlegend=False,
                    # margin=dict(l=0, r=0, t=0, b=0),
                    plot_bgcolor="rgba(0,0,0,0)",  # Make the background fully transparent
                    paper_bgcolor="#8cadbf",
                    dragmode="pan",
                )
                .update_xaxes(
                    showticklabels=False,
                )
                .update_yaxes(
                    showticklabels=False,
                )
                .update_traces(
                    hoverinfo="skip",  # disable hover events & tooltip
                    hovertemplate=None,  # ensure no hovertemplate is applied
                ),
                config={"displayModeBar": False, "scrollZoom": True},
                className="inspectModalImage",
            ),
            className="inspectModalLeft",
        ),
    )
    return dbc.Row(result)


def get_weight_figure(weights):
    colors = [
        "f94144",
        "f3722c",
        "f8961e",
        "f9c74f",
        "90be6d",
        "43aa8b",
        "577590",
    ]
    return (
        px.pie(
            pd.DataFrame(
                {
                    "weight": weights,
                    "feature": [
                        "Material",
                        "Tolerances",
                        "Surfaces",
                        "GD&T",
                        "Norms",
                        "Dimensions",
                        "Shape",
                    ],
                }
            ),
            color="feature",
            values="weight",
            names="feature",
        )
        .update_layout(
            showlegend=False,
            margin=dict(l=0, r=0, t=0, b=0),
            plot_bgcolor="rgba(0,0,0,0)",  # Make the background fully transparent
            paper_bgcolor="#8cadbf",
        )
        .update_traces(
            textinfo="label",
            # textfont_size=20,
            marker=dict(colors=colors),
        )
    )


layout = dcc.Loading(
    children=html.Div(
        [
            # The message history between user and chatbot is stored in this dcc.Store object
            # It is unique per user/session, because it is stored in the browser
            # Also, it is automatically reset when the page reloads
            dcc.Store(
                id="full_message_list",
                data=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant for a search engine on technical drawings. ",
                    }
                ],
            ),
            dcc.Store(
                id="update_results_source",
                data={
                    "source": "",
                },
            ),
            dcc.Store(
                id="store_colibri_dataset",
                data=[],
            ),
            dcc.Store(
                id="store_clip_dataset",
                data=[],
            ),
            dcc.Store(
                id="store_ids",
                data=[],
            ),
            dcc.Store(
                id="store_response_data",
                data=[],
            ),
            dcc.Store(
                id="store_technical_drawings",
                data=[],
            ),
            dcc.Store(
                id="store_embedding_type",
                data={"embedding_type": "colibri"},
            ),
            html.Div(id="searchEngineStatus"),
            html.Div(
                [
                    html.Button(
                        children=[
                            html.I(className="bi-1-square", id="embeddingIcon"),
                        ],
                        id="embeddingButton",
                        className="auxButtonInactive",
                    ),
                    dcc.Upload(
                        id="uploadImage",
                        children=[html.H3("Drag and Drop or Select Drawing", id="uploadText")],
                        multiple=False,
                    ),
                    html.Button(html.I(className="bi-filetype-pdf"), id="inspectButton", className="auxButtonInactive"),
                    html.Button(html.I(className="bi-search"), id="searchButton", className="auxButtonInactive"),
                    html.Button(html.H3("RESET"), id="resetButton"),
                ],
                id="headerWrapper",
            ),
            ChatComponent(
                id="chat-component",
                messages=[],
            ),
            html.Hr(className="thickHR"),
            html.Div(id="outputDataUpload"),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Uploaded File"), className="modalHeader"),
                    dbc.ModalBody(
                        id="inputModalBody",
                        className="modalBody",
                    ),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Close",
                            id="inputModalCloseButton",
                            className="ms-auto",
                            n_clicks=0,
                        )
                    ),
                ],
                id="inputModal",
                is_open=False,
                fullscreen=True,
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Feature Weights"), className="modalHeader"),
                    dbc.ModalBody(
                        children=[
                            dbc.Row(
                                children=[
                                    dbc.Col(
                                        children=[
                                            html.H3("Material"),
                                            html.Div(
                                                dcc.Slider(
                                                    min=0,
                                                    max=1,
                                                    marks=None,
                                                    value=0.5,
                                                    className="featureWeightSlider",
                                                    id="matWeightSlider",
                                                ),
                                                className="weightSliderWrapper",
                                                id="matSliderWrapper",
                                            ),
                                            html.H3("Tolerances"),
                                            html.Div(
                                                dcc.Slider(
                                                    min=0,
                                                    max=1,
                                                    marks=None,
                                                    value=0.5,
                                                    className="featureWeightSlider",
                                                    id="tolWeightSlider",
                                                ),
                                                className="weightSliderWrapper",
                                                id="tolSliderWrapper",
                                            ),
                                            html.H3("Surfaces"),
                                            html.Div(
                                                dcc.Slider(
                                                    min=0,
                                                    max=1,
                                                    marks=None,
                                                    value=0.5,
                                                    className="featureWeightSlider",
                                                    id="surfaceWeightSlider",
                                                ),
                                                className="weightSliderWrapper",
                                                id="surfaceSliderWrapper",
                                            ),
                                            html.H3("GD&T"),
                                            html.Div(
                                                dcc.Slider(
                                                    min=0,
                                                    max=1,
                                                    marks=None,
                                                    value=0.5,
                                                    className="featureWeightSlider",
                                                    id="gdtWeightSlider",
                                                ),
                                                className="weightSliderWrapper",
                                                id="gdtSliderWrapper",
                                            ),
                                            html.H3("Norms"),
                                            html.Div(
                                                dcc.Slider(
                                                    min=0,
                                                    max=1,
                                                    marks=None,
                                                    value=0.5,
                                                    className="featureWeightSlider",
                                                    id="normWeightSlider",
                                                ),
                                                className="weightSliderWrapper",
                                                id="normSliderWrapper",
                                            ),
                                            html.H3("Dimensions"),
                                            html.Div(
                                                dcc.Slider(
                                                    min=0,
                                                    max=1,
                                                    marks=None,
                                                    value=0.5,
                                                    className="featureWeightSlider",
                                                    id="dimWeightSlider",
                                                ),
                                                className="weightSliderWrapper",
                                                id="dimSliderWrapper",
                                            ),
                                            html.H3("Shape"),
                                            html.Div(
                                                dcc.Slider(
                                                    min=0,
                                                    max=1,
                                                    marks=None,
                                                    value=0.5,
                                                    className="featureWeightSlider",
                                                    id="formWeightSlider",
                                                ),
                                                className="weightSliderWrapper",
                                                id="formSliderWrapper",
                                            ),
                                        ],
                                        width=6,
                                        id="featureWeightSliderColumn",
                                    ),
                                    dbc.Col(
                                        children=[
                                            dcc.Graph(
                                                id="weightPlot",
                                                figure=get_weight_figure([1.0] * 7),
                                                config={"displayModeBar": False},
                                            ),
                                        ],
                                        width=6,
                                        id="featurePlotColumn",
                                    ),
                                ]
                            ),
                        ],
                        id="weightModalBody",
                        className="modalBody",
                    ),
                    dbc.ModalFooter(
                        html.Button(
                            html.Strong("Apply"),
                            id="weightModalCloseButton",
                            className="applyWeightButton",
                            n_clicks=0,
                        ),
                        className="modalFooter",
                    ),
                ],
                id="weightModal",
                is_open=False,
                fullscreen=False,
                size="xl",
            ),
        ],
    ),
    type="circle",
    parent_className="loadingWrapper",
    fullscreen=True,  # applies the blur to the whole screen
)


def clean_messages_for_chat_component(messages):
    """
    Converts a full list of messages into a list accepted by dash_chat,
    which only contains assistant and user messages (no system or tool calls messages).
    """
    return list(filter(lambda m: m["role"] in ("assistant", "user"), messages))


def handle_chat_error(request_type, error, full_message_list, technical_drawings):
    """
    Handle exceptions raised by requests in chat interactions, e.g., requests to LLM backend, or database.
    Build an according tuple for Dash callback containing the error message in the chat messages.
    """
    LOGGER.error(f"Error for {request_type} request: %s", error if isinstance(error, str) else repr(error))
    if isinstance(error, JSONDecodeError):
        error_message = f"Error: Response from {request_type} has invalid JSON format."
    elif isinstance(error, Timeout):
        error_message = f"Error: The connection to the {request_type} timed out."
    elif isinstance(error, RequestException):
        error_message = f"Error: HTTP request to {request_type} failed with {str(error)}"
    else:
        error_message = f"Error: Unexpected error with {request_type}: {str(error)}."

    full_message_list.append({"role": "assistant", "content": error_message})
    return (
        clean_messages_for_chat_component(full_message_list),
        html.Div(),  # leave results empty for errors
        full_message_list,
        {"source": "chat-component"},
        technical_drawings,
    )


@callback(
    Output("store_embedding_type", "data"),
    Output("embeddingIcon", "className"),
    State("store_embedding_type", "data"),
    Input("embeddingButton", "n_clicks"),
    prevent_initial_call=True,
)
def embedding_switch(store_data, n_clicks):
    embedding_type = store_data["embedding_type"]
    if embedding_type == "colibri":
        new_embed = "clip"
        new_class = "bi-2-square"
    elif embedding_type == "clip":
        new_embed = "colibri"
        new_class = "bi-1-square"
    else:
        LOGGER.warning(f"Unknown embedding type: {embedding_type}")
        new_embed = "colibri"
        new_class = "bi-1-square"
    LOGGER.info(f"New embedding type: {new_embed}")
    return {"embedding_type": new_embed}, new_class


@callback(
    Output("chat-component", "messages"),
    Output(
        "outputDataUpload", "children", allow_duplicate=True
    ),  # allow_duplicate needed because this callback and update_output both change the same outputDataUpload
    Output("full_message_list", "data"),
    Output("update_results_source", "data"),
    Output("store_technical_drawings", "data", allow_duplicate=True),
    Input("chat-component", "new_message"),
    State("full_message_list", "data"),
    State("store_technical_drawings", "data"),
    prevent_initial_call=True,  # Don't call this callback when the page is first initialized
)
def handle_chat(new_message, full_message_list, technical_drawings):
    """
    Handles the logic for processing a new user message.
    :param new_message: the new user message
    :param full_message_list: The previous list of all messages, including system prompts etc.
    :param technical_drawings: Result technical drawings
    :return:
        * **full_message_list**: messages for the chat component
        * ***uploadText**: text for upload button
        * **uploadImage**: contents for upload image
        * **uploadImage**: filename for upload image
        * **outputDataUpload**: container for result images
        * **full_message_list**: all chat messages for Dash store
        * **update_results_source**: source of the last search, e.g. chat-component
        * **store_technical_drawings**: current result drawings for Dash store
    :rtype: tuple
    """
    LOGGER.info("Handling chat message...")
    if new_message["role"] != "user":
        return clean_messages_for_chat_component(full_message_list)
    full_message_list.append(new_message)
    content = {"messages": full_message_list, "technical_drawing_ids": technical_drawings}
    try:
        response = send_request_to_llm_backend(resource="/chatbot", method="post", payload=content)
        LOGGER.info("LLM timings: %s", repr(response["timings"]))
    except Exception as e:
        return handle_chat_error(
            request_type="LLM backend",
            error=e,
            full_message_list=full_message_list,
            technical_drawings=technical_drawings,
        )

    response_messages = response["messages"]
    update_drawings = response["update"]
    full_message_list = response_messages
    cleaned_messages = clean_messages_for_chat_component(response_messages)
    # if llm determined that search was carried out, get drawings from database
    if update_drawings:
        try:
            # Update technical_drawings and input_drawing globally
            new_drawing_ids = response["technical_drawing_ids"]
            LOGGER.info("Updating drawings: %s", repr(new_drawing_ids))
            technical_drawings = []
            for drawing_id in new_drawing_ids:
                drawing = send_request_to_database(resource=f"/drawing/get/{drawing_id}", method="get")
                converted_drawing_obj = convert_database_response_to_technical_drawing(drawing)
                cache.set(drawing_id, converted_drawing_obj)
                technical_drawings.append(drawing_id)

        except Exception as e:
            return handle_chat_error(
                request_type="database",
                error=e,
                full_message_list=full_message_list,
                technical_drawings=technical_drawings,
            )

    input_drawing_obj = cache.get("input_drawing")
    table = draw_result(technical_drawings, input_drawing_obj)
    LOGGER.info("Finish handling chat message")
    return (
        cleaned_messages,
        html.Div(
            [
                table,
            ]
        ),
        full_message_list,
        {"source": "chat-component"},
        technical_drawings,
    )


@callback(
    Output("weightPlot", "figure"),
    Input("matWeightSlider", "value"),
    Input("tolWeightSlider", "value"),
    Input("surfaceWeightSlider", "value"),
    Input("gdtWeightSlider", "value"),
    Input("normWeightSlider", "value"),
    Input("dimWeightSlider", "value"),
    Input("formWeightSlider", "value"),
)
def update_weight_plot(mat_weight, tol_weight, surface_weight, gdt_weight, norm_weight, dim_weight, form_weight):
    weights = [mat_weight, tol_weight, surface_weight, gdt_weight, norm_weight, dim_weight, form_weight]
    return get_weight_figure(weights)


@callback(
    Output("searchEngineStatus", "children", allow_duplicate=True),
    Input("weightModalCloseButton", "n_clicks"),
    State("matWeightSlider", "value"),
    State("tolWeightSlider", "value"),
    State("surfaceWeightSlider", "value"),
    State("gdtWeightSlider", "value"),
    State("normWeightSlider", "value"),
    State("dimWeightSlider", "value"),
    State("formWeightSlider", "value"),
    State("store_colibri_dataset", "data"),
    State("store_ids", "data"),
    prevent_initial_call=True,
)
def update_search_engine(
    n_clicks, mat_weight, tol_weight, surface_weight, gdt_weight, norm_weight, dim_weight, form_weight, dataset, ids
):
    global COLIBRI_SEARCH_ENGINE

    weights = [
        mat_weight,
        tol_weight,
        surface_weight,
        gdt_weight,
        norm_weight,
        dim_weight,
        SHAPE_SCALE_FACTOR * form_weight,
    ]
    scaled_weights = []
    weights_sum = sum(weights)
    # make sure there is no division by 0
    if weights_sum == 0.0:
        scaled_weights = [0] * len(weights)
    else:
        for weight in weights:
            scaled_weights.append(weight / weights_sum)
    LOGGER.info("Set new weights: %s", repr(scaled_weights))

    COLIBRI_SEARCH_ENGINE = SearchEngine(dataset, ids, "colibri_distance", scaled_weights)

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@callback(
    Output("searchEngineStatus", "children"),
    Output("store_colibri_dataset", "data"),
    Output("store_clip_dataset", "data"),
    Output("store_ids", "data"),
    Input("dummy", "children"),
)
def init_search_engine(dummy):
    """
     Initializes the search engine in a global variable. For this a request is made to the database to get all
     search data vectors. Also, inits the dataset.
    :param dummy: status of the dummy div. This will only change upon loading the site
    :return: "loaded" when init is done
    """
    global COLIBRI_SEARCH_ENGINE
    global CLIP_SEARCH_ENGINE
    LOGGER.info("Setting up search engine...")
    try:
        # get data from database
        start = datetime.now()
        response = send_request_to_database(resource="/searchdata/get-search-vectors", method="get", payload=None)
        time_spent = datetime.now() - start
        LOGGER.info("Database request successful, request time: %s", time_spent.total_seconds())
    except Exception as e:
        LOGGER.error("Error for database request: %s", e if isinstance(e, str) else repr(e))
        return "error", [], [], []

    # reshape data
    colibri_dataset = []
    clip_dataset = []
    ids = []
    for entry in response:
        ids.append(entry["drawing_id"])
        colibri_dataset.append(entry["search_vector"])
        clip_dataset.append(entry["clip_vector"])
    # init the search engine with retrieved data
    try:
        start = datetime.now()
        COLIBRI_SEARCH_ENGINE = SearchEngine(
            dataset=colibri_dataset,
            ids=ids,
            metric="colibri_distance",
            weights=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, SHAPE_SCALE_FACTOR],
        )
        time_spent = datetime.now() - start
        LOGGER.info("Colibri Search engine initialized. Initialization time: %s", time_spent.total_seconds())
    except Exception as e:
        LOGGER.error("Error during Colibri search engine initialization: %s", e if isinstance(e, str) else repr(e))
        return "error", [], [], []
    try:
        start = datetime.now()
        CLIP_SEARCH_ENGINE = SearchEngine(dataset=clip_dataset, ids=ids, metric="euclidean", weights=None)
        time_spent = datetime.now() - start
        LOGGER.info("Clip Search engine initialized. Initialization time: %s", time_spent.total_seconds())
    except Exception as e:
        LOGGER.error("Error during Clip search engine initialization: %s", e if isinstance(e, str) else repr(e))
        return "error", [], [], []

    return "loaded", colibri_dataset, clip_dataset, ids


def get_query_tile(technical_drawing: TechnicalDrawing, n_cols, id):
    display_data = technical_drawing.get_display_data()
    return dbc.Col(
        children=[
            html.Div(
                [
                    html.H3("Query", className="tilePartNumber"),
                    dbc.Row(
                        children=[
                            dbc.Col(
                                dcc.Graph(
                                    figure=px.imshow(
                                        img=convert_bytestring_to_cv2(technical_drawing.get_drawing_image()),
                                        binary_string=True,
                                    )
                                    .update_layout(
                                        showlegend=False,
                                        margin=dict(l=0, r=0, t=0, b=0),
                                        plot_bgcolor="rgba(0,0,0,0)",  # Make the background fully transparent
                                        paper_bgcolor="#8cadbf",
                                        dragmode="pan",
                                    )
                                    .update_xaxes(
                                        showticklabels=False,
                                    )
                                    .update_yaxes(
                                        showticklabels=False,
                                    )
                                    .update_traces(
                                        hoverinfo="none",  # removes hover, preserves clickData for callback
                                        hovertemplate=None,
                                    ),
                                    config={"displayModeBar": False, "scrollZoom": True},
                                    id={
                                        "type": "drawing",
                                        "index": id,
                                    },
                                    className="tileDrawingImage",
                                ),
                                width=9,
                            ),
                            dbc.Col(
                                children=[
                                    html.Div(
                                        display_data["display_material"],
                                        className="tileInfoText",
                                        id={"type": "material_display", "index": id},
                                    ),
                                    html.Div(
                                        display_data["smallest_tolerance"],
                                        className="tileInfoText",
                                        id={"type": "tolerance_display", "index": id},
                                    ),
                                    html.Div(
                                        display_data["outer_dimensions"],
                                        className="tileInfoText",
                                        id={"type": "dim_display", "index": id},
                                    ),
                                    html.Div(
                                        display_data["smallest_surface"],
                                        className="tileInfoText",
                                        id={"type": "surface_display", "index": id},
                                    ),
                                    html.Div(
                                        display_data["smallest_gdt"],
                                        className="tileInfoText",
                                        id={"type": "gdt_display", "index": id},
                                    ),
                                ],
                                className="tileInfoWrapper",
                                width=3,
                            ),
                        ],
                        className="g-0 tileRow",
                    ),
                ],
                className="tileQueryContent",
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle(
                            f"Part Nb. {int(float(display_data['part_number']))}"
                            if str(display_data.get("part_number", "")).strip()
                            else "No Part Nb yet."
                        ),
                        className="modalHeader",
                    ),
                    dbc.ModalBody(
                        get_inspect_modal_content(technical_drawing, None),
                        className="modalBody",
                    ),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Back",
                            id={
                                "type": "modalCloseButton",
                                "index": id,
                            },
                            className="ms-auto",
                            n_clicks=0,
                        )
                    ),
                ],
                id={
                    "type": "modal",
                    "index": id,
                },
                is_open=False,
                fullscreen=True,
            ),
            # tooltips. get applied to target
            dbc.Tooltip("Material", target={"type": "material_display", "index": id}, placement="top"),
            dbc.Tooltip(
                "Tolerances according to ISO 2768", target={"type": "tolerance_display", "index": id}, placement="top"
            ),
            dbc.Tooltip("Dimensions", target={"type": "dim_display", "index": id}, placement="top"),
            dbc.Tooltip("Finest Surface Finish", target={"type": "surface_display", "index": id}, placement="top"),
            dbc.Tooltip("Smallest GD&T", target={"type": "gdt_display", "index": id}, placement="top"),
        ],
        className="resultTile",
        # dbc segments the space into 12 columns, width defines how many are used
        width=int(12 / n_cols),
    )


def get_result_tile(technical_drawing, n_cols, id, query_drawing):
    technical_drawing: TechnicalDrawing = cache.get(technical_drawing)
    display_data = technical_drawing.get_display_data()
    return dbc.Col(
        children=[
            html.Div(
                [
                    html.H3(f"Part Nb. {display_data['part_number']}", className="tilePartNumber"),
                    dbc.Row(
                        children=[
                            dbc.Col(
                                dcc.Graph(
                                    figure=px.imshow(
                                        img=convert_bytestring_to_cv2(technical_drawing.get_drawing_image()),
                                        binary_string=True,
                                        binary_compression_level=0,  #  compression of the binary string 0 None; 9 max
                                    )
                                    .update_layout(
                                        showlegend=False,
                                        margin=dict(l=0, r=0, t=0, b=0),
                                        plot_bgcolor="rgba(0,0,0,0)",  # Make the background fully transparent
                                        paper_bgcolor="#8cadbf",
                                        dragmode="pan",
                                    )
                                    .update_xaxes(
                                        showticklabels=False,
                                    )
                                    .update_yaxes(
                                        showticklabels=False,
                                    )
                                    .update_traces(
                                        hoverinfo="none",  # removes hover, preserves clickData for callback
                                        hovertemplate=None,
                                    ),
                                    config={"displayModeBar": False, "scrollZoom": True},
                                    id={
                                        "type": "drawing",
                                        "index": id,
                                    },
                                    className="tileDrawingImage",
                                ),
                                width=9,
                            ),
                            dbc.Col(
                                children=[
                                    html.Div(
                                        display_data["display_material"],
                                        className="tileInfoText",
                                        id={"type": "material_display", "index": id},
                                    ),
                                    html.Div(
                                        display_data["smallest_tolerance"],
                                        className="tileInfoText",
                                        id={"type": "tolerance_display", "index": id},
                                    ),
                                    html.Div(
                                        display_data["outer_dimensions"],
                                        className="tileInfoText",
                                        id={"type": "dim_display", "index": id},
                                    ),
                                    html.Div(
                                        display_data["smallest_surface"],
                                        className="tileInfoText",
                                        id={"type": "surface_display", "index": id},
                                    ),
                                    html.Div(
                                        display_data["smallest_gdt"],
                                        className="tileInfoText",
                                        id={"type": "gdt_display", "index": id},
                                    ),
                                ],
                                className="tileInfoWrapper",
                                width=3,
                            ),
                        ],
                        className="g-0 tileRow",
                    ),
                    dbc.Row(
                        children=[
                            dbc.Col(
                                children=display_data["info_text"],
                                width=9,
                                className="tileRuntimeText",
                                id={"type": "info_text", "index": id},
                            ),
                            dbc.Col(
                                children=[
                                    dbc.Button(
                                        children=[
                                            html.I(
                                                className="bi-hand-thumbs-up-fill upThumb",
                                                style={"transform": "translate(-60%, -50%)", "z-index": "100"},
                                            ),
                                            html.I(
                                                className="bi-hand-thumbs-up outlineThumbUp",
                                                style={"transform": "translate(-60%, -50%)", "z-index": "101"},
                                            ),
                                            html.I(
                                                className="bi-hand-thumbs-up-fill upThumb",
                                                style={
                                                    "transform": "translate(-50%, -50%) translate(20%, -15%)",
                                                    "z-index": "98",
                                                },
                                            ),
                                            html.I(
                                                className="bi-hand-thumbs-up outlineThumbUp",
                                                style={
                                                    "transform": "translate(-50%, -50%) translate(20%, -15%)",
                                                    "z-index": "99",
                                                },
                                            ),
                                        ],
                                        id={
                                            "type": "goodFeedback",
                                            "index": id,
                                        },
                                        className="thumbButton",
                                    ),
                                    dbc.Button(
                                        children=[
                                            html.I(className="bi-hand-thumbs-up-fill upThumb"),
                                            html.I(className="bi-hand-thumbs-up outlineThumbUpNeutral"),
                                        ],
                                        id={
                                            "type": "okayFeedback",
                                            "index": id,
                                        },
                                        className="thumbButton",
                                    ),
                                    dbc.Button(
                                        children=[
                                            html.I(className="bi-hand-thumbs-down-fill downThumb"),
                                            html.I(className="bi-hand-thumbs-down outlineThumbDown"),
                                        ],
                                        id={
                                            "type": "badFeedback",
                                            "index": id,
                                        },
                                        className="thumbButton",
                                    ),
                                ],
                                width=3,
                                className="tileFeedbackWrapper",
                            ),
                            dbc.Modal(
                                [
                                    dbc.ModalHeader(
                                        dbc.ModalTitle(display_data["part_number"]), className="modalHeader"
                                    ),
                                    dbc.ModalBody(
                                        children=[
                                            dcc.Textarea(
                                                placeholder="Feedback...",
                                                id={
                                                    "type": "feedbackModalTextArea",
                                                    "index": id,
                                                },
                                                className="feedbackModalTextArea",
                                            ),
                                            html.Button(
                                                "Senden",
                                                id={
                                                    "type": "feedbackModalSend",
                                                    "index": id,
                                                },
                                                className="feedbackModalSend",
                                            ),
                                        ],
                                        className="modalBody",
                                    ),
                                ],
                                id={
                                    "type": "feedbackModal",
                                    "index": id,
                                },
                                is_open=False,
                                size="lg",
                                fullscreen=False,
                            ),
                        ],
                        className="g-0 tileRow tileRowBottom",
                    ),
                ],
                className="tileContent",
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(display_data["part_number"]), className="modalHeader"),
                    dbc.ModalBody(
                        get_inspect_modal_content(technical_drawing, query_drawing),
                        className="modalBody",
                    ),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Back",
                            id={
                                "type": "modalCloseButton",
                                "index": id,
                            },
                            className="ms-auto",
                            n_clicks=0,
                        )
                    ),
                ],
                id={
                    "type": "modal",
                    "index": id,
                },
                is_open=False,
                fullscreen=True,
            ),
            # tooltips. get applied to target
            dbc.Tooltip("Material", target={"type": "material_display", "index": id}, placement="top"),
            dbc.Tooltip(
                "Tolerances according to ISO 2768", target={"type": "tolerance_display", "index": id}, placement="top"
            ),
            dbc.Tooltip("Dimensions", target={"type": "dim_display", "index": id}, placement="top"),
            dbc.Tooltip("Finest Surface Finish", target={"type": "surface_display", "index": id}, placement="top"),
            dbc.Tooltip("Smallest GD&T", target={"type": "gdt_display", "index": id}, placement="top"),
        ],
        className="resultTile",
        # dbc segments the space into 12 columns, width defines how many are used
        width=int(12 / n_cols),
    )


def draw_result(technical_drawings, query_drawing):
    """
    Updates the results to display the technical drawings.
    Args:
        technical_drawings: list of drawing_ids to load from the cache
        query_drawing: TechnicalDrawing instance of query

    Returns: html.Div containing the visualisation of the technical drawings

    """
    # calculate number of cols/ rows
    n = len(technical_drawings)
    LOGGER.info("technical_drawings: %s", repr(technical_drawings))
    if query_drawing is not None:
        n += 1  # adding the query drawing to it
    n_cols = 3
    n_rows = math.ceil(n / n_cols)

    rows = []
    for i in range(n_rows):  # iterate over rows
        tiles = []
        for j in range(i * n_cols, min((i + 1) * n_cols, n)):  # iterate over tiles in the rows
            if query_drawing is None:
                tiles.append(get_result_tile(technical_drawings[j], n_cols, j, query_drawing))
            else:
                if j == 0:
                    tiles.append(get_query_tile(query_drawing, n_cols, -1))
                else:
                    tiles.append(get_result_tile(technical_drawings[j - 1], n_cols, j - 1, query_drawing))
        rows.append(dbc.Row(children=tiles, className="resultRow"))
    return html.Div(rows)


@callback(
    Output({"type": "modal", "index": MATCH}, "is_open"),
    Input({"type": "drawing", "index": MATCH}, "clickData"),
    Input({"type": "modalCloseButton", "index": MATCH}, "n_clicks"),
    State({"type": "modal", "index": MATCH}, "is_open"),
    prevent_initial_call=True,
)
def toggle_modal(clickData, n2, is_open):
    n1 = len(clickData["points"][0])
    if n1 or n2:
        return not is_open
    return is_open


@callback(
    Output("weightModal", "is_open"),
    Input("searchButton", "n_clicks"),
    Input("weightModalCloseButton", "n_clicks"),
    State("weightModal", "is_open"),
    prevent_initial_call=True,
)
def toggle_weight_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@callback(
    Output("inputModal", "is_open"),
    Input("inspectButton", "n_clicks"),
    Input("inputModalCloseButton", "n_clicks"),
    State("inputModal", "is_open"),
    prevent_initial_call=True,
)
def toggle_input_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@callback(
    Output("outputDataUpload", "children", allow_duplicate=True),
    Output("uploadImage", "contents"),
    Output("uploadImage", "filename"),
    Output("update_results_source", "data", allow_duplicate=True),
    Output("store_technical_drawings", "data", allow_duplicate=True),
    Input("resetButton", "n_clicks"),
    prevent_initial_call=True,
)
def remove_output(n_clicks):
    # reset the results from the query
    LOGGER.info("Clearing outputs...")
    return html.Div(), "0", "0", {"source": "resetButton"}, []


@callback(
    Output("outputDataUpload", "children"),
    Output("uploadText", "children"),
    Output("inspectButton", "className"),
    Output("searchButton", "className"),
    Output("inputModalBody", "children"),
    Output("store_response_data", "data"),
    Output("store_technical_drawings", "data", allow_duplicate=True),
    Input("uploadImage", "contents"),
    Input("searchEngineStatus", "children"),
    Input("store_embedding_type", "data"),
    State("uploadImage", "filename"),
    State("update_results_source", "data"),
    State("store_response_data", "data"),
    prevent_initial_call=True,
)
def update_output(content, searchengine_status, store_embedding_data, filename, source, response_data):
    """

    :param content: content
    :param searchengine_status: search engine status
    :param filename: filename
    :param source: dash source
    :param response_data: response data
    :param input_drawing: input drawing
    :return: html.Div containing the thumbnails and a table for the search results of the given drawing
    """
    LOGGER.info("Updating results...")
    # check that file is not emtpy and search engine has been initialized
    if content is not None and content != "0" and CLIP_SEARCH_ENGINE is not None and COLIBRI_SEARCH_ENGINE is not None:
        # get the type of embedding (colibri or clip)
        embedding_type = store_embedding_data["embedding_type"]
        # we need to save response_data globally (dcc.store), so that when search engine changes due to new weights
        # preprocessor does not have to be called again
        content_type, content_string = content.split(",")  # split into header + content
        file_data = {
            "file_name": filename,
            "file_content": content_string,
            "file_type": content_type,
            "embedding_type": embedding_type,
        }

        # send file to preprocessor to convert to search vector
        try:
            # only send request to the preprocessor if new image is uploaded, else use old image
            if (
                    callback_context.triggered_id == "uploadImage"
                    or callback_context.triggered_id == "store_embedding_type"
            ):
                start = datetime.now()
                response_data = send_request_to_preprocessor(resource="/image_to_vector", method="post", payload=file_data)
                time_spent = datetime.now() - start
                LOGGER.info(
                    "Preprocessing successful, runtime: %s %s",
                    time_spent.total_seconds(),
                    repr(response_data["timings"]),
                )
                input_drawing = convert_preprocessor_response_to_technical_drawing(response_data, embedding_type)
                cache.set("input_drawing", input_drawing)
        except Exception as e:
            LOGGER.error("Error during preprocessor request: %s", e if isinstance(e, str) else repr(e))
            if isinstance(e, JSONDecodeError):
                error_message = "Error: Response from preprocessor has invalid JSON format."
            elif isinstance(e, Timeout):
                error_message = "Error: The connection to the preprocessor timed out."
            elif isinstance(e, RequestException):
                error_message = f"Error: HTTP request to preprocessor failed with {str(e)}"
            else:
                error_message = "Error: Unexpected error with preprocessor."
            return (
                error_message,
                "Drag and Drop or Select Drawing",
                "auxButtonInactive",
                "auxButtonInactive",
                html.Div(),
                None,
                [],
            )

        # extract both vectors
        try:
            LOGGER.info("Querying search engine...")
            start = datetime.now()
            if embedding_type == "colibri":
                ocr_vector = response_data["ocr_vector"]
                shape_vector = response_data["shape_vector"]
                # combine them
                search_vector = ocr_vector + shape_vector
                # query the search tree for the nearest vectors
                query_result, dist = COLIBRI_SEARCH_ENGINE.query([search_vector], 5)
                time_spent = datetime.now() - start
            elif embedding_type == "clip":
                search_vector = response_data["clip_vector"]
                # query the search tree for the nearest vectors
                query_result, dist = CLIP_SEARCH_ENGINE.query([search_vector], 5)
                time_spent = datetime.now() - start
            else:
                LOGGER.info("Invalid embedding type encoutered in update_output: %s", repr(embedding_type))
                return (
                    "Please try again! An unexpected error occurred during querying.",
                    "Drag and Drop or Select Drawing",
                    "auxButtonInactive",
                    "auxButtonInactive",
                    html.Div(),
                    None,
                    None,
                    [],
                )
            LOGGER.info("Search engine query runtime: %s", time_spent.total_seconds())
            LOGGER.info("Search engine query result: %s %s", repr(query_result), repr(dist))
        except Exception as e:
            LOGGER.error("Error during search engine query: %s", e if isinstance(e, str) else repr(e))
            return (
                "Please try again! An unexpected error occurred during querying.\n" + str(e),
                "Drag and Drop or Select Drawing",
                "auxButtonInactive",
                "auxButtonInactive",
                html.Div(),
                None,
                None,
                [],
            )
        # query results
        db_responses = get_drawing_data_for_drawing_ids(query_result)
        # update the technical drawings var globally, so it can be used elsewhere
        # global technical_drawings
        technical_drawings_objs = [
            convert_database_response_to_technical_drawing(db_response) for db_response in db_responses
        ]
        input_drawing = cache.get("input_drawing")

        technical_drawings = []
        for tech_draw_obj in technical_drawings_objs:
            drawing_id = tech_draw_obj.get_drawing_id()
            technical_drawings.append(drawing_id)
            cache.set(drawing_id, tech_draw_obj)

        # generate the page contents with the results of the search
        table = draw_result(technical_drawings, input_drawing)

        return (
            html.Div(
                [
                    table,
                ]
            ),
            str(filename),
            "auxButtonActive",
            "auxButtonActive",
            get_inspect_modal_content(input_drawing, None),
            response_data,
            technical_drawings,
        )
    if source is None:
        raise exceptions.PreventUpdate
    else:
        if source["source"] == "chat-component":
            raise exceptions.PreventUpdate
        else:
            if searchengine_status == "loaded" or content == "0":  # initial call when loading the page
                return (
                    html.Div(),
                    "Drag and Drop or Select Drawing",
                    "auxButtonInactive",
                    "auxButtonInactive",
                    html.Div(),
                    None,
                    [],
                )
            elif CLIP_SEARCH_ENGINE is None or COLIBRI_SEARCH_ENGINE is None:
                return (
                    "An Error occurred during search engine initialisation. Please reload the page.",
                    "Drag and Drop or Select Drawing",
                    "auxButtonInactive",
                    "auxButtonInactive",
                    html.Div(),
                    None,
                    [],
                )
            else:
                return (
                    "The uploaded file seems to be empty. Please try again.",
                    "Drag and Drop or Select Drawing",
                    "auxButtonInactive",
                    "auxButtonInactive",
                    html.Div(),
                    None,
                    [],
                )
