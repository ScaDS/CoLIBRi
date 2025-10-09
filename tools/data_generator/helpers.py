import random
import sys

import cv2
import numpy as np
from PIL import Image, ImageFont, ImageDraw, ImageFilter
from skimage.color import rgb2gray
from skimage.filters import threshold_otsu, sobel
from skimage.transform import hough_line, hough_line_peaks
from scipy.stats import mode
import pickle as pkl
def findShearAngle(image_edges):
    '''
    Gets the shear angle of an image. Assumes that the image is rotated, so that all horizontal lines are at 0°.
    :param image_edges: Edge detected image
    :return: Angle to shear the image by.
    '''
    # hough transformation
    h, theta, d = hough_line(image_edges)
    accum, angles, dists = hough_line_peaks(h, theta, d)
    # convert angles to degress
    angles = np.rad2deg(angles)
    # remove all angles that are not from vertical lines
    angles = np.delete(angles, np.where(abs(abs(angles) - 90) > 10))
    # if there are such angles, use the most common one and shear with that
    if len(angles) > 0:
        # get most common
        angle = mode(angles, keepdims=False)[0]
        # convert to usable angle for shearing
        if angle > 0:
            angle -= 90
        else:
            angle += 90
    else:
        angle = 0

    return angle


def findTiltAngle(image_edges):
    '''
    Finds the rotation angle of an image
    :param image_edges: edge detected image
    :return: Angle to fix the rotation.
    '''
    h, theta, d = hough_line(image_edges)
    accum, angles, dists = hough_line_peaks(h, theta, d)
    angles = np.rad2deg(angles)
    # only look at horizontal lines
    angles = np.delete(angles, np.where(abs(angles) > 10))
    if len(angles) > 0:
        angle = mode(angles, keepdims=False)[0]
    else:
        angle = 0

    return angle

def findEdges(bina_image):
    '''
    Applies a sobel filter to the input image
    :param bina_image: binary image
    :return: binary image
    '''
    image_edges = sobel(bina_image)
    return image_edges

def binarizeImage(RGB_image):
    '''
    Binarizes an rgb image
    :param RGB_image: rgb image
    :return: binary image
    '''
    image = rgb2gray(RGB_image)
    threshold = threshold_otsu(image)
    bina_image = image < threshold

    return bina_image

def parse_comma_float(x: str):
    '''
    Parses a float using ',' instead of '.'
    :param x: string of a float
    :return: float
    '''
    x = x.strip()
    x = x.replace(",", ".")
    return float(x)

def remove_dupes(list):
    '''
    Removes duplicates from a list
    :param list: python list
    :return: duplicate-free list
    '''
    new_list = []
    for item in list:
        if item not in new_list:
            new_list.append(item)
    return new_list

def parse_string_of_list(string_of_a_list, parenthesis='[]'):
    '''
    Parses a string version of any given 1D-list to a list
    :param string_of_a_list: String of a list
    :param parenthesis: string of the used parenthesis
    :return: parsed list
    '''
    string_of_a_list = string_of_a_list.strip()
    parsed_list = string_of_a_list.strip(parenthesis).replace("'", "").split(', ')
    if '' in parsed_list:
        parsed_list.remove('')
    return parsed_list

def remove_empty_strings_from_list(list_of_strings):
    '''
    Removes the empty strings from a list
    '''
    return_data = []
    for s in list_of_strings:
        if len(s) > 0:
            return_data.append(s)
    return return_data

def load_pickle_file(path):
    '''
    Loads a pickle file and returns it
    :param path: path to the file
    :return: data in the file
    '''
    with open(path, "rb") as file:
        data = pkl.load(file)
        file.close()
    return data

