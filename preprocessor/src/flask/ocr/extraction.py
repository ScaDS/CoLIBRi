import json
import string
from importlib.resources import files

import regex
from fuzzysearch import find_near_matches
from fuzzywuzzy import fuzz

import preprocessor.src.flask.ocr.resources.json as json_resource_dir
from preprocessor.src.flask.ocr.utils import fuzzy_match, get_numbers


def find_position_of_din_code(text, code):
    """
    :param text: string to find DIN code in
    :param code: the code to find
    :return: start, end
    """
    match = find_near_matches(code, text, max_l_dist=1)
    if len(match) > 0:
        start = match[0].start
        end = match[0].end
        return start, end
    else:
        return 0, 0


def get_next_n_alpha_chars(text, n):
    """
    Return the next n alphanumeric characters in the text. If there are less than n alphanumeric characters,
    pad the result with the appropriate amount of '$'s.
    """
    chars = []
    for char in text:
        if len(chars) >= n:
            break
        if char in string.ascii_letters:
            chars.append(char)
    while len(chars) < n:
        chars.append("$")
    return chars


def search_for_all_occurrences_of_regex(re, text):
    """
    Search for all occurrences of a given regex string in text.
    :return: list of string matching the regex
    """
    results = []
    if len(re) == 0:
        return results
    # first search
    search_result = regex.search(re, text)
    # continue if new match found
    while search_result is not None:
        # append the match to the results
        start = search_result.start()
        end = search_result.end()
        results.append(text[start:end])
        # remove everything before the match from text
        text = text[end:]
        # search again
        search_result = regex.search(re, text)
    return results


def get_tolerance(text):
    """
    Extracts the tolerance value from the given text.
    :param text: str
    :return: tolerance class, gdt tolerance class
    """
    # symbols for 2768
    tol_classes = ["f", "m", "c", "v"]
    gdt_tol_classes = ["h", "k", "l"]
    # symbols for 7168
    old_tol_classes = ["f", "m", "g", "s"]
    old_gdt_tol_classes = ["a", "b", "c", "d", "r", "s", "t", "u"]
    # first check if class is spelled out
    full_names = ["fein", "mittel", "grob", "sehr grob", "fine", "middle", "coarse", "very coarse"]
    full_name_id = fuzzy_match(text, full_names)
    # if class is not spelled out => use symbols
    if full_name_id is None:
        # 7168 uses different abbreviations than 2768.
        # 7168: http://www.programmierer-forum.de/files/2014/03/din7168.pdf
        # -> f,m,g,sg + A,B,C,D,R,S,T,U
        # 2768: https://www.dau-components.co.uk/doc/General_Tolerances_-DIN_-ISO_-2768.pdf
        # -> f,m,c,v + H,K,L
        s, e = find_position_of_din_code(text, "2768")  # try to find 2768 in text
        if s + e == 0:  # no match
            s, e = find_position_of_din_code(text, "7168")  # try to find other norm code
            new_din = False  # drawing uses old standard
        else:
            new_din = True  # drawing uses new standard
        # tolerance class should be right after the code ends
        potential_class_text = text[e:]
        if s + e != 0:  # only continue if code was actually found
            if new_din:  # 2768
                # get the next 2 chars. these should be the tolerance and gdt tolerance class respectively
                [tol_class, gdt_tol_class] = get_next_n_alpha_chars(potential_class_text, 2)
                # check if they are actually a correct tolerance class
                if tol_class.lower() not in tol_classes:
                    tol_class = "-"
                if gdt_tol_class.lower() not in gdt_tol_classes:
                    gdt_tol_class = "-"
            else:  # 7168, do same as above
                [tol_class, gdt_tol_class] = get_next_n_alpha_chars(potential_class_text, 2)
                if tol_class.lower() not in old_tol_classes:
                    tol_class = "-"
                if gdt_tol_class.lower() not in old_gdt_tol_classes:
                    gdt_tol_class = "-"
        else:  # no code was found => no tolerance classes
            tol_class = "-"
            gdt_tol_class = "-"
    else:  # full name match found
        tol_class = tol_classes[full_name_id % len(tol_classes)]  # get tol_class
        gdt_tol_class = "-"
    return tol_class, gdt_tol_class


def get_material(text, materials):
    """
    Fuzzy matches the text with each material in all material classes and returns the class with the best match.
    :param text: string to find matches against
    :param materials: list of list with material names
    :return: list of material names (the matched material class), matched material name
    """
    best_ratio = 0
    material_class = None
    material_single = None
    for mat_class in materials:
        for mat in mat_class:
            ratio = fuzz.partial_ratio(mat, text)
            if ratio > best_ratio:
                best_ratio = ratio
                material_class = mat_class
                material_single = mat
    if best_ratio > 85:
        return material_class, material_single
    else:
        return None


