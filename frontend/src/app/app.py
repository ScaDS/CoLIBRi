
import dash_bootstrap_components as dbc
from dash import Dash, html, page_container
from dotenv import load_dotenv

# load environment file
load_dotenv()

pathname_params = {
    "requests_pathname_prefix": "/",
    "assets_url_path": "/assets",
}

app = Dash(
    __name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP], **pathname_params
)

server = app.server

app.layout = dbc.Container(
    [  # container that contains navigation + content
        html.Div(id="dummy"),
        html.Div(
            [  # content
                page_container
            ],
            id="pageContent",
            className="pageContentExpanded pageContent",
        ),
    ],
    style={
        "height": "90vh",
        "width": "95vw",
    },
    fluid=True,
)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)  # nosec