def find_sequences_of_same_values_in_list(list):
    '''
    Given a list of items, tries to find sequences of equivalent items and returns a list of these sequences (encoded using their indices)
    '''
    last_item = None
    sequences = []
    sequence = []
    for i in range(len(list)):
        # if seq continues
        if list[i] == last_item:
            sequence.append(i)
        # if it doesnt
        else:
            # check if it is longer than 1
            if len(sequence) > 1:
                # if so add to return data
                sequences.append(sequence)
            # create new sequence with this item
            sequence = [i]
        last_item = list[i]
    # check if last sequence is long enough. This has to be done, since a sequence only gets added iff it breaks (which sequences at the end of the list dont)
    if len(sequence) > 1:
        sequences.append(sequence)

    return sequences

def offset_text(texts, offset_x, offset_y):
    '''
    Offsets the text bbs by offset_x and y
    '''
    offset_texts = []
    for text in texts:
        coords = text[1]
        offset_texts.append([text[0],
                             [int(coords[0]) + int(offset_x), int(coords[1]) + int(offset_y), int(coords[2]),
                              int(coords[3])], text[2]])
    return offset_texts

def scale_text(texts, scale_x, scale_y):
    '''
    Scales the text bbs by scale_x and scale_y
    '''
    offset_texts = []
    for text in texts:
        coords = text[1]
        offset_texts.append([text[0],
                             [int(coords[0] * scale_x),
                              int(coords[1] * scale_y),
                              int(coords[2] * scale_x),
                              int(coords[3] * scale_y)], text[2]])
    return offset_texts

def getbb(image: Image.Image, threshold = 150, pad = 0):
    '''
    Gets the bounding box for an PIL image
    :param image: PIL image
    :param threshold: threshold for the bounding box
    :param pad: padding on each side in pixels
    :return: [xmin, ymin, xmax, ymax]
    '''
    img = np.asarray(image)
    positions = np.transpose((img <= threshold).nonzero())
    if len(positions) > 0:
        [ymin, xmin] = np.min(positions, axis=0)
        [ymax, xmax] = np.max(positions, axis=0)
        return [max(xmin - pad, 0),
                max(ymin - pad, 0),
                min(xmax + pad, image.size[0]),
                min(ymax + pad, image.size[1])]
    else:
        return [0,0,0,0]



def crop_rgb_image_to_text_content(image: Image, crop_y=False):
    '''
    Crops a PIL image to its (black) contents
    '''
    grey_img = image.convert(mode="L")
    [min_x, min_y, max_x, max_y] = getbb(grey_img)
    pad = 2
    return image.crop((max(min_x-pad, 0), max(min_y - pad, 0) if crop_y else 0, max_x + pad, max_y + pad))

def get_image_from_char(char, typeface: ImageFont.ImageFont, color):
    '''
    Generates an image from a given char
    :param char: char to paste in image
    :param typeface: ImageDraw typeface to use
    :param color: color of the text
    :return: PIL image
    '''
    bbox = typeface.getbbox(char)
    image = Image.new("RGB", (bbox[2], bbox[3]), (255,255,255))
    draw = ImageDraw.ImageDraw(image)
    draw.text((0,0), char, fill=color, font = typeface)
    return image


def get_image_from_text(text, typeface, extra_kerning, color, mode='L', crop_y = False):
    '''
    Generate an image for a given text
    :param text: text to paste in image
    :param typeface: ImageFont typeface to use
    :param extra_kerning: additional spacing between letters in pixels
    :param color: color of the text
    :param mode: converts the image to this mode after generating
    :return: PIL image
    '''
    image = Image.new('RGB', (2048, 2048), color="white")
    current_x = -extra_kerning
    for char in text:
        current_x += extra_kerning
        char_img = get_image_from_char(char, typeface, color)

        image.paste(char_img, (current_x, 0))
        current_x += char_img.size[0]

    image = image.convert(mode)
    return crop_rgb_image_to_text_content(image, crop_y)

def random_float():
    number = random.random() * 10**random.choices([0,1,2], weights=[5,2,1])[0]
    number = round(number, ndigits=random.choices([1,2,3], weights=[3,2,1])[0])
    return number