def contains_surface(text):
    """
    Searches for surfaces in the given text.
    Surfaces are defined by starting with Ra/Rz/Rt and having a float/ integer after
    :return: A list of strings that are surface names
    """
    return search_for_all_occurrences_of_regex(r"(Ra|Rz|Rt)\s*\d+\.*\d*", text)


def contains_gdt(text):
    """
    Searches for GDTs in the given text.
    GDTs are defined by starting with a special char, followed by a number and potentially a capital letter
    :return: A list of strings that are GDTs
    """
    return search_for_all_occurrences_of_regex(r"(⌾|◯|◠|⌓|ￌ|↗|⌰|=|//|▱|∠|⌖)\s*\d+\.*\d*\s*[A-Z]*", text)


def contains_thread(text):
    """
    Searches for thread names in the given text.
    Threads could be ISO, NPT, UNF or G threads.
    :return: A list of strings that are thread names
    """
    m_search_result = search_for_all_occurrences_of_regex(r"(M)\d+\.*\d*(x)*\d*\.*\d*", text)
    g_search_result = search_for_all_occurrences_of_regex(r'(G)\d+/*\d*(")', text)
    npt_search_result = search_for_all_occurrences_of_regex(r'\d*/*\d*"*[0-9\-x"]*\s*(NPT)\d*/*\d*"*[0-9\-x"]*', text)
    unf_search_result = search_for_all_occurrences_of_regex(r'\d*/*\d*"*[0-9\-x"]*\s*(UNF)\d*/*\d*"*[0-9\-x"]*', text)
    return m_search_result + g_search_result + npt_search_result + unf_search_result


def contains_isos(text: str):
    """
    Searches for ISOs in the given text.
    ISOs are defined as starting with either 'din' or 'iso' and containing a number after
    :return: A list of strings that are GDTs
    """
    found_isos = search_for_all_occurrences_of_regex(r"(din |iso )+\d+", text.lower())
    isos = []
    for found_iso in found_isos:
        iso_nr = get_numbers(found_iso)
        if iso_nr != "2768" and iso_nr != "7168" and len(iso_nr) > 0:  # already covered by general tolerance extraction
            isos.append(iso_nr)
    return isos


def extract_data(text, materials):
    # flatten materials list
    materials_flat = []
    for material_class in materials:
        materials_flat.extend(material_class)

    # keywords to classify a cell as either containing a tolerance or a material
    keywords = {
        "general_tolerances": ["2768", "7168", "toleranz", "tolerance"],
        "material": ["material", "werkstoff", "halbzeug"] + materials_flat,
    }

    # preparing data structure to store extracted data in
    return_data = {
        "material": [],
        "material_class": [],
        "general_tolerances": [],
        "surfaces": [],
        "gdts": [],
        "threads": [],
        "other_isos": [],
    }

    # structure: call subfunctions that check for each field in return data and append their results

    # check if keywords for general tolerance or found in cell
    if fuzzy_match(text, keywords["general_tolerances"]) is not None:
        # if so, extract the tolerance
        tols = get_tolerance(text)
        if not (tols[0] is None and tols[1] is None):
            return_data["general_tolerances"].append(tols[0] + tols[1])
    if fuzzy_match(text, keywords["material"]) is not None:
        extracted_materials = get_material(text, materials)
        if extracted_materials is not None:
            material_class, material = extracted_materials
            return_data["material_class"].append(material_class)
            return_data["material"].append(material)
    return_data["surfaces"].extend(contains_surface(text))
    return_data["gdts"].extend(contains_gdt(text))
    return_data["threads"].extend(contains_thread(text))
    return_data["other_isos"].extend(contains_isos(text))
    return return_data


def extend_data_dict(old_dict: dict, new_dict: dict):
    """
    Extends old dictionary using the new dictionary.
    Both dicts must have the same keys and values should be lists.
    :return: extended dictionary
    """
    for old_key, new_values in zip(old_dict.keys(), new_dict.values(), strict=True):
        old_dict[old_key].extend(new_values)
    return old_dict


def classify_blob(blob_data):
    if len(blob_data["material"]) > 0:
        return "material"
    elif len(blob_data["general_tolerances"]) > 0:
        return "general_tolerance"
    elif len(blob_data["surfaces"]) > 0:
        return "surface"
    elif len(blob_data["gdts"]) > 0:
        return "gdt"
    elif len(blob_data["threads"]) > 0:
        return "thread"
    elif len(blob_data["other_isos"]) > 0:
        return "iso"
    else:
        return None


