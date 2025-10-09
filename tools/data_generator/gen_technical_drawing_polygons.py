import os
import string

import cv2

from helpers import *
import numpy as np
import pandas as pd
import random
import string
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import matplotlib.pyplot as plt
import json
from perlin_noise import PerlinNoise
import time
import sys
from gen_table_rec_data import *
import math
from scipy import ndimage


def get_1d_perlin_noise(n, octaves):
    '''
    Samples a 1D-perlin noise image n times
    :param n: times to sample
    :param octaves: list of octaves to use in the noise
    :return: list of noise values
    '''
    noises = []
    for octave in octaves:
        noise = PerlinNoise(octaves=octave)
        noises.append(noise)

    data = []
    for i in range(n):
        value = 0
        for noise in noises:
            value += noise([i / n, 0])
        data.append(value)
    return data



def sample_unit_circle_uniform(n):
    '''
    Samples half a unit circle n times uniformly
    :param n: number of samples
    :return: np array of points on the circle
    '''
    unit_vec = np.transpose(np.array([1, 0]))
    points = []
    # rotate unit vector by increasing angle
    for i in range(n + 1):
        angle = 360 * i / n
        points.append(rotate(unit_vec, angle))
    return np.array(points)


def shift_to_rectangle(circle_samples, aspect_ratio):
    '''
    Shifts points sampled on a unit semi circle to lie on either x == -1, y == 1 or x == 1
    :param circle_samples: iterable of np arrays
    :param aspect_ratio: tuple of: stretch in x direction and y direction
    :return: np array containing new coords
    '''
    new_points = []
    side_affiliation = []
    for sample in circle_samples:
        gradient = sample[1] / sample[0]
        # intersect with all 3 lines: x == -1, y == 1 or x == 1
        # y = gradient * x + 0
        # x == 1: => y == gradient
        # x == -1: => y == -gradient
        # y == 1: ==> x == 1/gradient
        # y == -1: ==> x == -1/gradient
        solutions = [
            np.array([-1, -gradient]),
            np.array([1, gradient]),
            np.array([1 / gradient, 1]),
            np.array([-1 / gradient, -1])
        ]
        side_names = "lrtb"
        # get distances to original point
        closest_point = None
        best_distance = sys.maxsize
        side = None
        for i, solution in enumerate(solutions):
            dist = np.linalg.norm(solution - sample)
            if dist < best_distance:
                closest_point = solution
                best_distance = dist
                side = side_names[i]
        # choose the closest one
        side_affiliation.append(side)
        new_points.append(closest_point * np.array(aspect_ratio))
    return np.array(new_points), side_affiliation


def offset_points_using_perlin_noise(points, base, noise_factor, octaves=[3, 6], round_resolution=0):
    '''
    Offsets a set of points by sampling a perlin noise function
    :param points: iterable of np array coords
    :param base: shift the points out by this amount by default
    :param noise_factor: multiplicative factor for the noise
    :param octaves: what octaves to use to create a perlin noise function
    :param round_resolution: if > 0: devide offset points by this number, round to nearest decimal, multiply by this number. If == 0 skip this. Essentially this snaps points to a grid and this number controls the size of the grid.
    :return: np array of coords
    '''
    # sample noise
    n = len(points)
    noise_pts = get_1d_perlin_noise(n, octaves)
    final_data = []
    for noise, unit_vector in zip(noise_pts, points):
        # shift the vector by the noise, scale the noise by noise_factor and shift by base
        unit_vector += unit_vector * (base + noise_factor * noise)
        # if snapping to grid
        if round_resolution > 0:
            # decrease by round_resolution
            unit_vector /= round_resolution
            # round
            unit_vector = np.round(unit_vector, 1)
            # increase by round_resolution
            unit_vector *= round_resolution
        final_data.append(unit_vector)
    return np.array(final_data)


def get_upright_triangle_coords(tip, width, height):
    '''
    Generates the coordinates for a triangle pointing up
    :param tip: position of the tip
    :param width: width of the triangle
    :param height: height of the triangle
    :return: [tip, left, right]: 2d coordinates
    '''
    left = np.array([tip[0] - width / 2, tip[1] - height])
    right = np.array([tip[0] + width / 2, tip[1] - height])
    return np.array([tip, left, right])


def rotate_triangle(triangle_coords, rotation):
    '''
    Rotates a triangle by rotation
    :param triangle_coords: [tip, left, right]: 2d coords
    :param rotation: degrees
    :return: [tip, left, right]: np array
    '''
    tip = triangle_coords[0]
    points = [tip]
    for coord in [triangle_coords[1], triangle_coords[2]]:
        rot_coord = coord - tip
        points.append(rotate(rot_coord, rotation) + tip)
    return np.array(points)


def get_arrow_head(coord, width, height, rotation):
    '''
    Get coordinates for an arrow head pointing at coord and for a given width, height and rotation
    :return: coordinates: 2d np array
    '''
    coords = rotate_triangle(get_upright_triangle_coords(coord, width, height), rotation)
    return coords


def get_random_arrow_sizes():
    '''
    Chooses a random width and height for an arrow
    :return: width, height
    '''
    width = random.choice([6, 8, 10, 12])
    height = random.choice([10, 12, 14, 16])
    return width, height