def shift_coords(coords, shift_x, shift_y):
    '''
    Shifts the coords by shift_x and shift_y
    :param coords: list of 2d coords
    :param shift_x: shift for first dim
    :param shift_y: shift for second dim
    :return: list of shifted coords (np.array)
    '''
    new_coords = []
    for coord in coords:
        new_coords.append(np.array([coord[0] + shift_x, coord[1] + shift_y]))
    return new_coords

def rotate(vector, angle):
    '''
    Rotates a given vector by angle
    :param vector: np array of shape [2]
    :param angle: angle in degrees
    :return: rotated point
    '''
    theta = np.radians(angle)
    c, s = np.cos(theta), np.sin(theta)
    R = np.array(((c, -s), (s, c)))
    return np.matmul(R, vector)


def get_rotated_text_image(typeface, text, color, angle, dilations=3, mode="RGB"):
    '''
    Genarates an images based on text, typeface and color and rotates it by angle around its center counter-clockwise.
    :return: pil image with text, pil image: mask where the text is
    '''
    # get normal image
    img = get_image_from_text(text, typeface, 0, color, crop_y=True, mode=mode)
    W, H = img.size
    center_x = int(W / 2)
    center_y = int(H / 2)
    # rotate using built in
    if 90 < angle < 270:
        img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    img = img.rotate(angle, expand=True,
                     fillcolor=255 if mode == "L" else (255, 255, 255))  # rotates counter-clockwise around the center

    # calculate coords for that
    coords = shift_coords([[0, 0], [0, H], [W, H], [W, 0]], -center_x, -center_y)
    rot_coords = []
    for coord in coords:
        rot_coords.append(rotate(coord, -angle))
    rot_coords = np.array(shift_coords(rot_coords, center_x, center_y))
    min_x, miny = np.min(rot_coords, axis=0)
    text_coords = shift_coords(rot_coords, -min_x, -miny)

    # new mask image
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.ImageDraw(mask)
    draw.polygon(list(np.asarray(text_coords).flatten()), fill=255)
    for _ in range(dilations):
        mask = mask.filter(ImageFilter.MaxFilter(3))  # dilation
    return img, mask

def find_best_coord(eligible_coords, com_y, com_x, bias=1, max_iterations=16):
    '''
    Randomly samples eligible coords and tries to get a coordinate as close to the center of mass (com) as possible.
    This is done iteratively and if there isnt a better coord in max_iterations, use the current best one.
    :param eligible_coords: list of coordinates to randomly sample
    :param com_y: y coordinate of the center of mass
    :param com_x: x coordinate of the center of mass
    :param bias: bias for dimensions: float > 1 ==> bias towards x dim, float < 1 ==> bias towards y dim
    :param max_iterations: max samples bef
    :return:
    '''
    if bias == 0:
        bias = 1

    iterations_since_last_update = 0
    best_coord = [0,0]
    best_distance = sys.maxsize
    while iterations_since_last_update < max_iterations:
        random_coord = random.choice(eligible_coords)
        random_distance = abs(random_coord[0] - com_y) * 1/bias + abs(random_coord[1] - com_x) * bias
        if random_distance < best_distance:
            best_coord = random_coord
            best_distance = random_distance
            iterations_since_last_update = 0
        else:
            iterations_since_last_update += 1

    return best_coord[0], best_coord[1]

def unit_vector(vector):
    """ Returns the unit vector of the vector.  """
    return vector / np.linalg.norm(vector)

def angle_between(v1, v2):
    """ Returns the angle in radians between vectors 'v1' and 'v2'::

            >>> angle_between((1, 0, 0), (0, 1, 0))
            1.5707963267948966
            >>> angle_between((1, 0, 0), (1, 0, 0))
            0.0
            >>> angle_between((1, 0, 0), (-1, 0, 0))
            3.141592653589793
    """
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))

def PIL_angle_between(vector):
    default = np.array([1,0])
    deg = np.degrees(angle_between(default, vector))
    if vector[1] < 0: # upper half of circle
        deg *= -1
    return deg