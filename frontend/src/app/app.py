import logging
import os

import dash_bootstrap_components as dbc
from dash import Dash, html, page_container
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s +0000] [%(process)d] [%(levelname)s] [%(filename)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOGGER = logging.getLogger(__name__)

# load environment file and set paths
load_dotenv()

pathname_prefix = os.getenv('PATHNAME_PREFIX', '').strip()
if not pathname_prefix or pathname_prefix == '/':
    pathname_prefix = '/'
else:
    # Remove duplicate slashes and ensure starts and ends with /
    pathname_prefix = '/' + '/'.join(filter(None, pathname_prefix.split('/'))) + '/'

LOGGER.info('Set frontend pathname prefix: %s', pathname_prefix)

pathname_params = {
    "requests_pathname_prefix": pathname_prefix,
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
    app.run(debug=True, host="0.0.0.0", port=5001)