def gen_measurement(font_path, text_color, font_size, spacing, extra_kerning=0):
    '''
    Generates a random measurement image
    :param font_path: path to the image to use
    :param text_color: color of the text
    :param font_size: size of the base font, if ±: 2/3 of that size, if upper/lower bounds 1/2 of that size
    :param spacing: space between numbers
    :param extra_kerning: extra spacing between words
    :return: PIL image, text
    '''
    # init variables
    extra_kerning = min(extra_kerning, spacing)
    spacing += extra_kerning
    typeface = ImageFont.truetype(font_path, font_size)
    small_font_size = int(font_size * 2 / 3)
    small_typeface = ImageFont.truetype(font_path, small_font_size)
    smallest_font_size = int(font_size / 2)
    smallest_typeface = ImageFont.truetype(font_path, smallest_font_size)

    # get base text
    base_text = str(random_float())
    has_diameter = random.choice([True, False])

    # decide where to put the tolerances
    if random.random() > 0.3:  # 30% chance to add tolerances
        upper_and_lower = random.choice([True, False])
        if not upper_and_lower:
            upper, lower = random.choice([(True, True), (True, False), (False, True)])
        else:
            upper, lower = (False, False)
    else:
        upper_and_lower, upper, lower = False, False, False

    # put all of it in an image together
    # base
    base_text_img = get_image_from_text(base_text, typeface, extra_kerning, text_color, "RGB", True)
    if has_diameter:
        # first get ⌀, because some fonts dont have the char included
        dia_typeface = ImageFont.truetype(random.choice([
                                            "../resources/fonts/seguisym.ttf",
                                            "../resources/fonts/osifont.ttf",
                                            "../resources/fonts/isocpeui.ttf",
                                            ]), font_size)
        diameter = get_image_from_text("⌀", dia_typeface, extra_kerning, text_color, "RGB", True)
        dia_W, dia_H = diameter.size
        base_W, base_H = base_text_img.size
        new_W = base_W + dia_W + spacing
        new_H = max(base_H, dia_H)

        # new empty image
        new_base_img = Image.new("RGB", (new_W, new_H), (255,255,255))
        # paste them both in appropriately
        new_base_img.paste(diameter, (0,0))
        new_base_img.paste(base_text_img, (dia_W + spacing, 0))

        # update base_text_img
        base_text_img = new_base_img
    background = Image.new("RGB", (font_size * 10, font_size * 3), (255, 255, 255))
    center_y = int(background.size[1] / 2) - font_size
    background.paste(base_text_img, [0, center_y])
    base_w, base_h = base_text_img.size
    center_text = center_y + int(base_h / 2)
    text = base_text if not has_diameter else "⌀" + base_text

    if upper_and_lower:
        tol = "±" + str(random_float())
        u_l_img = get_image_from_text(tol, small_typeface, extra_kerning, text_color, "RGB", True)
        background.paste(u_l_img, [base_w + spacing, center_y + random.choice(range(font_size - small_font_size))])
        text += " " + tol
    elif upper:
        upper_tol = random.choice("+-") + str(random_float())
        upper_image = get_image_from_text(upper_tol, smallest_typeface, extra_kerning, text_color, "RGB", True)
        background.paste(upper_image, [base_w + spacing, center_text - spacing - upper_image.size[1]])
        text += " " + upper_tol
        # if not lower:
        #     text += " " + str(0)
    elif lower:
        lower_tol = random.choice("+-") + str(random_float())
        lower_image = get_image_from_text(lower_tol, smallest_typeface, extra_kerning, text_color, "RGB", True)
        background.paste(lower_image, [base_w + spacing, center_text + spacing])
        # if not upper:
        #     text += " " + str(0)
        text += " " + lower_tol

    return crop_rgb_image_to_text_content(background, crop_y=True), text

def outer_measurements(points, image: Image.Image, margin, gen, arrow_w, arrow_h, font_size, font, line_color,
                       thin_line_width=2, padding=5, extra_kerning = 0, text_color = (0,0,0)):
    '''
    Draws outer measurements into an image
    :param points: list of points of the object
    :param image: PIL image to draw in
    :param margin: spacing between the object and the annotation
    :param gen: ImagepairGenerator
    :param arrow_w: width of the arrows
    :param arrow_h: height of the arrows
    :param font_size: int
    :param font: path to the used font
    :param line_color: color to use for the lines
    :param thin_line_width: thickness to use in the lines
    :param padding: spacing between lines and text
    :param extra_kerning: extra spacing between letters in pixels
    :param text_color: color of the text
    :return: PIL image, pasted texts
    '''
    max_id = np.argmax(points, axis=0)
    [xmax, ymax] = points[max_id]

    min_id = np.argmin(points, axis=0)
    [xmin, ymin] = points[min_id]

    x_line_height = ymax[1] + margin
    y_line_width = xmin[0] - margin
    texts = []
    mask = np.zeros((image.size[1], image.size[0]))
    image, text_data, mask = draw_measurement(image, xmax, xmin, "b", [y_line_width, 0, 0, x_line_height], arrow_w, arrow_h,
                                        line_color, thin_line_width, mask, font_size, font, padding, extra_kerning, text_color)  #
    texts.extend(text_data)
    image, text_data, mask = draw_measurement(image, ymax, ymin, "l", [y_line_width, 0, 0, x_line_height], arrow_w, arrow_h,
                                        line_color, thin_line_width, mask, font_size, font, padding, extra_kerning, text_color)
    texts.extend(text_data)

    return image, texts


def split_points_by_sides(points, sides):
    '''
    Separates points into lists by the class given in sides
    :param points: list of points
    :param sides: list of classes
    :return: list of list of points
    '''
    side_ids = []
    split_points = []
    for point, side_id in zip(points, sides):
        if side_id in side_ids:
            split_points[side_ids.index(side_id)].append(list(point))
        else:
            split_points.append([list(point)])
            side_ids.append(side_id)
    return split_points, side_ids


def get_measurement_points(n_points):
    '''
    Which point ids to draw a measurement on
    :param n_points: number of points on this side
    :return: the ids between which measurement should be drawn
    '''
    point_ids = []
    for i in range(1, n_points - 1):
        if random.choices([True, False], weights=[1,2])[0]:
            point_ids.append(i)
    point_ids.append(n_points - 1)

    last_point_id = 0
    measurement_ids = []
    for point_id in point_ids:
        measurement_ids.append([last_point_id, point_id])
        last_point_id = point_id
    return measurement_ids


def choose_where_to_measure(points, side_ids):
    '''
    Randomly generates the points between which a measurement should be drawn
    :param points: list of 2d-points
    :param side_ids: list of their respective side affiliations
    :return: list of measurements between the points: [[p1,p2,side],...]. p1 always > p2 for the relevant dimension
    '''
    measurements = []
    for side_points, side_name in zip(points, side_ids):
        n_points = len(side_points)
        measures = get_measurement_points(n_points)
        for measure in measures:
            p1 = side_points[measure[0]]
            p2 = side_points[measure[1]]
            if "l" in side_name or "r" in side_name:
                if p1[1] > p2[1]:
                    measurements.append([p1, p2, side_name])
                else:
                    measurements.append([p2, p1, side_name])
            else:
                if p1[0] > p2[0]:
                    measurements.append([p1, p2, side_name])
                else:
                    measurements.append([p2, p1, side_name])
    return measurements

