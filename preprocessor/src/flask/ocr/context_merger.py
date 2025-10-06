import string
import sys

import numpy as np
from PIL import Image, ImageDraw
from sklearn.cluster import DBSCAN


def get_center_of_bb(bb):
    """
    :param bb: [x,y,w,h]
    :return: center of bounding box: x,y
    """
    [x, y, w, h] = bb
    return int(x + (w // 2)), int(y + (h // 2))


def is_in_info_block(bb, info_mask_image):
    """
    :param bb: [x,y,w,h]
    :param info_mask_image: mask image
    :return: boolean
    """
    center = get_center_of_bb(bb)  # x, y
    # this is not readable at all, but ruff wants me to do it this way
    # if not in drawing: drawing_mask_image[center[1], center[0]] will be 1 => True => return False
    # else it will 0 => False => return True
    return not info_mask_image[center[1], center[0]]


def is_in_drawing(bb, drawing_mask_image):
    """
    :param bb: [x,y,w,h]
    :param drawing_mask_image: mask image
    :return: boolean
    """
    center = get_center_of_bb(bb)  # x, y
    # this is not readable at all, but ruff wants me to do it this way
    # if not in drawing: drawing_mask_image[center[1], center[0]] will be 1 => True => return False
    # else it will 0 => False => return True
    return not drawing_mask_image[center[1], center[0]]


def vis_classification(info_mask_image, drawing_mask_image, bbs, rectangles):
    """
    Visualizes the classification of the text in either part of the info block or part of the drawing
    (or completely outside of the frame)
    :param info_mask_image: mask of the info block
    :param drawing_mask_image: mask of the drawing
    :param bbs: [x, y, w, h]
    :param rectangles: list of rectangles
    :return: PIL image
    """
    img = Image.fromarray(info_mask_image).convert("RGB")
    draw = ImageDraw.Draw(img)
    for bb in bbs:
        [x, y, w, h] = bb
        if is_in_info_block(bb, info_mask_image):
            draw.rectangle((x, y, x + w, y + h), outline="red", width=3)
        elif is_in_drawing(bb, drawing_mask_image):
            draw.rectangle((x, y, x + w, y + h), outline="yellow", width=3)
        else:
            draw.rectangle((x, y, x + w, y + h), outline="green", width=3)

    for rect in rectangles:
        [x, y, w, h] = rect
        draw.rectangle((x, y, x + w, y + h), outline="blue", width=3)

    return img


def remove_dupes_from_list(data_list):
    """
    Removes duplicates from the list
    """
    return list(dict.fromkeys(data_list))


def point_in_rect(point, rect):
    """
    :param point: (x, y) coordinates of the point
    :param rect: x,y,w,h of the rectangle
    :return: boolean
    """
    return rect[0] < point[0] < rect[0] + rect[2] and rect[1] < point[1] < rect[1] + rect[3]


def get_avg_y_of_centers(list_of_centers):
    """
    Averages the y coordinates of the centers of the list
    :param list_of_centers: list of lists of centers: ex: [[(1,2), (2,2)],[(3,3), (7,7),...]]
    :return: list of means of the lists of centers: ex: [2,5,...]
    """
    list_of_means = []
    for cs in list_of_centers:
        list_of_means.append(np.mean(np.array(cs)[:, 1]))
    return list_of_means


def sort_rows_horizontally(list_of_list_of_row_ids, list_of_list_of_row_centers):
    """
    :param list_of_list_of_row_ids: list of lists of row ids
    :param list_of_list_of_row_centers: list of lists of centers
    :return: row ids, row centers sorted according to the lists of centers x position
    """
    return_row_ids = []
    return_row_centers = []
    # iterating over each row
    for row_id_list, row_center_list in zip(list_of_list_of_row_ids, list_of_list_of_row_centers, strict=True):
        if len(row_id_list) == 1:  # only one word in the row; no need to sort
            return_row_ids.append(row_id_list)
            return_row_centers.append(row_center_list)
        else:
            # sort by x position
            return_row_ids.append(
                [x for x, _ in sorted(zip(row_id_list, row_center_list, strict=True), key=lambda pair: pair[1][0])]
            )
            return_row_centers.append(
                [x for _, x in sorted(zip(row_id_list, row_center_list, strict=True), key=lambda pair: pair[1][0])]
            )
    return return_row_ids, return_row_centers


def sort_rows_vertically(list_of_list_of_row_ids, list_of_list_of_row_centers):
    """
    :param list_of_list_of_row_ids: list of lists of row ids
    :param list_of_list_of_row_centers: list of lists of centers
    :return: row ids, row centers sorted according to the average y position of the centers in each row
    """
    # get the average y position for each row
    avg_y_pos = []
    for row_center_list in list_of_list_of_row_centers:
        avg_y_pos.append(
            np.sum(np.array(row_center_list)[:, 1]) / len(row_center_list)
        )  # row_center_list is [[x, y],...]
    # sort by y position
    return_ids = [x for x, _ in sorted(zip(list_of_list_of_row_ids, avg_y_pos, strict=True), key=lambda pair: pair[1])]
    return_centers = [
        x for x, _ in sorted(zip(list_of_list_of_row_centers, avg_y_pos, strict=True), key=lambda pair: pair[1])
    ]

    return return_ids, return_centers


def get_avg_height_of_bbs(bbs_and_text):
    """
    Computes the average height of all bounding boxes and unzips the list
    :param bbs_and_text: list of tuples: [[x,y,w,h], text]
    :return: list of centers, list of texts, avg_height
    """
    heights = []
    centers = []
    texts = []
    for bb_and_text in bbs_and_text:
        [bb, text] = bb_and_text
        # get center of bb
        center = get_center_of_bb(bb)  # x, y
        centers.append(center)

        # get height of text bb
        heights.append(bb[3])  # bb == [x,y,w,h]

        # get text
        texts.append(text)

    # average the height of all bbs to get an estimate for char size
    avg_height = round(sum(heights) / len(heights))
    return centers, texts, avg_height


def get_rows(centers, avg_height):
    """
    Sort the text (represented by the centers of the bounding boxes) into rows that have similar y values
    :param centers: list of (x, y) values
    :param avg_height: average height of the bounding boxes
    :return: list of lists of centers, list of lists of ids of texts
    """

    row_centers = []  # list of lists containing the centers of the bbs in a row
    row_ids = []  # list of lists containing the id of the bbs in a row

    for bb_id, center in enumerate(centers):  # for all bbs represented by their centers
        if len(row_centers) == 0:  # if there hasn't been a row added yet
            row_centers.append([center])
            row_ids.append([bb_id])
        else:  # if there has been a row added
            means = get_avg_y_of_centers(row_centers)  # get the average y position of all bbs in that row
            found_similar_row = False
            for i, mean in enumerate(means):  # for all rows represented by their mean y position
                if abs(mean - center[1]) < avg_height // 2:  # check if current bb is close enough to that mean
                    # if so, add it to that row
                    row_centers[i].extend([center])
                    row_ids[i].extend([bb_id])
                    found_similar_row = True
            if not found_similar_row:  # if no similar row was found, add new row with this bb as only member
                row_centers.append([center])
                row_ids.append([bb_id])
    return row_centers, row_ids


def merge_text(texts, sorted_row_ids):
    """
    Merges the words in texts into a single string using the ids in sorted_row_ids
    :param texts: list of strings
    :param sorted_row_ids: list of lists of ids of the words in texts
    :return: string with merged text
    """
    final_words = []
    for row in sorted_row_ids:
        row_words = []
        for word in row:
            row_words.append(texts[word])
        row_text = " ".join(row_words)
        final_words.append(row_text)

    final_text = "\n".join(final_words)
    return final_text


def get_text_from_bb_for_info_block(bbs_and_text):
    """
    Detects lines in the text and merges the words using space and new lines chars accordingly
    :param bbs_and_text: list of tuples: [[x,y,w,h], text]
    :return: text of the region.
    """

    centers, texts, avg_height = get_avg_height_of_bbs(bbs_and_text)

    row_centers, row_ids = get_rows(centers, avg_height)

    sorted_row_ids, sorted_row_centers = sort_rows_vertically(row_ids, row_centers)
    sorted_row_ids, sorted_row_centers = sort_rows_horizontally(sorted_row_ids, sorted_row_centers)

    # merge text using row_ids
    final_text = merge_text(texts, sorted_row_ids)

    return final_text


def get_char_to_number_ratio(text):
    """
    Computes (number of alphabetical chars)/(number of alphabetical chars + number of numbers).
    If text is empty (has no numbers or alphabetical chars), returns 0
    :param text: string
    :return: float
    """

    n_chars = 0
    n_numbers = 0
    for char in text:
        if char in "0123456789":
            n_numbers += 1
        elif char in string.ascii_letters:
            n_chars += 1
    if n_chars + n_numbers == 0:
        return 0
    return n_chars / (n_numbers + n_chars)


def get_dbscan_input_from_bbs(bbs_and_text):
    """
    Using bounding boxes of text, get input for clustering.
    If a bounding box contains more than 50% numbers in the text it isn't considered
    :param bbs_and_text: list of tuples: [[x,y,w,h], text]
    :return: input for dbscan model -> list of x,y coordinates of the edges of the text bb,
    list of booleans indicating whether the bb is used in the DBSCAN input
    """
    dbscan_input = []
    in_input = []
    for bb, text in bbs_and_text:
        if get_char_to_number_ratio(text) > 0.5:
            [x, y, w, h] = bb
            x, y, w, h = round(x), round(y), round(w), round(h)

            # basically, all the edges are 'drawn' pixel by pixel
            # top edge
            for i in range(w + 1):
                dbscan_input.append([x + i, y])
            # bottom edge
            for i in range(w + 1):
                dbscan_input.append([x + i, y + h])

            # right edge
            for i in range(h + 1):
                dbscan_input.append([x + w, y + i])
            # left edge
            for i in range(h + 1):
                dbscan_input.append([x, y + i])

            in_input.append(True)
        else:
            in_input.append(False)
    return dbscan_input, in_input


def get_outer_bb(bbs):
    """
    From a set of bbs, get the outer bounding boxes
    :param bbs: list of tuples: [([x,y,w,h], text),...]
    :return: [x_outer, y_outer, w_outer, h_outer]
    """
    if len(bbs) == 0:
        return [0, 0, 0, 0]
    xmin_outer = sys.maxsize
    ymin_outer = sys.maxsize
    xmax_outer = 0
    ymax_outer = 0
    for bb, _ in bbs:
        [x, y, w, h] = bb
        x, y, w, h = round(x), round(y), round(w), round(h)
        if x < xmin_outer:
            xmin_outer = x

        if xmax_outer < x + w:
            xmax_outer = x + w

        if y < ymin_outer:
            ymin_outer = y

        if ymax_outer < y + h:
            ymax_outer = y + h

    return [xmin_outer, ymin_outer, xmax_outer - xmin_outer, ymax_outer - ymin_outer]


def get_text_clusters_in_drawing(bbs_in_drawing):
    """
    Applies DBSCAN algorithm to the bbs and finds clusters. Merges the text in the clusters accordingly.
    :param bbs_in_drawing: list of tuples: [[x,y,w,h], text]
    :return: clusters,drawing measures->both are list of tuples:[[x_outer, y_outer, w_outer, h_outer], text]
    """
    # DBSCAN
    db_input, in_input = get_dbscan_input_from_bbs(bbs_in_drawing)  # dbscan input only looks at TEXT, no measures
    if len(db_input) > 0:
        db = DBSCAN(eps=20, min_samples=20).fit(db_input)
        labels = db.labels_
        n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
    else:  # no dbscan input
        labels = []
        n_clusters_ = 0

    # get clusters
    drawing_clusters = {x: [] for x in range(n_clusters_)}  # normal text
    drawing_measures = []  # measures
    for (bb, content), in_inp in zip(bbs_in_drawing, in_input, strict=True):
        if in_inp:
            [x, y, _, _] = bb
            # get the cluster id == label by using the top left pixel of the bb
            label = labels[db_input.index([round(x), round(y)])]
            drawing_clusters[label].append([bb, content])
        else:
            drawing_measures.append([bb, content])

    # sort text in cluster
    clusters = []
    for bbs in drawing_clusters.values():
        text = get_text_from_bb_for_info_block(bbs)
        outer_bb = get_outer_bb(bbs)
        clusters.append([outer_bb, text])
    return clusters, drawing_measures


def remove_nested_rectangles(rectangles):
    """
    Attempts to remove nested rectangles: rectangles that are contained in other rectangles.
    :param rectangles: list of [x,y,w,h]
    :return: list of rectangles -> [[x,y,w,h],...]
    """

    centers = [get_center_of_bb(list(rect)) for rect in rectangles]
    keep_list = [True] * len(rectangles)

    for i, (center, rect) in enumerate(zip(centers, rectangles, strict=True)):
        for j, compare_rect in enumerate(rectangles):
            # compare all possible pairs
            # check if rect center is inside of comparison rect and it's not the same rectangle
            if point_in_rect(center, compare_rect) and rect != compare_rect:
                # get sizes of the rectangles
                size_rect = rect[2] * rect[3]
                size_compare_rect = compare_rect[2] * compare_rect[3]

                # set flag as False for the smaller one in the keep_list
                # this rectangle will be removed later
                if size_rect >= size_compare_rect:
                    keep_list[j] = False
                else:
                    keep_list[i] = False
    # only keep rectangles with True flag
    keep_rectangles = []
    for rect, keep in zip(rectangles, keep_list, strict=True):
        if keep:
            keep_rectangles.append(rect)

    return keep_rectangles


def merge_text_in_image(bbs, texts, rect_data, masks):
    """
    Merge text in image into coherent sections. This is split into two stages:
    1. Spit the image into two parts: info block and drawing
    2a. In the info block text is grouped by cells
    2b. In the drawing block text is grouped by proximity using a clustering algorithm
    Text is merged by sorting the positions of the bounding boxes. Lines are split using "\n", phrases split using " "
    :param bbs: list of bounding boxes: [x,y,w,h]
    :param texts: list of texts corresponding to the bounding boxes
    :param rect_data: [burnt_rects, inner_frame]
    :param masks: [info_mask, drawing_mask]
    :return: list of triples: [bounding box == [x,y,w,h], text, is_in_info_block]
    """
    # get rectangles in the image
    [burnt_rects, inner_frame] = rect_data
    if len(inner_frame) == 0:  # cant find inner frame
        # just return the original bounding boxes.
        # Cant consider everything to be in the infoblock, because there are no rectangles in the drawing.
        # Also cant consider everything to be in the drawing, because DBSCAN would be wayyyy too slow.
        return bbs, texts, [get_char_to_number_ratio(text) > 0.5 for text in texts]
    # get mask for drawing and info block
    [info_mask, drawing_mask] = masks

    # remove duplicates from the list of rectangles
    rects_in_image = remove_dupes_from_list(burnt_rects)
    rects_in_image.remove(inner_frame)

    # deal with text in info block
    rects_in_info_block = []  # rects: [x,y,w,h]
    for rect in rects_in_image:
        if is_in_info_block(list(rect), info_mask):
            rects_in_info_block.append(rect)

    rects_in_info_block = remove_nested_rectangles(rects_in_info_block)

    # setup datastructures for rects in info block and drawing
    # tracks which text boxes are in which cell in the info block
    bb_in_rect_tracker = {rect: [] for rect in rects_in_info_block}
    bbs_in_drawing = []  # list of bbs in the drawing
    # split bbs into info block and drawing
    for bb, content in zip(bbs, texts, strict=True):
        if is_in_info_block(bb, info_mask):
            # check all cells (rectangles) in the info block
            for rect in bb_in_rect_tracker:
                if point_in_rect(get_center_of_bb(bb), rect):  # text is in a given cell in the info block
                    bb_in_rect_tracker[rect].append((bb, content))
        # deal with text in drawing
        elif is_in_drawing(bb, drawing_mask):
            bbs_in_drawing.append([bb, content])

    ocr_bbs = []
    ocr_texts = []
    is_texts = []

    # merge the text in the cells by position
    for rect_bb, bbs in bb_in_rect_tracker.items():
        if len(bbs) > 0:
            ocr_bbs.append(list(rect_bb))
            # sort all text that is within this particular cell horizontally and vertically
            ocr_texts.append(get_text_from_bb_for_info_block(bbs))
            is_texts.append(True)

    # deal with text outside of info block
    text_clusters_in_drawing, measures_in_drawing = get_text_clusters_in_drawing(bbs_in_drawing)
    for bb, text in text_clusters_in_drawing:
        ocr_bbs.append(bb)
        ocr_texts.append(text)
        is_texts.append(True)

    # deal measures outside of info block
    for bb, text in measures_in_drawing:
        ocr_bbs.append(bb)
        ocr_texts.append(text)
        is_texts.append(False)

    return [ocr_bbs, ocr_texts, is_texts]
