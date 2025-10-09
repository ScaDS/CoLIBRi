"""
This file should only be ran once, to generate the llm_text and llm_vector fields in the database.
"""

import base64
import json
import os
import re

import pandas as pd
import requests
from dotenv import load_dotenv
from llama_index.core.schema import ImageDocument
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from tqdm import tqdm
from utils import get_remote_api_key, send_request_to_database

load_dotenv()
OLLAMA_URL = os.getenv("OLLAMA_URL")


def uri_to_image_document(uri: str) -> ImageDocument:
    """
    Convert the uri string representation of an image into a LlamaIndex ImageDocument.
    """
    header, b64_data = uri.split(",", 1)
    # Optional: extract MIME type from URI header
    match = re.match(r"data:(.*?);base64", header)
    mime_type = match.group(1) if match else "application/octet-stream"
    image_bytes = base64.b64decode(b64_data)
    return ImageDocument(image=image_bytes, image_mimetype=mime_type)


def extract_final_json(text):
    """
    Args:
        - text: A string containing a JSON like this: "{"component_name" : "Gewinderohr"}"
        Because the LLM responds in a JSON format like this (it's more reliable since it was trained for this)

    Returns:
        - the extracted value of the JSON key component_name, for example "Gewinderohr"
    """
    matches = re.findall(r"\{.*?\}", text, re.DOTALL)
    if not matches:
        return ""
    try:
        return json.loads(matches[-1]).get("component_name")
    except json.JSONDecodeError:
        return ""


def extract_component_combined(img_base64_encoded, ocr_text):
    """Use an VLM to extract the component name (e.g. "Gewinderohr", "Schalterkörper", ...) from a drawing using the
    drawing (base64 encoded) and the already extracted OCR text.

    Args:
        - img_base64_encoded: The drawing image as a base64 encoded string
        - ocr_text: A string of previously extracted text from the drawing (useful since sometimes the VLM cannot read
        text so well)
        When the VLM models get better, perhaps we don't need the ocr_text anymore
    Returns:
        - content: String that contains the name of the component
    """
    payload = {
        "model": "vllm-llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "You are an expert in reading and interpreting technical engineering drawings."
                        + "Your task is to extract the name of the part from the given image."
                        + "Return only the name in a valid JSON format like this: "
                        '\{"component_name":"<name of the component>"\}'
                        + "Do not include any additional text, explanations, or formatting."
                        + "You will also receive a list of already extracted words from the drawing that have been "
                        "extracted using OCR. You can you those in combination with the image to find the name "
                        "of the pictured component. " + f" Here are the extracted words: {ocr_text}",
                    },
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64_encoded}"}},
                ],
            }
        ],
    }
    token = get_remote_api_key()
    url = os.getenv("REMOTE_URL") + "/chat/completions"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    # API Request
    response, is_ok = requests.post(url, headers=headers, data=json.dumps(payload), timeout=600)
    if is_ok:
        content = response["choices"][0]["message"]["content"]
        content = extract_final_json(content)
        content = content.strip()
    else:
        content = ""
    return content


"""
Helper methods to convert raw data from the database into a full text string.
"""


def construct_runtime_string(runtimes):
    if runtimes == []:
        runtime_string = "Es sind keine Laufzeiten für das Teil bekannt. "
    elif len(runtimes) == 1:
        runtime_string = (
            "Das Teil hat die folgende Laufzeit: "
            + str(runtimes[0]["machine_runtime"])
            + " Minuten auf Maschine "
            + runtimes[0]["machine"]
            + ". "
        )
    else:
        runtime_string = "Das Teil hat die folgenden Laufzeiten: "
        for runtime in runtimes:
            runtime_string += str(runtime["machine_runtime"]) + " Minuten auf Maschine " + runtime["machine"] + ". "
    return runtime_string


def construct_string_from_list(items, no_items_string, single_item_string, multiple_items_string):
    items = list(set(items))
    if len(items) == 0:
        result_string = no_items_string
    elif len(items) == 1:
        result_string = single_item_string + items[0] + ". "
    else:
        result_string = multiple_items_string
        i = 0
        while i < len(items) - 2:
            result_string += items[i] + ", "
            i += 1
        result_string += items[i] + " und " + items[i + 1] + ". "
    return result_string


def construct_material_string(materials):
    return construct_string_from_list(
        materials,
        "Die Materialien sind nicht bekannt. ",
        "Das Teil besteht aus dem Material ",
        "Das Teil besteht aus den Materialien ",
    )


def construct_tolerances_string(tolerances):
    return construct_string_from_list(
        tolerances,
        "Die Toleranzen nach ISO-2768 sind nicht bekannt. ",
        "Die Toleranz nach ISO-2768 ist ",
        "Die Toleranzen nach ISO-2768 sind ",
    )


def construct_surfaces_string(surfaces):
    return construct_string_from_list(
        surfaces,
        "Die Oberflächenrauheit ist nicht bekannt. ",
        "Das Teil besitzt eine Oberflächenrauheit von ",
        "Das Teil besitzt Oberflächen mit Rauheit ",
    )


def construct_gdts_string(gdts):
    return construct_string_from_list(
        gdts,
        "Die GD&T-Toleranzen sind nicht bekannt. ",
        "Das Teil enthält die GD&T-Toleranz ",
        "Das Teil enthält die GD&T-Toleranzen ",
    )