def get_max_text_size(side_name, mask, text_center, fixed_position):
    if side_name == "r" or side_name == "l":
        center_x = text_center # get center of text in the relevant dimension
        col = mask[:, fixed_position] # just look at that dimension, because the other one is fixed
        positions = np.transpose((col == 255).nonzero()) # positions is a 1d array in this case
        # get closest values to center_y on left and right side
        left = positions[positions <= center_x]
        right = positions[positions > center_x]
        if len(left) > 0:
            closest_left = np.max(left)
        else:
            closest_left = 0

        if len(right) > 0:
            closest_right = np.min(right)
        else:
            closest_right = len(col)

        distance_to_closest_value = min(abs(closest_left - center_x), abs(closest_right - center_x))

    else:
        center_y = text_center
        row = mask[fixed_position, :]
        positions = np.transpose((row == 255).nonzero())
        left = positions[positions <= center_y]
        right = positions[positions > center_y]
        if len(left) > 0:
            closest_left = np.max(left)
        else:
            closest_left = 0

        if len(right) > 0:
            closest_right = np.min(right)
        else:
            closest_right = len(row)
        distance_to_closest_value = min(abs(closest_left - center_y), abs(closest_right - center_y))

    return distance_to_closest_value





def draw_measurement(img, p1, p2, side_name, fixed_positions, arrow_w, arrow_h, line_color, thin_line_width,
                     mask, font_size, font_path, padding, extra_kerning, text_color):
    '''
    Draws a single measurement into an image
    :param img: PIL image to draw in
    :param p1: 2d point
    :param p2: 2d point
    :param side_name: either l,r,t or b
    :param fixed_positions: either the x value for l and r or the y value for t and b in a list in this order
    :param mask: mask of where measurements are placed so far
    :param arrow_w: width of the arrows
    :param arrow_h: height of the arrows
    :param font_size: int
    :param font_path: path to the used font
    :param line_color: color to use for the lines
    :param thin_line_width: thickness to use in the lines
    :param padding: spacing between lines and text
    :param extra_kerning: extra spacing between letters in pixels
    :param text_color: color of the text
    :return: PIL image, [text, [x,y,w,h]]
    '''
    draw = ImageDraw.ImageDraw(img)
    if side_name == "l":
        meas_line = [fixed_positions[0], p1[1], fixed_positions[0], p2[1]]
        help_line1 = [fixed_positions[0], p1[1], p1[0], p1[1]]
        help_line2 = [fixed_positions[0], p2[1], p2[0], p2[1]]
        arrow1_rot = 0
        arrow2_rot = 180
        meas_center = [fixed_positions[0] - padding, int((p1[1] + p2[1]) / 2)]
        meas_rot = Image.ROTATE_90
        text_offset = [-padding, 0]
    elif side_name == "r":
        meas_line = [fixed_positions[1], p1[1], fixed_positions[1], p2[1]]
        help_line1 = [fixed_positions[1], p1[1], p1[0], p1[1]]
        help_line2 = [fixed_positions[1], p2[1], p2[0], p2[1]]
        arrow1_rot = 0
        arrow2_rot = 180
        meas_center = [fixed_positions[1] + padding, int((p1[1] + p2[1]) / 2)]
        meas_rot = Image.ROTATE_270
        text_offset = [padding, 0]
    elif side_name == "t":
        meas_line = [p1[0], fixed_positions[2], p2[0], fixed_positions[2]]
        help_line1 = [p1[0], fixed_positions[2], p1[0], p1[1]]
        help_line2 = [p2[0], fixed_positions[2], p2[0], p2[1]]
        arrow1_rot = -90
        arrow2_rot = 90
        meas_size = abs(p1[0] - p2[0])
        meas_center = [int((p1[0] + p2[0]) / 2), fixed_positions[2] - padding]
        meas_rot = None
        text_offset = [0, -padding]
    else:
        meas_line = [p1[0], fixed_positions[3], p2[0], fixed_positions[3]]
        help_line1 = [p1[0], fixed_positions[3], p1[0], p1[1]]
        help_line2 = [p2[0], fixed_positions[3], p2[0], p2[1]]
        arrow1_rot = -90
        arrow2_rot = 90
        meas_size = abs(p1[0] - p2[0])
        meas_center = [int((p1[0] + p2[0]) / 2), fixed_positions[3] + padding]
        meas_rot = None
        text_offset = [0, padding]

    # draw lines
    draw.line(meas_line, line_color, thin_line_width)
    draw.line(help_line1, line_color, thin_line_width)
    draw.line(help_line2, line_color, thin_line_width)
    arrow1_poly = get_arrow_head(np.array([meas_line[0], meas_line[1]]), arrow_w, arrow_h, arrow1_rot)
    arrow2_poly = get_arrow_head(np.array([meas_line[2], meas_line[3]]), arrow_w, arrow_h, arrow2_rot)
    draw.polygon(
        list(arrow1_poly.flatten()),
        fill=line_color)  # Imagedraw cant use np arrays :)
    draw.polygon(
        list(arrow2_poly.flatten()),
        fill=line_color)

    text_data = []

    min_x, min_y = np.min(arrow1_poly, axis=0)
    max_x, max_y = np.max(arrow1_poly, axis=0)
    # text_data.extend([["↗", [
    #                 int(min_x) - 2,
    #                 int(min_y) - 2,
    #                 int(abs(min_x - max_x) + 4),
    #                 int(abs(min_y - max_y) + 4)
    #             ]]])
    # min_x, min_y = np.min(arrow2_poly, axis=0)
    # max_x, max_y = np.max(arrow2_poly, axis=0)
    # text_data.extend([["↗", [
    #                 int(min_x) - 2,
    #                 int(min_y) - 2,
    #                 int(abs(min_x - max_x) + 4),
    #                 int(abs(min_y - max_y) + 4)
    #             ]]])

    txt = None

    horizontal = True if side_name in "tb" else False



    if horizontal:
        text_center = meas_center[0]
        fixed_position = meas_center[1] + text_offset[1]

        # add arrow to the text data
        # text_data.append(["↗", [meas_line[0] - 2,  # x
        #                         meas_line[1] - int(arrow_w / 2) - 2,  # y
        #                         meas_line[2] - meas_line[0] + 4,  # w
        #                         meas_line[3] - meas_line[1] + arrow_w + 4]])  # h
    else:
        text_center = meas_center[1]
        fixed_position = meas_center[0] + text_offset[0]

        # add arrow to the text data
        # text_data.append(["↗", [meas_line[0] - int(arrow_w / 2) - 2,  # x
        #                         meas_line[1] - 2,  # y
        #                         meas_line[2] - meas_line[0] + arrow_w + 4,  # w
        #                         meas_line[3] - meas_line[1] + 4]])  # h

    max_text_radius = get_max_text_size(side_name, mask.copy(), text_center, fixed_position)

    final_text_img, final_text = None, None


    i = 0
    while final_text is None and i < 8:
        i += 1
        text_img, text = gen_measurement(font_path, text_color, font_size, max(int(font_size / 10), 1), extra_kerning)
        text_w, text_h = text_img.size
        text_radius = int(text_w/2)

        if text_radius + 2*padding <= max_text_radius:
            final_text_img = text_img
            if meas_rot is not None:
                final_text_img = final_text_img.transpose(meas_rot)
            final_text = text

    if final_text is not None:
        img_W, img_H = final_text_img.size
        topleft_y = meas_center[1] - int(img_H / 2) + text_offset[1]
        topleft_x = meas_center[0] - int(img_W / 2) + text_offset[0]
        img.paste(final_text_img, (topleft_x,topleft_y))

        # update mask
        mask[topleft_y:topleft_y + img_H, topleft_x:topleft_x+img_W] = 255
        text_data.append([final_text, [meas_center[0] - int(img_W / 2) + text_offset[0],
                                meas_center[1] - int(img_H / 2) + text_offset[1], img_W, img_H], "measure"])

    return img, text_data, mask


