import base64
import io
import math
import os
import pickle  # nosec
import random
import sys

import pandas as pd
import requests

from get_llm_examples import get_llm_examples

def send_request_to_preprocessor(resource, content=None, type="post"):
    """
    Sends request preprocessor resource and returns response json. If return status code is not 200, will return
    dictionary with key "ERROR".
    :param resource: the REST resource to be called, e.g. /drawing/get/1 (include leading /)
    :param content: the payload of the request, e.g. json data for saving a drawing
    :param type: post, get, or delete
    :return: json response from endpoint
    """
    url = "localhost:6201" + resource
    return send_request_to(url, content, type)

def send_request_to_llm_backend(resource, content=None, type="post"):
    """
    Sends request conv-search backennd resource and returns response json. If return status code is not 200, will return
    dictionary with key "ERROR".
    :param resource: the REST resource to be called, e.g. /drawing/get/1 (include leading /)
    :param content: the payload of the request, e.g. json data for saving a drawing
    :param type: post, get, or delete
    :return: json response from endpoint
    """
    url = "localhost:9201" + resource
    return send_request_to(url, content, type)


def send_request_to(url, content, type="post"):
    """
    Sends request to url and returns response json. If return status code is not 200, will return dictionary with key
    "ERROR".
    :param url: url to sent content to
    :param content: content to sent to url
    :param type: post, get, or delete
    :return: json response from endpoint
    """
    try:
        if type == "get":
            response = requests.get(url, json=content, timeout=100)  # timeout of 100 seconds
        elif type == "post":
            response = requests.post(url, json=content, timeout=100)
        elif type == "delete":
            response = requests.delete(url, json=content, timeout=100)
        else:
            return {"ERROR", "invalid request type"}
    except requests.exceptions.Timeout:
        return {"ERROR": "timed out"}
    if response.status_code == 200:
        return response.json()
    else:
        return {"ERROR", str(response.content)}


def file_to_base64(file_path):
    """
    Reads a file from the given file path and converts its content to a Base64-encoded bytestring. If local files is
    True, will try to load the file from the path locally. If not, will try to fetch it from gpu server.

    :param file_path: Path to the file to be encoded.
    :return: Base64-encoded bytestring of the file content.
    """
    try:
        with open(file_path, "rb") as file:
            # Read the file in binary mode
            file_content = file.read()
            # Encode the content to Base64
        return str(base64.b64encode(file_content))[2:-1]
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def replace_commas(text: str):
    """
    Replaces commas in a string with '\,'.
    """
    return text.replace(",", "\,")


def remove_empty_text(text_array):
    """
    Removes empty text from a list of strings.
    """
    for text in text_array:
        if text.strip() == "":
            text_array.remove(text)
    return text_array


def handle_preprocessing_result(prepro_result: dict, drawing_id, part_number, path, full_text, machine, runtime, llm_text, llm_vector):
    """
    Converts preprocessor response into a Dataframe.
    :param prepro_result: Preprocessor response dictionary.
    :param drawing_id: Drawing ID.
    :param part_number: Part number.
    :param path: Path to the file.
    :param full_text: Full text from the CPT database.
    :param machine: Machine names.
    :param runtime: Runtimes.
    :return: Dataframe with preprocessor response data.
    """
    response_data = {
        "drawing_id": [drawing_id],
        "part_number": [part_number],
        "path": [path],
        "runtime_text": [full_text],
        "machines": [machine],
        "runtimes": [runtime],
        "llm_text": [llm_text],
        "llm_vector": [llm_vector],
    }
    drawing_data = prepro_result["drawing_data"]
    ocr_vector = prepro_result["ocr_vector"]

    # full ocr text
    full_ocr_text = prepro_result["ocr_text"]
    full_ocr_text = remove_empty_text([replace_commas(text) for text in full_ocr_text])
    response_data["ocr_text"] = [full_ocr_text]

    response_data["shape"] = [prepro_result["shape_vector"]]
    response_data["original_drawing"] = [prepro_result["original_drawing"]]

    # drawing data
    response_data["material"] = [drawing_data["material"]]
    response_data["general_tolerances"] = [drawing_data["general_tolerances"]]
    response_data["surfaces"] = [drawing_data["surfaces"]]
    response_data["gdts"] = [drawing_data["gdts"]]
    response_data["threads"] = [drawing_data["threads"]]
    response_data["outer_dimensions"] = [drawing_data["outer_dimensions"]]

    # search_vector
    response_data["search_vector"] = [ocr_vector + prepro_result["shape_vector"]]

    return pd.DataFrame(response_data).set_index("drawing_id")