def is_of_right_length_for_measure(number):
    """
    Returns true if the given number does not have more than 3 digits before or after "."
    """
    text = str(number)
    return all([len(component) <= 3 for component in text.split(".")])  # split text + check if each component is <= 3


def process_measure(text):
    """
    :param text: string with measures
    :return: measure, is_diameter
    """
    if "°" in text:  # angle
        return None, False
    search_result = regex.search(r"\d+\.{0,1}\d*", text)  # find number string
    if search_result is not None:
        start = search_result.start()
        end = search_result.end()
        measure = float(text[start:end])
        radius_search_result = regex.search(r"(R){1}.{0,1}\d+\.{0,1}\d*", text)  # see if some Radii in text
        if radius_search_result is None:  # no radii
            if is_of_right_length_for_measure(text[start:end]):  # text has too many digits -> exclude part numbers etc
                if "din" in text.lower() or "iso" in text.lower():  # if it's an iso
                    return None, False
                if "SW" in text or "⌀" in text:  # diameters
                    return measure, True
                elif ":" in text:  # exclude scales
                    return None, False
                else:  # not an iso/ din, not a diameter, not a scale
                    return measure, False
            else:  # text has too many digits for a measure
                return None, False
        else:  # radius in text
            return None, False
    else:  # no number string found
        return None, False


def bb_is_horizontal(bb):
    """
    :param bb: [x,y,w,h]
    :return: True if bb is horizontal else False
    """
    [_, _, w, h] = bb
    return w >= h


def extract_outer_measures(ocr_bbs, ocr_texts, is_normal_measures):
    """
    Extracts the biggest measures in each spatial dimension
    :param ocr_bbs: list of bounding boxes [[x,y,w,h],...]
    :param ocr_texts: list of texts associated with the bounding boxes
    :param is_normal_measures: list of booleans: whether the text is a normal measure or a Radius etc
    :return: max_x, max_y
    """
    # TODO:
    #  do not get the side by orientation but by position relative to the drawing, -> maybe also exclude random tables

    # init all values with 0
    biggest_vertical = (0, None)
    biggest_horizontal = (0, None)
    biggest_diameter = (0, None)
    has_diameter = False

    # iterate over all measures
    for bb, text, is_normal_measure in zip(ocr_bbs, ocr_texts, is_normal_measures, strict=True):
        if is_normal_measure:
            # get value from measure
            measure, is_diameter = process_measure(text)
            if measure is not None:
                is_horizontal = bb_is_horizontal(bb)
                if is_diameter:
                    if measure > biggest_diameter[0]:
                        has_diameter = True
                        biggest_diameter = (measure, bb)
                elif is_horizontal and measure > biggest_horizontal[0]:
                    biggest_horizontal = (measure, bb)
                elif not is_horizontal and measure > biggest_vertical[0]:
                    biggest_vertical = (measure, bb)
    if has_diameter:
        return biggest_diameter, max(
            [biggest_vertical, biggest_horizontal], key=lambda tup: tup[0]
        )  # get the tuple with the maximum measure
    else:
        return biggest_horizontal, biggest_vertical


def extract(ocr_bbs, ocr_texts, is_texts):
    # load material classes
    # Construct the path to the JSON file
    json_file_path = files(json_resource_dir).joinpath("materials.json")
    with open(json_file_path, "rb") as mat_file:
        materials = json.load(mat_file)

    # prepare data structure that stores extracted data
    data_dict_complete_drawing = {
        "material": [],
        "material_class": [],
        "general_tolerances": [],
        "surfaces": [],
        "gdts": [],
        "threads": [],
        "other_isos": [],
    }

    is_normal_measure = []
    text_classification = []

    # extract information from each text block
    for text, is_text in zip(ocr_texts, is_texts, strict=True):
        blob_data = extract_data(text, materials)
        # add this data to the data structure that tracks for the whole image
        data_dict_complete_drawing = extend_data_dict(data_dict_complete_drawing, blob_data)

        # classify the text
        c = classify_blob(blob_data)
        text_classification.append([c, is_text])

        # text is not part of a field defined above (i.e. thread, surface etc.) and is not alphabetical
        if c is None and not is_text:
            is_normal_measure.append(True)  # text is a measure
        else:
            is_normal_measure.append(False)

    outer_measures = extract_outer_measures(ocr_bbs, ocr_texts, is_normal_measure)

    data_dict_complete_drawing["outer_dimensions"] = outer_measures

    return data_dict_complete_drawing, text_classification