def construct_threads_string(threads):
    return construct_string_from_list(
        threads, "Das Teil enthält keine Gewinde. ", "Das Teil enthält das Gewinde ", "Das Teil enthält die Gewinde "
    )


def construct_dimension_string(outer_dims):
    if outer_dims == []:
        dimension_string = "Die Aussendimensionen sind nicht bekannt. "
    else:
        dimension_string = (
            "Die Aussendimensionen des Teils sind "
            + str(outer_dims[0])
            + ", "
            + str(outer_dims[1])
            + " und "
            + str(outer_dims[2])
            + " Millimeter. "
        )
    return dimension_string


def construct_runtime_text_string(runtime_text):
    if runtime_text and runtime_text != "":
        runtime_text_string = (
            "Weitere Informationen über den Fertigungsprozess sind " + runtime_text.strip().replace("\n", " ") + ". "
        )
    else:
        runtime_text_string = "Es gibt keine weiteren Informationen über den Fertigungsprozess. "
    return runtime_text_string


def drawing_to_text_using_features(drawing, extracted_name):
    """
    Converts a json representation of a technical drawing (as received by /drawing/get) into a string that contains all
    neccessary information.

    Args:
        drawing: A json representation of a drawing as provided by the /drawing/get database endpoint

    Returns:
        combined_drawing_string: A full text string representation/description of the drawing.
    """
    part_number = drawing["searchdata"]["part_number"]
    part_number_string = "Das Teil mit Nummer " + part_number + " ist ein/e " + extracted_name + " . "

    runtimes = drawing["runtimes"]
    runtime_string = construct_runtime_string(runtimes)

    materials = drawing["searchdata"]["material"]
    material_string = construct_material_string(materials)

    tolerances = drawing["searchdata"]["general_tolerances"]
    tolerances_string = construct_tolerances_string(tolerances)

    surfaces = drawing["searchdata"]["surfaces"]
    surfaces_string = construct_surfaces_string(surfaces)

    gdts = drawing["searchdata"]["gdts"]
    gdts_string = construct_gdts_string(gdts)

    threads = drawing["searchdata"]["threads"]
    threads_string = construct_threads_string(threads)

    outer_dims = drawing["searchdata"]["outer_dimensions"]
    dimension_string = construct_dimension_string(outer_dims)

    runtime_text = drawing["searchdata"]["runtime_text"]
    runtime_text_string = construct_runtime_text_string(runtime_text)

    combined_drawing_string = (
        part_number_string
        + runtime_string
        + material_string
        + tolerances_string
        + surfaces_string
        + gdts_string
        + threads_string
        + dimension_string
        + runtime_text_string
    )

    return combined_drawing_string


def add_llm_embeddings_from_csv():
    """
    Iterate through all drawings, for each drawing construct a textual description of the pictured component based on
    the attributes from the database and the previously extracted component names. Save the description in
    searchdata["llm_text"] and create a vector embedding of that text, save
    that in searchdata["llm_vector"].
    """

    response, is_ok = send_request_to_database("/drawing/get-all", type="get")
    embed_model_name = os.getenv("LOCAL_EMBED_MODEL")
    embed_model = HuggingFaceEmbedding(model_name=embed_model_name)

    def embed_text(text):
        embedding = embed_model.get_text_embedding(text)
        return embedding

    if is_ok:
        # Load previously extracted component names from the csv file
        import csv

        with open("names.csv", newline="") as f:
            reader = csv.DictReader(f)
            name_dict = {row["drawing_id"]: row["name"] for row in reader}

        for item in tqdm(response, desc="Building text descriptions and embeddings"):
            drawing_id = item["drawing_id"]
            drawing_name = name_dict[str(drawing_id)]
            item_text = drawing_to_text_using_features(item, drawing_name)

            llm_vector = embed_text(item_text)
            searchdata = item["searchdata"]
            searchdata_id = searchdata["searchdata_id"]
            searchdata["llm_text"] = item_text
            searchdata["llm_vector"] = llm_vector
            # Only for id=0, we get an error when updating the searchdata, so for this case we delete it first.
            if searchdata_id == 0:
                send_request_to_database(f"/searchdata/delete/{searchdata_id}", type="delete")
            send_request_to_database("/searchdata/save", content=searchdata, type="post")
    del response


def extract_component_names_to_csv():
    """
    Iterate through all drawings, for each drawing use an LLM to extract the component name,
    and save them to a csv file.
    """
    response, is_ok = send_request_to_database("/drawing/get-all", type="get")
    if is_ok:
        results = []
        for i, item in enumerate(tqdm(response, desc="Extracting names")):
            ocr_text = item["searchdata"]["ocr_text"]
            original_drawing = item["original_drawing"]
            drawing_id = item["drawing_id"]
            extracted_description_combined = extract_component_combined(original_drawing, ocr_text)
            results.append({"drawing_id": drawing_id, "name": extracted_description_combined})
            if i % 10 == 0:
                output_df = pd.DataFrame(results)
                output_df.to_csv("names.csv", index=False)
        output_df = pd.DataFrame(results)
        output_df.to_csv("names.csv", index=False)
    del response


if __name__ == "__main__":
    if not os.path.exists("names.csv"):
        print("Generating names.csv...")
        extract_component_names_to_csv()
        print("Done.")
    print("Adding llm embeddings...")
    add_llm_embeddings_from_csv()
    print("Done.")
