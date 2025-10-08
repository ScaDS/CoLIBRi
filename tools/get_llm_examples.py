import requests
import json
import re
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

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
    token = "your_token"
    url = "your_url"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    # API Request
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.ok:
        content = response.json()['choices'][0]['message']['content']
        content = extract_final_json(content)
        content = content.strip()
    else:
        content = ""
    return content


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
        dims = [str(dim[0]) for dim in outer_dims]
        dimension_string = (
            "Die Aussendimensionen des Teils sind " + "x".join(dims) + " Millimeter. "
        )
    return dimension_string


def drawing_to_text_using_features(preprocessing_result, extracted_name, part_number):
    """
    Converts response_data into a string that contains all neccessary information for the llm.

    Args:
        preprocessing_result: A dict representation of a drawing as provided by the /drawing/get database endpoint

    Returns:
        combined_drawing_string: A full text string representation/description of the drawing.
    """

    drawing_data = preprocessing_result["drawing_data"]

    part_number_string = "Das Teil mit Nummer " + part_number + " ist ein/e " + extracted_name + " . "

    materials = drawing_data["material"]
    material_string = construct_material_string(materials)

    tolerances = drawing_data["general_tolerances"]
    tolerances_string = construct_tolerances_string(tolerances)

    surfaces = drawing_data["surfaces"]
    surfaces_string = construct_surfaces_string(surfaces)

    gdts = drawing_data["gdts"]
    gdts_string = construct_gdts_string(gdts)

    threads = drawing_data["threads"]
    threads_string = construct_threads_string(threads)

    outer_dims = drawing_data["outer_dimensions"]
    dimension_string = construct_dimension_string(outer_dims)

    combined_drawing_string = (
        part_number_string
        + material_string
        + tolerances_string
        + surfaces_string
        + gdts_string
        + threads_string
        + dimension_string
    )

    return combined_drawing_string


def get_llm_examples(preprocessing_result, part_number):
    name = extract_component_combined(preprocessing_result["original_drawing"], preprocessing_result["ocr_text"])

    llm_text = drawing_to_text_using_features(preprocessing_result, name, part_number)

    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3")
    llm_vector = embed_model.get_text_embedding(llm_text)

    # print("llm text: " + llm_text)
    # print("llm vector: " + str(len(llm_vector)))

    return llm_text, llm_vector