import requests
import json
import re
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from fuzzywuzzy import fuzz
import traceback

REMOTE_URL = "https://kiara.sc.uni-leipzig.de/api"
REMOTE_MODEL = "vllm-llama-4-scout-17b-16e-instruct"
REMOTE_API_KEY = "sk-0d043583220e4a78afada280fef3ed2b"

EMBEDDING_METHOD = "REMOTE" # either LOCAL or REMOTE
REMOTE_EMBED_MODEL = "vllm-multilingual-e5-large-instruct"
LOCAL_EMBED_MODEL = "BAAI/bge-m3"

with open("./resources/materials.json") as f:
    MATERIAL_CLASSES = json.load(f)


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


def extract_component_combined_remote(img_base64_encoded, ocr_text):
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
        "model": REMOTE_MODEL,
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
    headers = {"Authorization": f"Bearer {REMOTE_API_KEY}", "Content-Type": "application/json"}
    # API Request
    response = requests.post(REMOTE_URL, headers=headers, data=json.dumps(payload))
    if response.ok:
        content = response.json()['choices'][0]['message']['content']
        content = extract_final_json(content)
        content = content.strip()
    else:
        content = ""
    return content


def construct_string_from_list(items, section_name):
    items = list(set(items))
    if len(items) == 0:
        result_string = section_name + ": keine"
    else:
        result_string = section_name + ": "
        for item in items[:-1]:
            result_string += item + ", "
        result_string += items[-1]

    return result_string


def convert_materials_to_class(materials):
    def get_score_for_material_class(material, material_class):
        best_score = 0
        for comp_material in material_class:
            ratio = fuzz.partial_ratio(material, comp_material)
            if ratio > best_score:
                best_score = ratio
        return best_score

    material_classes = []

    for material in materials:
        best_class_score = 0
        best_class = None
        for material_class in MATERIAL_CLASSES:
            class_score = get_score_for_material_class(material, material_class)
            if class_score > best_class_score:
                best_class_score = class_score
                best_class = material_class
        if best_class_score > 0:
            material_classes.append(best_class)
        else:
            material_classes.append(material)

    return material_classes


def construct_material_string(materials):
    material_classes = convert_materials_to_class(materials)

    material_strings = []
    for material_class in material_classes:
        material_strings.append(", ".join(material_class))

    return construct_string_from_list(material_strings, "Material")


def convert_tolerance_chars_to_name(tolerance: str):
    tolerance = tolerance.lower()
    char1 = tolerance[0]
    char2 = tolerance[1]
    replacements_char1 = [
        ("f", "fine"),
        ("m", "medium"),
        ("c", "coarse"),
        ("v", "very coarse"),
    ]
    replacements_char2 = [("h", "tight"), ("k", "normal"), ("l", "loose")]

    for replacement in replacements_char1:
        if char1 == replacement[0]:
            char1 = replacement[1]
            break

    for replacement in replacements_char2:
        if char2 == replacement[0]:
            char2 = replacement[1]
            break

    return " and ".join([char1, char2])


def construct_tolerances_string(tolerances):
    converted_tolerances = []
    for tolerance in tolerances:
        converted_tolerances.append(convert_tolerance_chars_to_name(tolerance))
    return construct_string_from_list(converted_tolerances, "Toleranzen nach ISO-2768")


def construct_surfaces_string(surfaces):
    return construct_string_from_list(
        surfaces,
        "Oberflächenrauheit",
    )


def convert_gdt_symbol_to_name(gdt):
    conversions = {
        "-": "Straightness",
        "▱": "Flatness",
        "◯": "Circularity",
        # "": "Cilindricity",
        "⌓": "Profile of a Surface",
        "◠": "Profile of a Line",
        "ￌ": "Perpendicularity",
        "∠": "Angularity",
        "//": "Parallelism",
        "⌖": "Position",
        "⌾": "Concentricity",
        "=": "Symmetry",
        "↗": "Circular Runout",
        "⌰": "Total Runout",
    }
    for key, value in conversions.items():
        gdt = gdt.replace(key, value)
    return gdt


def construct_gdts_string(gdts):
    converted_gdts = []
    for gdt in gdts:
        converted_gdts.append(convert_gdt_symbol_to_name(gdt))
    return construct_string_from_list(
        converted_gdts,
        "GD&T",
    )


def construct_threads_string(threads):
    return construct_string_from_list(threads, "Gewinde")


def construct_dimension_string(outer_dims):
    if outer_dims == []:
        dimension_string = "Keine Aussendimensionen"
    else:
        dims = [str(dim[0]) for dim in outer_dims]
        dimension_string = "Die Aussendimensionen des Teils sind " + "x".join(dims) + " Millimeter. "
    return dimension_string


def drawing_to_text_using_features(preprocessing_result, extracted_name):
    part_name_string = "Name: " + extracted_name

    drawing_data = preprocessing_result["drawing_data"]

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

    combined_drawing_string = "\n".join(
        [
            part_name_string,
            material_string,
            tolerances_string,
            surfaces_string,
            gdts_string,
            threads_string,
            dimension_string,
        ]
    )
    return combined_drawing_string


def embed_using_remote(query: str):
    payload = {
        "model": REMOTE_EMBED_MODEL,
        "input": query,
    }
    url = REMOTE_URL + "/embeddings"
    headers = {"Authorization": f"Bearer {REMOTE_API_KEY}", "Content-Type": "application/json"}
    # API Request
    response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=600)
    if response.ok:
        embedding = response.json()["data"][0]["embedding"]
    else:
        print(str(traceback.format_exc()))
        embedding = []
    return embedding


def get_llm_examples(preprocessing_result):
    name = extract_component_combined_remote(preprocessing_result["original_drawing"], preprocessing_result["ocr_text"])

    llm_text = drawing_to_text_using_features(preprocessing_result, name)

    if EMBEDDING_METHOD == "REMOTE":
        llm_vector = embed_using_remote(llm_text)
    elif EMBEDDING_METHOD == "LOCAL":
        embed_model = HuggingFaceEmbedding(model_name=LOCAL_EMBED_MODEL)
        llm_vector = embed_model.get_text_embedding(llm_text)
    else:
        raise Exception(f"Unknown method: {EMBEDDING_METHOD}. Available methods are REMOTE, LOCAL.")

    return llm_text, llm_vector