import math
from datetime import datetime

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import MATCH, Input, Output, State, callback, callback_context, dcc, exceptions, html, register_page
from dash_chat import ChatComponent

from src.app.search_engine import SearchEngine
from src.app.technical_drawing import (
    TechnicalDrawing,
    convert_database_response_to_technical_drawing,
    convert_dict_to_technical_drawing,
    convert_preprocessor_response_to_technical_drawing,
    convert_technical_drawing_to_dict,
)
from src.app.utils import (
    convert_bytestring_to_cv2,
    get_drawing_data_for_drawing_ids,
    send_request_to_database,
    send_request_to_llm_backend,
    send_request_to_preprocessor,
)

# save time during development by caching preprocessing response
# this will load a response file, so make sure this exists already
LOCAL_DEVELOP = False

if LOCAL_DEVELOP:
    import json
    from importlib.resources import files

    import your_resource_dir as resource_dir  # change this as well

register_page(__name__, path="/")

search_engine = None
SHAPE_SCALE_FACTOR = 6  # this represents how much more the shape information is weighted in the search engine


def get_inspect_modal_content(technical_drawing: TechnicalDrawing):
    return dbc.Row(
        [
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
        ]
    )


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
                id="store_dataset",
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
                id="store_input_drawing",
                data=None,
            ),
            dcc.Store(
                id="store_technical_drawings",
                data=[],
            ),
            html.Div(id="searchEngineStatus"),
            html.Div(
                [
                    dcc.Upload(
                        id="uploadImage",
                        children=[html.H3("Drag and Drop or Choose Drawing", id="uploadText")],
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
    cleaned_messages = []
    for message in messages:
        if message["role"] == "assistant" or message["role"] == "user":
            cleaned_messages.append(message)
    return cleaned_messages


@callback(
    Output("chat-component", "messages"),
    Output("uploadText", "children", allow_duplicate=True),
    Output("uploadImage", "contents", allow_duplicate=True),
    Output("uploadImage", "filename", allow_duplicate=True),
    Output(
        "outputDataUpload", "children", allow_duplicate=True
    ),  # allow_duplicate needed because this callback and update_output both change the same outputDataUpload
    Output("full_message_list", "data"),
    Output("update_results_source", "data"),
    Output("store_input_drawing", "data", allow_duplicate=True),
    Output("store_technical_drawings", "data", allow_duplicate=True),
    Input("chat-component", "new_message"),
    State("full_message_list", "data"),
    State("store_input_drawing", "data"),
    State("store_technical_drawings", "data"),
    prevent_initial_call=True,  # Don't call this callback when the page is first initialized
)
def handle_chat(new_message, full_message_list, input_drawing, technical_drawings):
    """
    Handles the logic for processing a new user message.

    Args:
        - new_message: the new user message
        - full_message_list: The previous list of all messages, including system prompts etc.

    Returns:
        - cleaned_messsages: the updated message list for the chat-component, including the assistant response
        - outputDataUpload: html Div containing the table for displaying the search results
        - full_message_list: the updated full message list including the new assistant response and system prompts etc.
    """
    print("handling chat message")
    if new_message["role"] != "user":
        return clean_messages_for_chat_component(full_message_list)
    full_message_list.append(new_message)
    curr_drawing_ids = [drawing_dict["drawing_id"] for drawing_dict in technical_drawings]
    content = {"messages": full_message_list, "technical_drawing_ids": curr_drawing_ids}
    response = send_request_to_llm_backend("/chatbot", content=content, type="post")
    response_messages = response["messages"]
    update_drawings = response["update"]
    full_message_list = response_messages
    cleaned_messages = clean_messages_for_chat_component(response_messages)
    if update_drawings:  # if llm determined that search was carried out -> new drawings through RAG
        # Update technical_drawings and input_drawing globally
        new_drawing_ids = response["technical_drawing_ids"]
        print("updating drawings:", new_drawing_ids)
        technical_drawings = []
        technical_drawing_objs = []
        input_drawing = None
        for drawing_id in new_drawing_ids:
            drawing = send_request_to_database(f"/drawing/get/{drawing_id}", content=None, type="get")
            converted_drawing_obj = convert_database_response_to_technical_drawing(drawing)
            technical_drawing_objs.append(converted_drawing_obj)
            technical_drawings.append(convert_technical_drawing_to_dict(converted_drawing_obj))

    input_drawing_obj = convert_dict_to_technical_drawing(input_drawing)
    table = draw_result(
        [convert_dict_to_technical_drawing(drawing_dict) for drawing_dict in technical_drawings], input_drawing_obj
    )
    return (
        cleaned_messages,
        "Drag and Drop or Choose Drawing",
        "0",
        "0",
        html.Div(
            [
                table,
            ]
        ),
        full_message_list,
        {"source": "chat-component"},
        input_drawing,
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
    State("store_dataset", "data"),
    State("store_ids", "data"),
    prevent_initial_call=True,
)
def update_search_engine(
    n_clicks, mat_weight, tol_weight, surface_weight, gdt_weight, norm_weight, dim_weight, form_weight, dataset, ids
):
    global search_engine

    weights = [
        mat_weight,
        tol_weight,
        surface_weight,
        gdt_weight,
        dim_weight,
        norm_weight,
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
    print("New Weights: ", scaled_weights, flush=True)

    search_engine = SearchEngine(dataset, ids, "colibri_distance", weights)

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@callback(
    Output("searchEngineStatus", "children"),
    Output("store_dataset", "data"),
    Output("store_ids", "data"),
    Input("dummy", "children"),
)
def init_search_engine(dummy):
    """
     Initializes the search engine in a global variable. For this a request is made to the database to get all
     search data vectors. Also inits the dataset
    Args:
        dummy: status of the dummy div. This will only change upon loading the site

    Returns: "loaded" when init is done

    """
    global search_engine
    # get data from database
    print("Setting up search engine...", flush=True)
    try:
        if LOCAL_DEVELOP:
            with open(files(resource_dir).joinpath("database_response.json")) as f:
                response_data_all = json.load(f)
        else:
            start = datetime.now()
            response_data_all = send_request_to_database(resource="/searchdata/get-all", content=None, type="get")
            time_spent = datetime.now() - start
            print("Time spent: ", time_spent.total_seconds(), flush=True)

    except Exception as e:
        print("Error during database request: ", e, flush=True)
        return "error"
    print("Database connection successful.", flush=True)

    # reshape data
    dataset = []
    ids = []
    for response in response_data_all:
        ids.append(response["drawing_id"])
        dataset.append(response["search_vector"])

    # init the search engine using the data
    metric = "colibri_distance"
    try:
        start = datetime.now()
        search_engine = SearchEngine(dataset, ids, metric, [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, SHAPE_SCALE_FACTOR])
        time_spent = datetime.now() - start
        print("Time spent: ", time_spent.total_seconds(), flush=True)
        print("Search engine successfully initialized.", flush=True)
    except Exception as e:
        print("Error during search engine initialization: ", e, flush=True)
        return "error", [], []
    return "loaded", dataset, ids


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
                    dbc.ModalHeader(dbc.ModalTitle(display_data["part_number"]), className="modalHeader"),
                    dbc.ModalBody(
                        get_inspect_modal_content(technical_drawing),
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


def get_result_tile(technical_drawing: TechnicalDrawing, n_cols, id):
    display_data = technical_drawing.get_display_data()
    return dbc.Col(
        children=[
            html.Div(
                [
                    html.H3(display_data["part_number"], className="tilePartNumber"),
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
                className="tileContent",
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(display_data["part_number"]), className="modalHeader"),
                    dbc.ModalBody(
                        get_inspect_modal_content(technical_drawing),
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
        technical_drawings: list of TechnicalDrawing instances
        query_drawing: TechnicalDrawing instance of query

    Returns: html.Div containing the visualisation of the technical drawings

    """
    # calculate number of cols/ rows
    n = len(technical_drawings)
    if query_drawing is not None:
        n += 1  # adding the query drawing to it
    n_cols = 3
    n_rows = math.ceil(n / n_cols)

    rows = []
    for i in range(n_rows):  # iterate over rows
        tiles = []
        for j in range(i * n_cols, min((i + 1) * n_cols, n)):  # iterate over tiles in the rows
            if query_drawing is None:
                tiles.append(get_result_tile(technical_drawings[j], n_cols, j))
            else:
                if j == 0:
                    tiles.append(get_query_tile(query_drawing, n_cols, -1))
                else:
                    tiles.append(get_result_tile(technical_drawings[j - 1], n_cols, j - 1))
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
    return html.Div(), "0", "0", {"source": "resetButton"}, []


@callback(
    Output("outputDataUpload", "children"),
    Output("uploadText", "children"),
    Output("inspectButton", "className"),
    Output("searchButton", "className"),
    Output("inputModalBody", "children"),
    Output("store_response_data", "data"),
    Output("store_input_drawing", "data"),
    Output("store_technical_drawings", "data", allow_duplicate=True),
    Input("uploadImage", "contents"),
    Input("searchEngineStatus", "children"),
    State("uploadImage", "filename"),
    State("update_results_source", "data"),
    State("store_response_data", "data"),
    State("store_input_drawing", "data"),
    prevent_initial_call=True,
)
def update_output(content, searchengine_status, filename, source, response_data, input_drawing):
    """

    Args:
        content: content of the file uploaded in an html form
        filename: name of the file

    Returns: a html.Div containing the thumbnails and a table for the search results of the given drawing

    """
    # check that file is not emtpy and search engine has been initialized
    if content is not None and content != "0" and search_engine is not None:
        # we need to save response_data globally (dcc.store), so that when search engine changes due to new weights
        # preprocessor does not have to be called again
        content_type, content_string = content.split(",")  # split into header + content
        file_data = {"file_name": filename, "file_content": content_string, "file_type": content_type}

        # send file to preprocessor to convert to search vector
        try:
            # only send request to the preprocessor if new image is uploaded, else use old image
            if callback_context.triggered_id == "uploadImage":
                if LOCAL_DEVELOP:
                    with open(files(resource_dir).joinpath("example_response_data.json")) as f:
                        response_data = json.load(f)
                else:
                    start = datetime.now()
                    response_data = send_request_to_preprocessor(
                        resource="/image_to_vector", content=file_data, type="post"
                    )
                    time_spent = datetime.now() - start
                    print("Time spent: ", time_spent.total_seconds(), flush=True)
                    print("Complete Timings:", flush=True)
                    print(response_data["timings"], flush=True)
                    # json.dump(response_data, open(files(resource_dir).joinpath("example_response_data.json"), "w"))
                print("Successfully got response from preprocessor", flush=True)
                input_drawing = convert_technical_drawing_to_dict(
                    convert_preprocessor_response_to_technical_drawing(response_data)
                )
        except Exception as e:
            print("Error during request to preprocessor: ", e, " Response data: ", response_data, flush=True)
            return (
                (
                    "Bitte versuchen Sie es erneut! Bei der Verarbeitung der Zeichnung ist ein Fehler aufgetreten.\n"
                    + str(e)
                ),
                "Drag and Drop oder Zeichnung Auswählen",
                "auxButtonInactive",
                "auxButtonInactive",
                html.Div(),
                None,
                None,
                [],
            )

        # extract both vectors
        try:
            print("Querying search engine...", flush=True)
            start = datetime.now()
            ocr_vector = response_data["ocr_vector"]
            shape_vector = response_data["shape_vector"]
            # combine them
            search_vector = ocr_vector + shape_vector

            # query the search tree for the 10 nearest vectors
            query_result, dist = search_engine.query([search_vector], 5)
            time_spent = datetime.now() - start
            print("Time spent: ", time_spent.total_seconds(), flush=True)
            print("Query successful!", "Result:", query_result, dist, flush=True)
            # query_result = json.load(open(files(resource_dir).joinpath("example_search_result.json")))
        except Exception as e:
            print("Error during search engine query: ", e, flush=True)
            return (
                "Please try again! An unexpected error occured during querying.\n" + str(e),
                "Drag and Drop or Choose Drawing",
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
        input_drawing_obj = convert_dict_to_technical_drawing(input_drawing)

        # generate the page contents with the results of the search
        table = draw_result(technical_drawings_objs, input_drawing_obj)

        technical_drawings = [
            convert_technical_drawing_to_dict(tech_draw_obj) for tech_draw_obj in technical_drawings_objs
        ]
        return (
            html.Div(
                [
                    table,
                ]
            ),
            str(filename),
            "auxButtonActive",
            "auxButtonActive",
            get_inspect_modal_content(input_drawing_obj),
            response_data,
            input_drawing,
            technical_drawings,
        )
    if source["source"] == "chat-component":
        raise exceptions.PreventUpdate
    else:
        if searchengine_status == "loaded" or content == "0":  # initial call when loading the page
            return (
                html.Div(),
                "Drag and Drop or Choose Drawing",
                "auxButtonInactive",
                "auxButtonInactive",
                html.Div(),
                None,
                None,
                [],
            )
        elif search_engine is None:
            return (
                "An Error occured during search engine initialisation. Please reload the page.",
                "Drag and Drop or Choose Drawing",
                "auxButtonInactive",
                "auxButtonInactive",
                html.Div(),
                None,
                None,
                [],
            )
        else:
            return (
                "The uploaded file seems to be empty. Please try again.",
                "Drag and Drop or Choose Drawing",
                "auxButtonInactive",
                "auxButtonInactive",
                html.Div(),
                None,
                None,
                [],
            )