def inner_measurements(points, sides, image: Image.Image, margin, gen, arrow_w, arrow_h, font_size, font, line_color,
                       thin_line_width=2, padding=5, extra_kerning=0, text_color=(0,0,0)):
    '''
    Draws inner measurements into an image
    :param points: list of points of the object
    :param image: PIL image to draw in
    :param margin: spacing between the object and the annotation
    :param gen: ImagepairGenerator
    :param arrow_w: width of the arrows
    :param arrow_h: height of the arrows
    :param font_size: int
    :param font: path to the used font
    :param line_color: color to use for the lines
    :param thin_line_width: thickness to use in the lines
    :param padding: spacing between lines and text
    :param extra_kerning: extra spacing between letters in pixels
    :param text_color: color of the text
    :return: PIL image, drawn texts in the image
    '''

    max_id = np.argmax(points, axis=0)
    [xmax, ymax] = points[max_id]

    min_id = np.argmin(points, axis=0)
    [xmin, ymin] = points[min_id]

    fixed_positions = [xmin[0] - margin, xmax[0] + margin, ymin[1] - margin, ymax[1] + margin]  # lrtb

    split_points, side_ids = split_points_by_sides(points, sides)
    measurements = choose_where_to_measure(split_points, side_ids)
    texts = []
    mask = np.zeros((image.size[1], image.size[0]))
    # draw = ImageDraw.ImageDraw(image)
    for i, measurement in enumerate(measurements):
        p1, p2, side_name = measurement
        image, text_data, mask = draw_measurement(image, p1, p2, side_name, fixed_positions, arrow_w, arrow_h, line_color,
                                            thin_line_width, mask, font_size, font, padding, extra_kerning, text_color)
        texts.extend(text_data)
    return image, texts


def cross_hatching_background(width, height, linecolor, thin_line_width, thick_line_width):
    '''
    Creates an image of size width, height with cross hatching. Spacing is randomly chosen and line_color and width can be parsed
    '''
    spacing = random.choice(list(range(10, 30)))

    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.ImageDraw(img)

    current_x = 0
    current_y = 0

    while current_x <= width + height or current_y <= height + height:
        current_y += spacing
        current_x += spacing
        draw.line([0, current_y, current_x, 0], fill=linecolor, width=thin_line_width)

    # draw random regular polygons on it
    for _ in range(10):
        radius = random.choice(range(50,200))
        draw.polygon(xy = ImageDraw._compute_regular_polygon_vertices([  random.choice(range(radius, width - radius)),
                                        random.choice(range(radius, height-radius)),
                                        radius],
                                        n_sides = random.choice([4,5,6,7]),
                                        rotation=0),
                     fill = 255,
                     outline=linecolor,
                     width = thick_line_width
        )

    return img


def cross_hatching(coords, img, line_color, thin_line_width, thick_line_width, chance):
    '''
    Cross hatch the background of the object
    :param coords: coords of the polygon
    :param img: image to draw in
    :param line_color: color of the lines
    :param thin_line_width: width of the lines for cross hatching
    :param thick_line_width: width of the countour lines
    :return: PIL image, boolean: if background empty
    '''
    W, H = img.size
    mask = Image.new("L", (W, H), 0)
    mask_draw = ImageDraw.ImageDraw(mask)
    mask_draw.polygon(list(coords.flatten()), fill=255, outline=0, width=3)
    empty_background = True
    if random.random() <= chance:
        empty_background = False
        img.paste(cross_hatching_background(W, H, line_color, thin_line_width, thick_line_width), mask=mask)
    else:
        img.paste(Image.new("L", (W,H),255), mask=mask)
    return img, empty_background


def generate_random_drawing_shape(resolution, img_res, n_samples, base_offset, noise_factor, aspect_ratio=[1,1], octaves=[3, 6],
                                  round_resolution=3):
    '''
    Generates random coords for a polygon of a technical drawing
    :param resolution: resolution of the image
    :param n_samples: number of samples (points in the polygon)
    :param base_offset: base value that gets added to the noise
    :param noise_factor: amplification factor for the noise
    :param aspect_ratio: tuple of stretch in x and y direction
    :param octaves: octaves to use to generate the noise
    :param round_resolution: for snapping the points
    :return: np array of 2d coords
    '''
    img_radius = int(img_res / 2)
    points = sample_unit_circle_uniform(n_samples)
    offset_pts, sides = shift_to_rectangle(points, aspect_ratio)
    offset_pts = offset_points_using_perlin_noise(offset_pts, base_offset, noise_factor, octaves=octaves,
                                                  round_resolution=round_resolution)

    coords = np.int32(offset_pts * int(resolution / 2))
    coords += np.array([img_radius, img_radius])
    return coords, sides

