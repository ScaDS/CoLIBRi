import json
import string
from importlib.resources import files

import numpy as np

import src.flask.ocr.resources.json as json_resource_dir
from src.flask.ocr.utils import fuzzy_match, get_numbers


def get_material_vector(drawing_materials):
    """
    Creates a material vector based on a list of drawing materials
    :param drawing_materials: list of material classes contained in the drawing
    :return: binary material vector -> 1 indicates presence of material class, 0 otherwise
    """
    # load material classes
    json_file_path = files(json_resource_dir).joinpath("materials.json")
    with open(json_file_path, "rb") as mat_file:
        material_classes = json.load(mat_file)

    # create vector with same amount of zeros as material classes
    material_vector = np.zeros(len(material_classes))

    for i, material_class in enumerate(material_classes):
        if material_class in drawing_materials:
            material_vector[i] = 1

    return material_vector


def get_tolerance_vector(tolerances):
    """
    Creates a tolerance vector based on a list of tolerances
    :param tolerances: list of tolerances == list of tuples with 2 chars
    :return: binary material vector -> 1 indicates presence of material class, 0 otherwise
    """
    # tolerance classes
    tol_classes = ["f", "m", "c", "v"]
    gdt_tol_classes = ["h", "k", "l"]

    # init empty vectors for each tolerance type
    tolerance_vector = np.zeros(len(tol_classes))
    gdt_tolerance_vector = np.zeros(len(gdt_tol_classes))

    # for each tolerance entry that was found
    for tolerance in tolerances:
        # check first value in tuple equals which tol_class
        for i, tol_class in enumerate(tol_classes):
            if tolerance[0] == tol_class:
                tolerance_vector[i] = 1
        # check second value in tuple equals which gdt_tol_class
        for i, gdt_class in enumerate(gdt_tol_classes):
            if tolerance[1] == gdt_class:
                gdt_tolerance_vector[i] = 1

    # combine and return
    return np.append(tolerance_vector, gdt_tolerance_vector)


def convert_surface_string_to_ngrade(surface_string: str):
    """
    Converts a surface string to a ngrade
    :param surface_string: string starting with 'Ra', 'Rt', 'Rz' or 'Ry' and containing a float after
    :return: N grade number
    """
    finish_type = surface_string[:2].lower()  # first two chars are always either 'Ra', 'Rt', 'Rz' or 'Ry'

    # n grades
    # see https://werk24.io/knowledge-base-technical-drawings/surface-finish
    n_grade_data = {
        "ra": [0.012, 0.025, 0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.3, 12.5, 25, 50, 100, 200],
        "rt": [None, 0.25, 0.5, 0.8, 1.6, 2.5, 4, 8, 16, 25, 50, 100, None, None, None],
        "rz": [0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.3, 12.5, 25, 50, 100, 200, 400, None],
        "ry": [0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.3, 12.5, 25, 50, 100, 200, 400, None],
    }
    if finish_type in n_grade_data:
        steps = n_grade_data[finish_type]
    else:
        return None  # return None if finish type can't be determined

    # get the value of the field
    try:
        value = float(surface_string[2:].strip())
    except ValueError:
        return None  # return None if conversion fails

    # find the index value so that steps[index] <= value < steps[index+1]
    index = None  # return None if no ngrade was matched
    for i, step in enumerate(steps):
        if step is None:  # grade does not exist
            continue
        elif value >= step:
            index = i
        else:  # step > value
            break

    return index


def get_surface_vector(surfaces):
    """
    Converts a list of surface strings to a binary vector that indicates presence of surface (N Grade) classes.
    """
    ngrades = []
    for surface in surfaces:
        n_grade = convert_surface_string_to_ngrade(surface)
        if n_grade is not None:
            ngrades.append(n_grade)
    if len(ngrades) == 0:
        return 7
    else:
        return min(ngrades)


def get_gdt_vector(gdts):
    """
    Converts a list of GDT strings to a vector that includes the smallest tolerance found for each GDT class.
    """
    gdt_classes = ["⌾", "◯", "◠", "⌓", "ￌ", "↗", "⌰", "=", "//", "▱", "∠", "⌖"]
    gdt_vector = np.zeros(len(gdt_classes))
    for gdt in gdts:
        for i, gdt_class in enumerate(gdt_classes):
            # see which gdt class each found gdt is
            if gdt_class in gdt:  # class found
                tolerance = float(get_numbers(gdt))
                # only save to vector if there is not value already in position or the new value is smaller
                # the goal is to only have to smallest tolerances for each gdt class, since they are the limiting factor
                if tolerance < gdt_vector[i] or not gdt_vector[i] > 0:
                    gdt_vector[i] = tolerance

    return gdt_vector


def get_outer_measure_vector(outer_measures):
    """
    Converts outer_measure tuple to a length 3 vector with the measures for each dimensions
    :param outer_measures: tuple of tuples: ((xmax, bbox), (ymax, bbox), (zmax, bbox))
    :return: np array of length 3 with [xmax, ymax, zmax]
    """
    return_vector = np.zeros(3)

    for i, outer_measure in enumerate(outer_measures):
        measure = outer_measure[0]
        return_vector[i] = measure

    return return_vector


def convert_norm_string_to_number(norm_string: str):
    """
    Removes all alphabetical characters from norm_string.
    """
    for char in string.ascii_letters:
        norm_string = norm_string.replace(char, "")

    return norm_string.strip()


def get_norm_vector(norms_in_image):
    """
    Converts norms_in_image to a binary vector signifying presence of common norms.
    """
    # load common norm names
    json_file_path = files(json_resource_dir).joinpath("norms.json")
    with open(json_file_path, "rb") as norm_file:
        common_norms = json.load(norm_file)

    # remove alphabetical chars from norms extracted from image
    norms_in_image = [convert_norm_string_to_number(norm_in_image) for norm_in_image in norms_in_image]

    # init empty vector
    return_vector = np.zeros(len(common_norms))

    # check each common norm for matches
    for i, common_norm in enumerate(common_norms):
        match_id = fuzzy_match(common_norm, norms_in_image)
        if match_id is not None:  # match found
            return_vector[i] = 1  # set flag in binary vector

    return return_vector


def vectorize_extraction(data_dict):
    """
    Converts data in data_dict to a vector representation.
    :param data_dict: dictionary as output from the extract function in extract.py
    :return: numpy array
    """
    return_vector = np.array([])

    # materials
    return_vector = np.append(return_vector, get_material_vector(data_dict["material_class"]))

    # tolerances
    return_vector = np.append(return_vector, get_tolerance_vector(data_dict["general_tolerances"]))

    # surfaces
    return_vector = np.append(return_vector, get_surface_vector(data_dict["surfaces"]))

    # gdts
    return_vector = np.append(return_vector, get_gdt_vector(data_dict["gdts"]))

    # other norms
    return_vector = np.append(return_vector, get_norm_vector(data_dict["other_isos"]))

    # outer_measures
    return_vector = np.append(return_vector, get_outer_measure_vector(data_dict["outer_dimensions"]))

    return return_vector
