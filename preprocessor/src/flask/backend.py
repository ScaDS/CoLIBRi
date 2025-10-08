import json
import traceback
from importlib.resources import files

from flask_restful import Api, Resource, request

import src.flask.ocr.resources.json as json_resources
from flask import Flask
from src.flask.preprocess import apply_preprocessing

app = Flask(__name__)
api = Api(app)


class ImageToVector(Resource):
    def post(self):
        try:
            scale = 2048
            data = request.get_json()
            if data["file_content"]:
                return apply_preprocessing(data["file_content"], data["file_name"], scale)
            else:
                return "NO file_name in json"
        except Exception as e:
            traceback.print_exc()
            return "internal error: " + str(e)


class GetMaterials(Resource):
    def get(self):
        with open(files(json_resources).joinpath("materials.json")) as f:
            materials = json.load(f)
            return materials


api.add_resource(GetMaterials, "/get_materials")
api.add_resource(ImageToVector, "/image_to_vector")

if __name__ == "__main__":
    app.run()