def get_random_gdt_icon(size):
    '''
    Generate image of a random GDT icon
    :param size: max. width of the resulting image
    :return: PIL image, text
    '''
    chars = {
        "q": "⌾",
        "f": "◯",
        "m": "◠",
        "l": "⌓",
        "i": "ￌ",
        "n": "↗",
        "o": "⌰",
        "p": "=",
        "j": "//",
        "d": "▱",
        "h": "∠",
        "k": "⌖"
    }
    font_path = "../resources/fonts/ANSI_GDT.ttf"
    typeface = ImageFont.truetype(font_path, size)
    c = random.choice("qfmlinopjdhk") # ANSI_GDT.ttf replaces these with the corresponding symbols in chars
    char_img = get_image_from_text(c, typeface, 0, (0,0,0), crop_y = True)
    ori_width, ori_height = char_img.size
    scale_factor = size/ori_width
    return char_img.resize((size,int(ori_height * scale_factor))), chars[c]


def get_random_gdt_block(size, typeface, extra_kerning, text_color, line_color, line_width):
    '''
    Generates a GDT text and image randomly
    :param size: height of the resulting image
    :param typeface: typeface to use for accuracy, reference point
    :param extra_kerning: kerning between letters
    :param text_color: color of the text
    :param line_color: color of the line
    :param line_width: width of the outer lines
    :return: PIL image, text in image
    '''
    # padding on each side of the text
    pad = 4 + extra_kerning
    # maximum font size for the given size
    max_font_size = size - 2 * line_width

    # get a random icon and the image
    icon_img, icon_text = get_random_gdt_icon(size)
    icon_w, icon_h = icon_img.size

    # accuracy float and the image
    accuracy = str(round(random.random(), ndigits=random.choice([1, 2, 3])))
    acc_img = get_image_from_text(accuracy, typeface, extra_kerning, text_color, "RGB", crop_y=True)
    acc_w, acc_h = acc_img.size
    if acc_h > max_font_size:  # resize if too large
        acc_img = acc_img.resize((int(acc_w * max_font_size / acc_h), max_font_size))
    acc_w, acc_h = acc_img.size

    # reference point and the image
    ref = random.choice(string.ascii_uppercase)
    ref_img = get_image_from_text(ref, typeface, extra_kerning, text_color, "RGB", crop_y=True)
    ref_w, ref_h = ref_img.size
    if ref_h > max_font_size:  # resize if too large
        ref_img = ref_img.resize((int(ref_w * max_font_size / ref_h), max_font_size))
    ref_w, ref_h = ref_img.size

    # W and H of new image
    W = icon_w + acc_w + ref_w + 4 * line_width + 6 * pad
    H = size + 2 * pad

    final_image = Image.new("RGB", (W, H), (255, 255, 255))

    # draw the lines
    draw = ImageDraw.ImageDraw(final_image)
    # vertically
    half_line_w = max(int(line_width / 2), 1) # clamp to one, so that this is not set to zero
    current_w = 0
    for img in [icon_img, acc_img, ref_img]:
        draw.line([current_w, 0, current_w, H], line_color, line_width)
        current_w += pad
        current_w += line_width
        # also paste images in here to make code shorter
        img_w, img_h = img.size
        y_spacing = int((H - img_h) / 2)
        final_image.paste(img, [current_w, y_spacing])
        current_w += img_w
        current_w += pad

    draw.line([W - half_line_w, 0, W - half_line_w, H], line_color, line_width)

    # horizontal:
    draw.line([0, 0, W, 0], line_color, line_width)
    draw.line([0, H - half_line_w, W, H - half_line_w], line_color, line_width)

    return final_image, icon_text + " " + accuracy + " " + ref

def create_drawing_mask(texts, coords, size, fill_poly=False):
    '''
    Creates a mask from texts, and the coords for the polygon
    :param texts: [string, [x,y,w,h],...]
    :param coords: coords to use in cv2.fillpoly or cv2.polylines
    :param size: image size
    :param fill_poly: if True, use fillpoly, else use polylines
    :return: cv2 binary mask
    '''
    text_mask = np.zeros([size[1], size[0]], dtype=np.float32)

    for text in texts:
        [x, y, w, h] = text[1]
        text_mask[x:x+w,y:y+h] = 255

    # swap x and y for this type of image
    coords[:, [0, 1]] = coords[:, [1, 0]]
    if fill_poly:
        cv2.fillPoly(text_mask, [coords], color=255)
    else:
        cv2.polylines(text_mask, [coords], isClosed=True, color= 255, thickness=2)

    return text_mask


def get_random_reference(size, typeface, text_color, line_color, line_width):
    '''
    Generate random reference point image
    :param size: int - width and height of the image
    :param typeface: typeface to use
    :param text_color: color of the text
    :param line_color: color of the lines
    :param line_width: width of the lines
    :return: PIL image, text
    '''
    ref = random.choice(string.ascii_uppercase)
    ref_img = get_image_from_text(ref, typeface, 0, text_color, "RGB", crop_y=True)
    ref_w, ref_h = ref_img.size
    img = Image.new("RGB", (size, size), (255, 255, 255))
    draw = ImageDraw.ImageDraw(img)
    half_line_w = int(line_width / 2)
    W, H = (size, size)
    # paste in ref img
    center_img = int(size / 2)
    img.paste(ref_img, [center_img - int(ref_w / 2), center_img - int(ref_h / 2)])
    # draw outer lines
    # horizontally
    draw.line([0, 0, W, 0], line_color, line_width)
    draw.line([0, H - half_line_w, W, H - half_line_w], line_color, line_width)
    # vertically
    draw.line([0, 0, 0, H], line_color, line_width)
    draw.line([W - half_line_w, 0, W - half_line_w, H], line_color, line_width)

    return img, ref

def get_position_for_image(texts, poly_coords, img_res, img_size, fill_poly = False):
    '''
    From the given texts and polygon create a mask image of img_res size and dilate it img_size/2 times.
    If fill poly, fill the polygon, otherwise just use the outlines.
    Then randomly sample the available positions and get reasonable estimate of which is closest to the center
    :return: center point, if no space left == [0,0]
    '''
    # create mask where it may be without overlapping
    mask = create_drawing_mask(texts, poly_coords.copy(), (img_res, img_res), fill_poly)

    # also set edges so it doesnt cut off at edge
    mask[0:1, 0:img_res] = 1
    mask[img_res - 1:img_res, 0:img_res] = 1
    mask[0:img_res, 0:1] = 1
    mask[0:img_res, img_res - 1:img_res] = 1

    # dilate
    mask = cv2.dilate(mask, kernel=np.ones([3, 3]),
                      iterations=int(img_size / 2))  # half because getting the center for it
    # choose from those positions
    positions = np.transpose((mask == 0).nonzero())
    try:
        center = find_best_coord(positions, int(img_res / 2), int(img_res / 2), bias=1, max_iterations=40)
    except IndexError:
        center = [0,0]
    return center
