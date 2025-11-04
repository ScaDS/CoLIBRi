import regex


def convert_surface_string_to_ngrade(surface_string: str):
    """
    Converts a surface string to a ngrade.
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
        return 15  # return 15 if finish type can't be determined

    # get the value of the field
    try:
        value = float(surface_string[2:].strip())
    except ValueError:
        return 15  # return 15 as default if conversion fails

    # find the index value so that steps[index] <= value < steps[index+1]
    index = None
    for i, step in enumerate(steps):
        if step is None:  # grade does not exist
            continue
        elif value >= step:
            index = i
        else:  # step > value
            break

    if index is None:  # return 15 as default value
        index = 15

    return index


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


def convert_preprocessor_response_to_technical_drawing(preprocessor_response):
    """
    Converts the preprocessor response into a TechnicalDrawing instance.
    :param preprocessor_response: response object from the preprocessor service.
    :return: TechnicalDrawing instance.
    """
    # full ocr text
    full_ocr_text = preprocessor_response["ocr_text"]

    # drawing after preprocessing
    original_drawing = preprocessor_response["original_drawing"]

    # extract the other features from drawing_data
    drawing_data = preprocessor_response["drawing_data"]

    # material
    materials = drawing_data["material"]

    # general_tolerances
    general_tolerances = []
    for general_tolerance in drawing_data["general_tolerances"]:
        general_tolerances.append(GeneralTolerance(general_tolerance[0], general_tolerance[1]))

    # surfaces
    surfaces = []
    for surface_text in drawing_data["surfaces"]:
        surfaces.append(Surface(surface_text))

    # gdts
    gdts = []
    for gdt in drawing_data["gdts"]:
        gdts.append(GDT(gdt))

    # outer dimensions
    dims = drawing_data["outer_dimensions"]
    if len(dims) == 2:
        dims.append([0.0, [0.0]])
    dimensions = Dimensioning([dims[0][0], dims[1][0], dims[2][0]])

    return TechnicalDrawing(
        materials,
        general_tolerances,
        surfaces,
        gdts,
        dimensions,
        "",  # info text is not present
        original_drawing,
        full_ocr_text,
        "",
        "",
    )


def convert_database_response_to_technical_drawing(response_data):
    """
    Converts the database response from the /drawing/get/{id} resource in to a TechnicalDrawing instance.
    :param response_data: database response from the /drawing/get/{id} resource.
    :return: TechnicalDrawing instance.
    """
    drawing_id = response_data["drawing_id"]

    # get the actual image to display later
    drawing_image = response_data["original_drawing"]

    # extract the other features from drawing_data
    drawing_data = response_data["searchdata"]

    # material
    materials = drawing_data["material"]

    # general_tolerances
    general_tolerances = []
    for general_tolerance in drawing_data["general_tolerances"]:
        general_tolerances.append(GeneralTolerance(general_tolerance[0], general_tolerance[1]))

    # surfaces
    surfaces = []
    for surface_text in drawing_data["surfaces"]:
        surfaces.append(Surface(surface_text))

    # gdts
    gdts = []
    for gdt in drawing_data["gdts"]:
        gdts.append(GDT(gdt))

    # outer dimensions
    dimensions = Dimensioning(drawing_data["outer_dimensions"])

    # info text
    info_text = drawing_data["runtime_text"]

    # ocr text
    full_ocr_text = drawing_data["ocr_text"]

    # part number
    part_number = drawing_data["part_number"]

    # create technical drawing instance
    technical_drawing = TechnicalDrawing(
        materials,
        general_tolerances,
        surfaces,
        gdts,
        dimensions,
        info_text,
        drawing_image,
        full_ocr_text,
        part_number,
        drawing_id,
    )

    return technical_drawing


class TechnicalDrawing:
    def __init__(
        self,
        materials,
        general_tolerances,
        surfaces,
        gdts,
        outer_dimensions,
        info_text,
        drawing_image,
        full_ocr_text,
        part_number,
        drawing_id,
    ):
        self.materials = materials
        self.general_tolerances = general_tolerances
        self.surfaces = surfaces
        self.gdts = gdts
        self.outer_dimensions = outer_dimensions
        self.info_text = info_text
        self.drawing_image = drawing_image
        self.full_ocr_text = full_ocr_text
        self.part_number = part_number
        self.drawing_id = drawing_id

    def get_drawing_id(self):
        return self.drawing_id

    def get_display_data(self):
        return {
            "materials": self.materials,
            "display_material": self.get_display_material(),
            "general_tolerances": [tol.get_display_data() for tol in self.general_tolerances],
            "smallest_tolerance": self.get_smallest_tolerance(),
            "surfaces": [surface.get_display_data() for surface in self.surfaces],
            "smallest_surface": self.get_smallest_surface(),
            "gdts": [gdt.get_display_data() for gdt in self.gdts],
            "smallest_gdt": self.get_smallest_gdt(),
            "outer_dimensions": self.outer_dimensions.get_display_data(),
            "info_text": self.info_text,
            "full_ocr_text": self.full_ocr_text,
            "part_number": self.part_number,
        }

    def get_display_material(self):
        if len(self.materials) > 0:
            return self.materials[0]
        else:
            return ""

    def get_smallest_surface(self):
        if len(self.surfaces) > 0:
            sorted_surfaces = sorted(self.surfaces, key=lambda surface: surface.ngrade)
            return sorted_surfaces[0].get_display_data()["text"]
        else:
            return ""

    def get_drawing_image(self):
        return self.drawing_image

    def get_smallest_tolerance(self):
        tol_classes = ["f", "m", "c", "v", "-"]
        gdt_tol_classes = ["h", "k", "l", "-"]
        smallest_tol_class = 4
        smallest_gdt_class = 3
        for tolerance in self.general_tolerances:
            try:
                tol_class_id = tol_classes.index(tolerance.dimension_class)
                gdt_class_id = gdt_tol_classes.index(tolerance.geometry_class)
                if tol_class_id < smallest_tol_class:
                    smallest_tol_class = tol_class_id
                if gdt_class_id < smallest_gdt_class:
                    smallest_gdt_class = gdt_class_id
            except ValueError:
                continue

        return (tol_classes[smallest_tol_class] if smallest_tol_class < 4 else "-") + (
            gdt_tol_classes[smallest_gdt_class] if smallest_gdt_class < 3 else "-"
        )

    def get_smallest_gdt(self):
        if len(self.gdts) > 0:
            sorted_gdts = sorted(self.gdts, key=lambda gdt: gdt.value)
            smallest_gdt = sorted_gdts[0].get_display_data()
            return smallest_gdt["characteristic"] + " " + str(smallest_gdt["value"])
        else:
            return ""


class Surface:
    def __init__(self, text, ngrade=None):
        self.text = text
        if ngrade is None:
            self.ngrade = convert_surface_string_to_ngrade(text)
        else:
            self.ngrade = ngrade

    def get_display_data(self):
        return {
            "text": self.text,
            "ngrade": self.ngrade,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


class GeneralTolerance:
    def __init__(self, dimension_class: str, geometry_class: str):
        self.dimension_class = dimension_class.lower()
        self.geometry_class = geometry_class.lower()

    def get_display_data(self):
        return {
            "dimension_class": self.dimension_class,
            "geometry_class": self.geometry_class,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


class GDT:
    def __init__(self, text, characteristic=None, value=None, reference=None):
        """
        See https://en.wikipedia.org/wiki/Geometric_dimensioning_and_tolerancing
        """
        if characteristic is None and value is None and reference is None:
            self.text = text
            for symbol in ["⌾", "◯", "◠", "⌓", "ￌ", "↗", "⌰", "=", "//", "▱", "∠", "⌖"]:
                if symbol in text:
                    self.characteristic = symbol
                    text.replace(symbol, "")

            self.value = search_for_all_occurrences_of_regex(r"\d+\.*\d*", text)[0]
            text = text.replace(self.value, "")
            self.value = float(self.value)

            self.reference = text.strip()
        else:
            self.text = text
            self.characteristic = characteristic
            self.value = value
            self.reference = reference

    def get_display_data(self):
        return {
            "text": self.text,
            "characteristic": self.characteristic,
            "value": self.value,
            "reference": self.reference,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


class Dimensioning:
    def __init__(self, dimensions):
        self.dim1 = dimensions[0]
        self.dim2 = dimensions[1]
        self.dim3 = dimensions[2]

    def get_display_data(self):
        return f"{self.dim1}x{self.dim2}x{self.dim3}"

    def to_dict(self):
        return {
            "dim1": self.dim1,
            "dim2": self.dim2,
            "dim3": self.dim3,
        }

    @classmethod
    def from_dict(cls, d):
        dims = [d["dim1"], d["dim2"], d["dim3"]]
        return cls(dimensions=dims)


def convert_technical_drawing_to_dict(technical_drawing: TechnicalDrawing):
    return {
        "materials": technical_drawing.materials,
        "general_tolerances": [tol.get_display_data() for tol in technical_drawing.general_tolerances],
        "surfaces": [surface.get_display_data() for surface in technical_drawing.surfaces],
        "gdts": [gdt.get_display_data() for gdt in technical_drawing.gdts],
        "outer_dimensions": technical_drawing.outer_dimensions.to_dict(),
        "info_text": technical_drawing.info_text,
        "drawing_image": technical_drawing.drawing_image,
        "full_ocr_text": technical_drawing.full_ocr_text,
        "part_number": technical_drawing.part_number,
        "drawing_id": technical_drawing.drawing_id,
    }


def convert_dict_to_technical_drawing(drawing_dict):
    if drawing_dict is None:
        return None

    general_tolerances = [GeneralTolerance.from_dict(gdt_dict) for gdt_dict in drawing_dict["general_tolerances"]]

    surfaces = [Surface.from_dict(surface_dict) for surface_dict in drawing_dict["surfaces"]]

    gdts = [GDT.from_dict(gdt_dict) for gdt_dict in drawing_dict["gdts"]]

    outer_dim = Dimensioning.from_dict(drawing_dict["outer_dimensions"])

    return TechnicalDrawing(
        materials=drawing_dict["materials"],
        general_tolerances=general_tolerances,
        surfaces=surfaces,
        gdts=gdts,
        outer_dimensions=outer_dim,
        info_text=drawing_dict["info_text"],
        drawing_image=drawing_dict["drawing_image"],
        full_ocr_text=drawing_dict["full_ocr_text"],
        part_number=drawing_dict["part_number"],
        drawing_id=drawing_dict["drawing_id"],
    )