def iterate_preprocess(drawing_ids, part_numbers, drawing_paths, data_dir):
    """
    Iterates through the given lists and calls the preprocessor every iteration.
    :param drawing_ids: List of drawing IDs.
    :param part_numbers: List of part numbers.
    :param drawing_paths: List of drawing paths.
    :param data_dir: Path to the data directory.
    :return: dataframe with preprocessor response data for all drawings.
    """
    batch_df = pd.DataFrame(
        columns=[
            "drawing_id",
            "machines",
            "runtimes",
            "original_drawing",
            "shape",
            "material",
            "general_tolerances",
            "surfaces",
            "gdts",
            "threads",
            "outer_dimensions",
            "search_vector",
            "llm_text",
            "llm_vector",
        ]
    ).set_index("drawing_id")
    for drawing_id, part_number, drawing_path in zip(drawing_ids, part_numbers, drawing_paths, strict=True):
        print(f"Processing drawing {drawing_id}...: {drawing_path}")
        # try:
        file = file_to_base64(os.path.join(data_dir, drawing_path))  # load file as bytes
        file_data = {"file_name": drawing_path, "file_content": file}
        preprocessing_result = send_request_to_preprocessor(
            resource="/image_to_vector", content=file_data, type="post"
        )
        print("preprocessing result:", preprocessing_result)

        llm_text, llm_vector = get_llm_examples(preprocessing_result, str(part_number))

        result_df = handle_preprocessing_result(
            preprocessing_result, drawing_id, part_number, drawing_path, "", "", "", llm_text,
            llm_vector
        )  # convert the dictionary from preprocessor to a dataframe

        batch_df = pd.concat([batch_df, result_df])
        # except Exception as e:
        #     print("Exception occured during preprcoess iteration:", e)
        #     continue

    return batch_df


def load_and_apply_preprocessing(data_dir, output_dir):
    """
    Loads the dataframe, and make a preprocessor request for each row (or a random subset of rows)
    :param data_dir: directory where the data dump from CPT is
    :param output_dir: directory to output the checkpoints
    :return: dataframe
    """
    # make directory for the checkpoints
    os.makedirs(output_dir, exist_ok=True)

    # get the amount of files in data_dir
    example_drawing_paths = os.listdir(data_dir)
    ids = list(range(len(example_drawing_paths)))
    # get dataframe for all drawings in the batch
    df = iterate_preprocess(
        drawing_ids=ids,
        part_numbers=ids,
        drawing_paths=example_drawing_paths,
        data_dir=data_dir,
    )
    return df


def remove_bounding_boxes(data):
    """
    Removes bounding boxes from the entries in the outer_dimensions column.
    :param data: cell with bounding boxes.
    """
    result = []
    for dimension in data:
        [value, _] = dimension
        result.append(value)
    if len(result) < 3:
        result.append(0.0)
    return result


def handle_string_lists(s: str, cast_to_float):
    """
    Removes [,],' and " from a string and then splits it at ",".
    :param s: string to split.
    :param cast_to_float: bool. Cast string to float.
    :return: list of strings.
    """
    if pd.isna(s):
        return []
    s = s.replace("[", "")
    s = s.replace("]", "")
    s = s.replace("'", "")
    s = s.replace('"', "")
    elements = s.split(",")
    result = []
    for element in elements:
        if len(element) > 0:
            if cast_to_float:
                element = float(element)
            result.append(element)
    return result


# Function to format array literals
def format_array_literal(array_str):
    array_str = str(array_str)
    if pd.isnull(array_str):
        return None
    return array_str.replace("[", "{").replace("]", "}")


# Function to format the nested arrays in the top-level array
def format_nested_arrays(array_str):
    array_str = str(array_str)
    if pd.isnull(array_str):
        return None
    return "{" + array_str[1:-1].strip().replace("{", '"{').replace("}", '}"') + "}"


def replace_sing_quote(s: str):
    return s.replace("'", "")


def convert_to_separate_dfs(monolithic_df, result_dir):
    # define the columns for the newly created dataframes from the monolithic dataframe
    searchdata = monolithic_df[
        [
            "shape",
            "material",
            "general_tolerances",
            "surfaces",
            "gdts",
            "threads",
            "outer_dimensions",
            "search_vector",
            "part_number",
            "ocr_text",
            "runtime_text",
            "llm_text",
            "llm_vector",
        ]
    ]
    drawings = monolithic_df[["original_drawing"]]
    # ---------------------------------------------------
    #                 SEARCHDATA
    # ---------------------------------------------------
    searchdata["searchdata_id"] = list(range(len(searchdata)))  # add searchdata ids
    searchdata = searchdata.set_index("searchdata_id", append=True).reset_index(level=0)  # set them as index
    # remove bounding boxes from outer dimensions
    searchdata["outer_dimensions"] = searchdata["outer_dimensions"].apply(remove_bounding_boxes)

    # Apply the formatting function to all relevant columns
    array_columns = [
        "shape",
        "material",
        "general_tolerances",
        "surfaces",
        "gdts",
        "threads",
        "outer_dimensions",
        "search_vector",
        "ocr_text",
    ]

    for column in array_columns:
        searchdata[column] = searchdata[column].apply(format_array_literal)
        searchdata[column] = searchdata[column].apply(format_nested_arrays)
        searchdata[column] = searchdata[column].apply(replace_sing_quote)

    # save as csvs in the results dir
    os.makedirs(result_dir, exist_ok=True)
    searchdata.to_csv(result_dir + "searchdata.csv", index=True)
    drawings.to_csv(result_dir + "drawings.csv", index=True)


if __name__ == "__main__":
    # Directory of the dataset with all images
    DATA_DIR = sys.argv[1] if len(sys.argv) > 1 else "../example_data/"
    # output file
    OUTPUT_DIR = str(sys.argv[2]) if len(sys.argv) > 2 else "../database/resources/example_data/"

    df = load_and_apply_preprocessing(DATA_DIR, OUTPUT_DIR)
    convert_to_separate_dfs(df, OUTPUT_DIR)