def add_random_arrows(img, texts, coords, font_size, text_gen, text_color, arrow_w, arrow_h, line_color, thin_line_width, fill_poly):
    '''
    For a given image, draws randomly draws arrows pointing to corners and puts text on them
    :param img: PIL image
    :param texts: measurements with their bbs
    :param coords: coords of the polygon
    :param font_size: font size
    :param text_gen: measurement text generator
    :param text_color: lightness of the text
    :param arrow_w: width of the arrow
    :param arrow_h: height of the arrow
    :param line_color: lightness of the lines
    :param thin_line_width: line width to use
    :param fill_poly: whether the arrows may be inside of the polygon. if true they cant
    :return: PIL image, texts
    '''
    img_res = img.size[0]
    draw = ImageDraw.ImageDraw(img)
    if random.choice([True, False]):
        arrow_text = random.choice(["R"] * 10 + ["", "Ra ", "Rz ", "+", "-", "±"]) + str(random_float()) + random.choice(
            [""] * 5 + ["°"])
    else:
        arrow_text = str(random_float()) + "x" + generate_angle_text()

    pointing_to = random.choice(coords)  # [x,y]
    angle = random.choice(
        list(range(15, 75)) + list(range(105, 165)) + list(range(195, 255)) + list(range(285, 345))
    )
    font_path = random.choice(text_gen.fonts_paths)
    typeface = ImageFont.truetype(font_path, font_size)
    arrow_text_image, arrow_text_mask = get_rotated_text_image(typeface, arrow_text, text_color, angle, mode="RGB")
    ar_txt_W, ar_txt_H = arrow_text_image.size

    # helpful computations for the drawings
    line_dir = rotate(np.array([1, 0]), -angle)

    line_size = (ar_txt_W ** 2 + ar_txt_H ** 2) ** 0.5

    end_line_x = int(pointing_to[0] + line_dir[0] * line_size)
    end_line_y = int(pointing_to[1] + line_dir[1] * line_size)

    line_center = [
        int(pointing_to[0] + line_dir[0] * line_size / 2),
        int(pointing_to[1] + line_dir[1] * line_size / 2)
    ]

    line_normal = rotate(line_dir, 90 if random.choice([True, False]) else -90)

    text_center = [
        int(line_center[0] + line_normal[0] * font_size),
        int(line_center[1] + line_normal[1] * font_size),
    ]

    placement_mask = create_drawing_mask(texts, coords.copy(), (img_res, img_res), fill_poly)

    text_min_x = text_center[0] - int(ar_txt_W / 2)
    text_min_y = text_center[1] - int(ar_txt_H / 2)

    if np.sum(placement_mask[text_min_x:text_min_x+ar_txt_W, text_min_y:text_min_y+ar_txt_H]) == 0:
        # draw all the things
        arrow_poly = get_arrow_head(pointing_to, arrow_w, arrow_h, rotation=-angle + 90)
        draw.polygon(
            list(arrow_poly.flatten()),
            # +90 because triangle is pointing up by default
            fill=line_color)
        draw.line([pointing_to[0], pointing_to[1], end_line_x, end_line_y], line_color, thin_line_width)
        img.paste(arrow_text_image, [text_center[0] - int(ar_txt_W / 2), text_center[1] - int(ar_txt_H / 2)],
                  mask=arrow_text_mask)
        # register the text
        texts.extend([[arrow_text,
                       [text_center[0] - int(ar_txt_W / 2), text_center[1] - int(ar_txt_H / 2), ar_txt_W, ar_txt_H], "measure"]])

        # add the arrow to the text as well
        min_x, min_y = np.min(arrow_poly, axis = 0)
        max_x, max_y = np.max(arrow_poly, axis = 0)
        # texts.extend([["↗", [
        #             int(min_x) - 2,
        #             int(min_y) - 2,
        #             int(abs(min_x - max_x) + 4),
        #             int(abs(min_y - max_y) + 4)
        #         ]]])
    return img, texts

def generate_angle_text():
    '''
    Generates random angle
    :return: string
    '''
    return str(round(random.random()*180, ndigits=random.choice([0,1]))) + "°"
def generate_angle_arc(coords, resolution, font_size, font_path, text_color):
    '''
    Generates all the data needed to draw an angle measurement
    :param coords: coords of the polygon
    :param resolution: size of the polygon
    :param font_size: font size
    :param font_path: font path
    :param text_color: lightness of the text
    :return: center, scaled_vector, rotated_coords, bb, angle_edge, offset_angle, angle_img, angle_text_pos, angle_mask, text
    '''
    # choose random edge
    edge_id = random.choice(range(len(coords)))
    pts = np.array([coords[edge_id], coords[(edge_id + 1) % (len(coords) - 1)]])

    # random angle to that line
    offset_angle = random.choice(range(6)) * 15.0 + 30.0  # random angle between 30 and 120 degrees in 15° steps
    # random length to that line
    target_length = random.choice(range(int(resolution / 4), resolution))
    # print("target", target_length)

    center_id = random.choice([0, 1])  # point id: rotate around this point and values of the vector
    # rescale to target_length
    current_length = abs(np.linalg.norm(pts[0] - pts[1]))
    if current_length > 0.5:
        center = pts[center_id]
        vector_at_00 = pts[0 if center_id == 1 else 1] - center
        # scale the vector
        scaled_vector = center + (target_length / current_length) * vector_at_00

        # rotate the scaled vector by offset_angle
        rotated_coords = rotate(scaled_vector - center, offset_angle)
        rotated_coords += center

        angle_edge = PIL_angle_between(vector_at_00)

        # get bb for arc drawing
        radius = np.linalg.norm(rotate(scaled_vector - center, angle_edge))
        bb = [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius]

        # insert the text
        # rotate the edge by half of the offset angle to get center of the arc
        arc_center = rotate(scaled_vector - center, offset_angle / 2)

        # offset it by some padding
        arc_center_offset = ((font_size) / np.linalg.norm(arc_center)) * arc_center
        scaled_arc_center = center + arc_center - arc_center_offset

        # get angle of text, generate text image
        typeface = ImageFont.truetype(font_path, font_size)
        text = generate_angle_text()
        if 0 < (angle_edge + offset_angle / 2) % 360 < 180:
            text_rot = -(angle_edge + (offset_angle / 2)) + 90
        else:
            text_rot = -(angle_edge + (offset_angle / 2)) - 90
        angle_img, angle_mask = get_rotated_text_image(typeface, text, text_color,
                                                       angle=text_rot, dilations=3,
                                                       mode="L")

        # get pos where to paste
        angle_W, angle_H = angle_img.size
        text_offset = np.array([angle_W / 2, angle_H / 2])
        angle_text_pos = scaled_arc_center - text_offset

        return center, scaled_vector, rotated_coords, bb, angle_edge, offset_angle, angle_img, angle_text_pos, angle_mask, text
    else:
        return None

def generate_random_drawing(text_gen, thin_line_width, thick_line_width, line_color, padding, outer_margin, inner_margin,
                            resolution, font_path, font_size, aspect_ratio, extra_kerning, text_color, title_typeface, n_samples=30, base_offset=0.2, noise_factor=1.5):
    '''
    Generates a drawing of a polygon with measurements
    :param text_gen: ImagepairGenerator
    :param thin_line_width: width of thin lines
    :param thick_line_width: width of thick lines
    :param line_color: color the lines
    :param padding: distance between lines and text
    :param outer_margin: margin of the outer measurements
    :param inner_margin: margin to the inner measurements
    :param resolution: size of the polygon. this is not exact. should be around twice this value though
    :param >>: path to the font to use
    :param font_size: size of the font
    :param aspect_ratio: tuple of stretch in x and y direction
    :param extra_kerning: extra spacing between letters in pixels
    :param text_color: color of the text
    :param title_typeface: typeface to use for the titles of the views
    :param n_samples: number of points in the polygon
    :param base_offset: base value to offset noise by
    :param noise_factor: amplification factor for the noise
    :return: PIL image in L mode, texts
    '''
    arrow_w, arrow_h = get_random_arrow_sizes()

    # set a resolution for the image
    img_res = resolution * 12
    img = Image.new("L", (img_res, img_res), 255)

    #-----------
    #  polygon
    #-----------

    # generate the coordiantes for the points in the polygon
    coords, sides = generate_random_drawing_shape(resolution, img_res, n_samples, base_offset, noise_factor, aspect_ratio)

    # draw the polygon using the thick lines size
    draw = ImageDraw.ImageDraw(img)
    last_coord = coords[0]
    for coord in coords[1:]:
        draw.line([last_coord[0], last_coord[1], coord[0], coord[1]], fill=line_color, width=thick_line_width)
        last_coord = coord

    draw.line([last_coord[0], last_coord[1], coords[0][0], coords[0][1]], fill=line_color, width=thick_line_width)

    #----------------
    #  measurements
    #----------------

    # list of texts
    texts = []
    # add the outer measurements
    img, text_data = outer_measurements(coords, img, outer_margin, text_gen, arrow_w, arrow_h, font_size, font_path,
                                        line_color, thin_line_width, padding, extra_kerning, text_color)
    texts.extend(text_data)

    # add the inner measurements
    img, text_data = inner_measurements(coords, sides, img, inner_margin, text_gen, arrow_w, arrow_h, font_size,
                                        font_path, line_color, thin_line_width, padding, extra_kerning, text_color)
    texts.extend(text_data)

    # add cross hatching
    img, empty_background = cross_hatching(coords, img, line_color, thin_line_width, thick_line_width, chance=0.5)

    #------------------------
    # random angled arrows
    #------------------------
    for _ in range(4):
        img, texts = add_random_arrows(img, texts, coords, font_size, text_gen, text_color, arrow_w, arrow_h, line_color, thin_line_width, not empty_background)

    #----------------------
    #  random angles
    #----------------------
    for i in range(3):
        # get positions for drawing
        arc_data = generate_angle_arc(coords, resolution, font_size, font_path, text_color)
        if arc_data is not None:
            center, scaled_vector, rotated_coords, bb, angle_edge, offset_angle, angle_img, angle_text_pos, angle_mask, text = arc_data
            angle_W, angle_H = angle_img.size

            placement_mask = create_drawing_mask(texts, coords.copy(), (img_res, img_res), not empty_background)

            if np.sum(placement_mask[   int(angle_text_pos[0]):int(angle_text_pos[0]+angle_W),
                                        int(angle_text_pos[1]):int(angle_text_pos[1]+angle_H)]) == 0:

                # draw lines
                draw.line([center[0], center[1], rotated_coords[0], rotated_coords[1]],line_color, thin_line_width) # rotated line
                draw.line([center[0], center[1], scaled_vector[0], scaled_vector[1]],line_color, thin_line_width) # line in polygon

                # draw the arc
                draw.arc(bb, angle_edge, angle_edge + offset_angle, fill = line_color, width = thin_line_width)
                # draw the arrows
                arrow1_poly = get_arrow_head(np.array([rotated_coords[0], rotated_coords[1]]),
                               arrow_w,
                               arrow_h,
                               (angle_edge + offset_angle - 90) + 90)
                draw.polygon(
                    list(arrow1_poly.flatten()), # this is pil rotation, so clockwise
                    fill=line_color)

                arrow2_poly = get_arrow_head(np.array([scaled_vector[0], scaled_vector[1]]),
                               arrow_w,
                               arrow_h,
                               (angle_edge - 90) - 90)

                draw.polygon(
                    list(arrow2_poly.flatten()), # this is pil rotation, so clockwise
                    fill=line_color)

                min_x, min_y = np.min(arrow1_poly, axis=0)
                max_x, max_y = np.max(arrow1_poly, axis=0)
                # texts.extend([["↗", [
                #     int(min_x) - 2,
                #     int(min_y) - 2,
                #     int(abs(min_x - max_x) + 4),
                #     int(abs(min_y - max_y) + 4)
                # ]]])

                min_x, min_y = np.min(arrow2_poly, axis=0)
                max_x, max_y = np.max(arrow2_poly, axis=0)
                # texts.extend([["↗", [
                #     int(min_x) - 2,
                #     int(min_y) - 2,
                #     int(abs(min_x - max_x) + 4),
                #     int(abs(min_y - max_y) + 4)
                # ]]])


                # paste into image
                img.paste(angle_img, [int(angle_text_pos[0]), int(angle_text_pos[1])], angle_mask)

                # update bbs
                texts.extend([[text, [int(angle_text_pos[0]), int(angle_text_pos[1]), angle_W, angle_H], "measure"]])



    #-------------
    #   gdts
    #--------------
    font_path = random.choice(text_gen.fonts_paths)
    gdt_size = max(min(font_size+10, 50), 25)
    typeface = ImageFont.truetype(font_path, gdt_size)
    # get image
    gdt_img, text = get_random_gdt_block(gdt_size, typeface, extra_kerning, text_color, line_color, thin_line_width)
    gdt_w, gdt_h = gdt_img.size
    # get coordinates
    gdt_center = get_position_for_image(texts, coords.copy(), img_res, gdt_img.size[0])
    # paste
    if gdt_center != [0,0]:
        gdt_top_left = [gdt_center[0] - int(gdt_w/2), gdt_center[1] - int(gdt_h/2)]
        img.paste(gdt_img, gdt_top_left)

    texts.extend([[text, [gdt_center[0] - int(gdt_w/2), gdt_center[1] - int(gdt_h/2), gdt_w, gdt_h], "measure"]])

    # ref point
    # get image
    ref_img, text = get_random_reference(gdt_size, typeface, text_color, line_color, thin_line_width)
    ref_w, ref_h = ref_img.size
    # get coordinates
    ref_center = get_position_for_image(texts, coords.copy(), img_res, ref_img.size[0])
    if ref_center != [0,0]:
        ref_top_left = [ref_center[0] - int(ref_w/2), ref_center[1] - int(ref_h/2)]
        img.paste(ref_img, ref_top_left)
    texts.extend([[text, [ref_center[0] - int(ref_w/2), ref_center[1] - int(ref_h/2), ref_w, ref_h], "ref"]])

    #--------------
    #  title block
    #--------------

    text = random.choice(string.ascii_uppercase)
    if random.random() > 0.9:
        text += "-" + text
    title_image = get_image_from_text(text, title_typeface, extra_kerning, text_color, mode="RGB", crop_y=True)
    title_w, title_h = title_image.size
    title_center = get_position_for_image(texts, coords.copy(), img_res, max(title_w, title_h),fill_poly=True)
    if title_center != [0,0]:
        title_top_left = [title_center[0] - int(title_w/2), title_center[1] - int(title_h/2)]
        img.paste(title_image, title_top_left)
    texts.extend([[text, [title_center[0] - int(title_w/2), title_center[1] - int(title_h/2), title_w, title_h], "ref"]])

    #----------
    # circles
    #---------
    n_circles = random.choices([0,1,2,3], weights=(10,2,1,1))[0]
    circle_coords = random.sample(list(coords), k=n_circles)
    draw = ImageDraw.ImageDraw(img)
    for circle_coord in circle_coords:
        circle_radius = random.choice(range(20,70))
        draw.ellipse([circle_coord[0] - circle_radius, circle_coord[1] - circle_radius,
                      circle_coord[0] + circle_radius, circle_coord[1] + circle_radius],
                     fill=None, outline=line_color, width=thin_line_width)

    # get bounding box
    bbox = getbb(img, pad=2)

    #---------------
    # dashed lines
    #---------------
    if empty_background:

        horizontal = random.choice([True, False])
        dash_distance = random.choice(range(20, 50))
        dash_lengths = [random.choice(range(40, 100)), random.choice(range(20, 50))]


        if horizontal:
            center_y = int(img_res / 2)
            current_x = 0
            i = 0
            while current_x < img_res:
                dash_len = dash_lengths[i % 2]
                draw.line([current_x, center_y, current_x + dash_len, center_y], line_color, thin_line_width)
                current_x += dash_len + dash_distance
                i += 1
        else:
            center_x = int(img_res / 2)
            current_y = 0
            i = 0
            while current_y < img_res:
                dash_len = dash_lengths[i % 2]
                draw.line([center_x, current_y, center_x, current_y + dash_len], line_color, thin_line_width)
                current_y += dash_len + dash_distance
                i += 1

    # crop to content
    cropped = img.crop(bbox)

    # offset the texts by the crop
    texts = offset_text(texts, -bbox[0], -bbox[1])
    return cropped, texts

class DrawingGenerator(object):

    def __init__(self,thin_line_width, line_color, padding, outer_margin,  tokens, norms, materials_flat, extra_kerning, text_color,title_typeface, base_font_path = "../resources/fonts"):
        '''
        Iterator class to generate random drawings
        :param thin_line_width: width of thin lines
        :param line_color: color the lines
        :param padding: distance between lines and text
        :param outer_margin: margin of the outer measurements
        :param tokens: dictionary of tokens to use for the text gen
        :param norms: dictionary of tokens to use for the text gen
        :param materials_flat: dictionary of tokens to use for the text gen
        :param extra_kerning: extra spacing between letters in pixels
        :param text_color: color of the text
        :param title_typeface: typeface to use for titles of views
        :param base_font_path: base path for fonts. one in this dictionary will be chosen randomly
        '''
        self.text_gen = ImagePairGenerator(tokens, norms, materials_flat, base_font_path,
                                      add_noise=False,
                                      probabilities=[0.0, 0.0, 0.0, 1.0, 1.0, 1.0])
        self.thin_line_width = thin_line_width
        self.line_color = line_color
        self.padding = padding
        self.outer_margin = outer_margin
        self.font_size = random.choice([20,22,24,26,28])
        self.font_path = random.choice(self.text_gen.fonts_paths)
        self.extra_kerning = extra_kerning
        self.text_color = text_color
        self.title_typeface = title_typeface

    def __iter__(self):
        return self

    def __next__(self):
        '''
        Calls the .next() function. Does not support exact font sizes.
        '''
        return self.next()

    def next(self, resolution, aspect_ratio):
        return generate_random_drawing(
                                text_gen=self.text_gen,
                                thin_line_width=self.thin_line_width,
                                thick_line_width=self.thin_line_width*2,
                                line_color = self.line_color,
                                padding = self.padding,
                                outer_margin=self.outer_margin,
                                inner_margin=int(self.outer_margin/2),
                                resolution=resolution,
                                font_path=self.font_path,
                                font_size=self.font_size,
                                aspect_ratio = aspect_ratio,
                                extra_kerning=self.extra_kerning,
                                text_color=self.text_color,
                                title_typeface=self.title_typeface
                                )
