import os
import string
import sys
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
import cv2
from gen_table_rec_data import *
import math
from gen_technical_drawing_polygons import DrawingGenerator
from gen_3d_views import View3DGenerator
class TechDrawGenerator(object):
    def __init__(self, tokens, norms, materials_flat, view_gen, base_font_path="./resources/fonts"):
        '''
        Class to generate random technical drawings.
        '''
        self.tokens = tokens
        self.norms = norms
        self.materials = materials_flat
        self.text_gen = ImagePairGenerator(tokens, norms, materials_flat, base_font_path, add_noise=False)
        self.view_gen = view_gen
        self.H = 2048
        self.W = 3072
        self.final_H = 2048
        self.final_W = 2048

    def __iter__(self):
        return self

    def __next__(self):
        '''
        Calls the .next() function.
        '''
        return self.next()

    @staticmethod
    def choose_n_seps_for_1d(size, max_size, min_output, max_output):
        '''
        Seperates a line of size into [min_output, max_output] sections. To do this samples from a gaussian distribition with mu = 10 * size/max_size
        :return: int
        '''
        ratio = size / max_size

        max_mu = 5
        mu = int(ratio * max_mu)

        return min(max(int(random.gauss(mu, 2)), min_output), max_output)

    @staticmethod
    def get_lines(cell_height, small_font_size, large_font_size, padding=5):
        '''
        For a given cell_height and two possible font sizes (and padding between the lines), generates a list of which font size to use in which line in the cell
        :return: list of font sizes
        '''
        # running variable to keep track of how mich of the cell was used already
        current_h = padding
        lines = []
        while current_h < cell_height:
            # mostly use the smaller font size
            choice = random.choices([small_font_size, large_font_size], weights=[0.85, 0.15])[0]
            lines.append(int(choice))
            current_h += choice + padding
        # the last one is always too much
        if len(lines) > 1:
            return lines[:-1]
        else:
            return []

    @staticmethod
    def choose_cells_in_sequence_to_join(sequence):
        '''
        :param sequence: list of sequential indices
        :return: subsets of that list to join together
        '''
        # which seperations between cells to join
        joins = []
        for i in range(len(sequence) - 1):
            join = random.choice([True, False])
            joins.append(join)

        # join those cells
        joined_subsets = []
        subset = []
        for i, join in enumerate(joins):
            # if join, add the next element to this sequence
            if join:
                subset.append(sequence[i + 1])
            else:
                if len(subset) > 1:
                    joined_subsets.append(subset)
                subset = [sequence[i + 1]]
        if len(subset) > 1:
            joined_subsets.append(subset)

        return joined_subsets

    def merge_cells(self, col_list, n_cells_list):
        '''
        Merge some cells in the col_list.
        :param col_list: list of columns = list of cell with bbs
        :param n_cells_list: list of number of rows in a column
        :return: updated col_list
        '''
        same_n_cells_col_ids = find_sequences_of_same_values_in_list(n_cells_list)  # col seqs with same amount of cells
        for sequence in same_n_cells_col_ids:
            # number of cells in those columns
            n_cells = n_cells_list[sequence[0]]
            # iterate over the rows
            for i in range(n_cells):
                # for a given row, choose which cells to join
                joins = self.choose_cells_in_sequence_to_join(sequence)
                # print(f"in row {i}, joining cols {joins}")
                for join in joins:
                    # cells that get joined together
                    list_of_cells_in_join = []
                    # enumerate over the columns that get joined in this row
                    for j, col_id in enumerate(join):
                        list_of_cells_in_join.append(col_list[col_id][i])
                        # all but the first cell get deleted
                        if j > 0:
                            col_list[col_id][i] = None
                    # first cell gets changed to include all others
                    first_cell = col_list[join[0]][i]
                    # update the first cell
                    new_first_cell = [first_cell[0], first_cell[1], list_of_cells_in_join[-1][2],
                                      list_of_cells_in_join[-1][3]]
                    col_list[join[0]][i] = new_first_cell

        return col_list

    def generate_and_paste_text_in_cell(self, cell, small_font_size, large_font_size, block_img, empty_chance=0.2,
                                        cutt_off_chance=0.5, center=True, extra_kerning = 0, text_color = (0,0,0)):
        '''
        Generates a random text and pastes it into the cell.
        :param cell: [min_x,min_y,max_x,max_y]
        :param small_font_size: int
        :param large_font_size: int
        :param block_img: PIL image to paste into
        :param empty_chance: chance to leave the cell empty
        :param cutt_off_chance: chance to cut off a line, otherwise will run until the end of the cell
        :param center: if True, may center text using the large_font-size
        :param extra_kerning: extra spacing between letters in pixels
        :param text_color: color of the text
        :return: block_img, texts
        '''
        texts = []
        [min_x, min_y, max_x, max_y] = cell
        cell_w = max_x - min_x
        cell_h = max_y - min_y

        big_kerning = extra_kerning
        small_kerning = int(extra_kerning/2)

        if random.random() > empty_chance:  # 20% chance to leave cell empty
            # get number of lines
            line_padding = random.randint(7, 20) + extra_kerning
            line_sizes = self.get_lines(cell_h, small_font_size, large_font_size, padding=line_padding)
            offset_y = line_padding

            for line_size in line_sizes:
                # get random font
                font_path = random.choice(self.text_gen.fonts_paths)
                # try a word in this pos
                found = False
                offset_x = line_padding
                if line_size != large_font_size:
                    kerning_to_use = small_kerning
                else:
                    kerning_to_use = big_kerning
                t = 0 # try
                while not found and t < 32:
                    t += 1
                    img, text = self.text_gen.next(font_size=line_size, font_path=font_path, stretch_factor=0.7, extra_kerning = kerning_to_use, text_color = text_color)
                    text_width, text_height = img.size
                    # check if fits
                    if text_width <= cell_w - (line_padding * 2):
                        found = True
                        if line_size == large_font_size and random.choice(
                                [True, False]) and center:  # 50% chance to center big text center text
                            center_cell = cell_w / 2
                            text_x = min_x + int(center_cell - text_width / 2)
                            text_y = min_y + offset_y
                            offset_x = None

                        else:  # align text left
                            text_x = min_x + offset_x
                            offset_x += text_width + line_padding
                            text_y = min_y + offset_y
                        block_img.paste(img, [text_x, text_y])
                        offset_y += text_height + line_padding
                        texts.append([text, [text_x, text_y, text_width, text_height], "info"])

                # try to continue text, if not centered
                continue_line = True if random.random() > cutt_off_chance else False
                if offset_x is not None and continue_line:
                    tries = 3
                    tries_left = tries
                    while tries_left > 0 and continue_line:
                        img, text = self.text_gen.next(font_size=line_size, font_path=font_path, stretch_factor=0.7, extra_kerning = kerning_to_use, text_color = text_color)
                        text_width, text_height = img.size
                        # check if fits
                        if text_width + offset_x + line_padding <= cell_w:
                            # it does fit
                            # reset counter
                            tries_left = tries
                            text_x = min_x + offset_x
                            offset_x += text_width + line_padding
                            text_y = min_y + offset_y - text_height - line_padding
                            block_img.paste(img, [text_x, text_y])
                            texts.append([text, [text_x, text_y, text_width, text_height], "info"])
                            continue_line = random.choice([True, False])
                        else:
                            tries_left -= 1
        return block_img, texts

    def draw_cells(self, col_list, draw_block_img: ImageDraw, block_img, small_font_size, large_font_size, line_color,
                   line_width, extra_kerning, text_color):
        '''
        Draw cells in col_list on draw_block_img using line_color and line_width and paste text images from text_gen into block_img. For this use small_font_size and large_font_size with extra_kerning and text_color.
        :return: draw_block_img, block_img, texts in image with their bbs
        '''
        texts = []
        for col in col_list:
            for cell in col:
                if cell is not None:
                    # draw cell on the image
                    draw_block_img.rectangle(cell, fill=None, outline=line_color, width=line_width)
                    # get data
                    block_img, gen_texts = self.generate_and_paste_text_in_cell(cell, small_font_size, large_font_size,
                                                                                block_img, extra_kerning = extra_kerning, text_color = text_color)

                    texts.extend(gen_texts)

        return draw_block_img, block_img, texts

    def generate_cells(self, width, height):
        '''
        Generates a grid of cells for a given image width and height.
        :return: col_list, n_cells_list, min_cell_height, max_cell_height
        '''
        # end pos of last column
        last_col_end = 0
        # number of cols
        cols = self.choose_n_seps_for_1d(width, self.W, 2, 6)
        # cell width based on number of cols
        base_cell_width = int(width / cols)
        # possible deviation from that width
        jitter_size = int(base_cell_width * 0.2)
        col_list = []
        n_cells_list = []

        # get max and min cell height for fonts later
        max_cell_height = 0
        min_cell_height = sys.maxsize

        # generate grid-esque of cells
        for i in range(0, cols):  # for all columns
            col_min_x = last_col_end  # start is old endpoint
            if i == cols - 1:  # if at the last col go until the last pixel
                col_max_x = width - 1
            else:  # else go until cell width + some random value
                col_max_x = (i + 1) * base_cell_width + random.randint(-jitter_size, jitter_size)

            # choose number of cells in the column
            min_n_cells = math.ceil(height / base_cell_width) + 1
            n_cells = self.choose_n_seps_for_1d(height, self.H * 0.5, min_n_cells, 6)
            n_cells_list.append(n_cells)

            # for all cells in the col
            base_cell_height = int(height / n_cells)

            if base_cell_height > max_cell_height:
                max_cell_height = base_cell_height

            if base_cell_height < min_cell_height:
                min_cell_height = base_cell_height

            cell_list = []
            for j in range(0, n_cells):
                cell_min_y = (j) * base_cell_height
                cell_max_y = (j + 1) * base_cell_height
                cell_list.append([col_min_x, cell_min_y, col_max_x, cell_max_y])
            # update values
            col_list.append(cell_list)
            last_col_end = col_max_x
        return col_list, n_cells_list, min_cell_height, max_cell_height

    def generate_info_block_image(self, width, height, line_color, line_width, extra_kerning, text_color):
        '''
        Generates a random info block for a given width and height.
        :return: PIL image.
        '''
        # empty image
        block_img = Image.new(mode='RGB', size=(width, height), color=(255, 255, 255))
        # draw on that img
        draw_block_img = ImageDraw.ImageDraw(block_img)

        # generate cells
        col_list, n_cells_list, min_cell_height, max_cell_height = self.generate_cells(width, height)

        # define two font sizes: small and large
        small_font_size = int(min_cell_height / 4)
        large_font_size = int(max_cell_height * 0.75)

        # merge some cells
        col_list = self.merge_cells(col_list, n_cells_list)

        # draw cells with text in them
        draw_block_img, block_img, texts = self.draw_cells(col_list, draw_block_img, block_img, small_font_size,
                                                           large_font_size, line_color, line_width, extra_kerning, text_color)

        return block_img, texts

    def generate_random_size_for_block(self, min_width, min_height, d_x, d_y, main=False):
        '''
        Generates a random size using min_width, d_x, min_height and d_y. If main, the width gets set to self.W if it is over half.
        :return: block_width, block_height
        '''
        block_width = int((random.random() * d_x + min_width) * self.W)
        block_height = int((random.random() * d_y + min_height) * self.H)
        if main:
            if block_width > 0.5 * self.W:
                block_width = self.W
        return block_width, block_height

    def generate_info_block(self, min_width, min_height, d_x, d_y, line_color, line_width, extra_kerning, text_color, main=False):
        '''
        Calls generate_info_block image and generates a random size for the image beforehand using min_width, d_x, min_height and d_y. If main, the width gets set to self.W if it is over half.
        '''
        (block_width, block_height) = self.generate_random_size_for_block(min_width, min_height, d_x, d_y, main=main)
        block_image, texts = self.generate_info_block_image(block_width, block_height, line_color, line_width, extra_kerning, text_color)
        return block_image, texts

    def get_random_block_position(self, bbs, block_width, block_height, anchor_point):
        '''
        Finds all eligible positions for a block of given block_width and block_height using the bbs of previously pasted blocks. Also tries to get the position as close as possible to anchor_point.
        :return: [top left y, top left x], if no space return None
        '''

        mask = np.zeros([self.H, self.W])

        # size of the expansions
        border_y = int(block_height / 2)
        border_x = int(block_width / 2)

        # set edges to 1
        mask[0:border_y, :] = 1
        mask[:, 0:border_x] = 1
        mask[self.H - border_y:self.H, :] = 1
        mask[:, self.W - border_x:self.W] = 1
        for bb in bbs:
            [ymin, ymax, xmin, xmax] = bb
            # paste 1s for all bbs with border around them
            mask[max(0, ymin - border_y): min(self.H - 1, ymax + border_y),
            max(0, xmin - border_x): min(self.W - 1, xmax + border_x)] = 1

        positions = np.transpose((mask == 0).nonzero())

        if len(positions) > 0:
            best_pos_y, best_pos_x = find_best_coord(positions, anchor_point[0], anchor_point[1], 1, 32)
            return np.array([best_pos_y, best_pos_x]) - np.array([border_y, border_x])
        else:
            return None

    def add_text_box(self, draw_img, img, bbs, line_color, line_width, extra_kerning, text_color):
        '''
        Adds a Box of random text to img, appends the coords to bbs and return the texts with their bounding boxes
        :return: img, bbs, gen_texts, draw_img
        '''
        # determine size and positioning
        # size
        block_width, block_height = self.generate_random_size_for_block(0.1, 0.1, 0.1, 0.2)

        # then, get corner that it hugs
        corner = np.array([random.choice([0, self.H]), random.choice([0, self.W])])

        position = self.get_random_block_position(bbs, block_width, block_height, corner)
        if position is not None:
            if random.random() > 0.2:
                draw_img.rectangle([position[1], position[0], position[1] + block_width, position[0] + block_height],
                                   None, outline=line_color, width=line_width)

            small_font_size = self.text_gen.get_random_font_size(sigma=5, min=15, max=35)
            large_font_size = self.text_gen.get_random_font_size(sigma=7, min=35, max=70)

            img, gen_texts = self.generate_and_paste_text_in_cell(
                [position[1], position[0], position[1] + block_width, position[0] + block_height],
                small_font_size, large_font_size, img, empty_chance=0.0, cutt_off_chance=0.1, center=True, extra_kerning = extra_kerning, text_color = text_color)

            bb = [position[0], position[0] + block_height, position[1], position[1] + block_width]
            bbs.append(bb)
        else:
            gen_texts = []
        return img, bbs, gen_texts, draw_img

    @staticmethod
    def get_triangle_positions(translation_x, translation_y, scale=1):
        '''
        Generates a unit equilateral triangle and translates it and scales it.
        :return: list of coordinates: [x1,y1,x2,y2,x3,y3]
        '''
        # top left will always be at 0,0 before translation
        top_left = [translation_x, translation_y]
        top_right = [scale + translation_x, translation_y]
        triangle_height = scale * 3 ** 0.5 / 2
        bottom = [scale * 0.5 + translation_x, translation_y + triangle_height]
        pts = []
        for pt in [top_left, top_right, bottom]:
            pts.extend(pt)
        return pts

    def get_surface_sign(self, text_img, scale, line_color=(0, 0, 0), line_width=3, padding=10, text_right=True):
        '''
        Generates a surface sign with the given text_img pasted in.
        :param text_img: PIL image
        :param scale: side lengths of the triangle
        :param line_color: color of the lines, triple
        :param line_width: int
        :param padding: int
        :param text_right: boolean, if True text is pasted to the right side, otherwise to the left
        :return:
        '''
        # get triangle points
        pts = self.get_triangle_positions(1024, 1024, scale)

        # create empty image
        img = Image.new(mode='RGB', size=(2048, 2048), color=(255, 255, 255))

        # paste triangle in there
        draw = ImageDraw.ImageDraw(img)
        draw.polygon(pts, None, line_color, width=line_width)

        # line continuing the right line in the triangle
        end_line_x = pts[2] + (pts[2] - pts[4])
        end_line_y = pts[3] + (pts[3] - pts[5])
        draw.line([pts[2], pts[3], end_line_x, end_line_y], line_color, line_width)

        if text_right:
            # line at the top of the text
            draw.line([end_line_x, end_line_y, end_line_x + text_img.size[0] + padding, end_line_y], line_color,
                      line_width)

            img = img.filter(ImageFilter.SMOOTH)
            # paste text image in correct position
            img.paste(text_img, [int(end_line_x + padding), int(end_line_y + padding)])
            # crop the image
            img = img.crop([
                pts[0],
                end_line_y,
                end_line_x + text_img.size[0] + padding,
                pts[5]
            ])
        else:
            img = img.filter(ImageFilter.SMOOTH)
            # paste text image in correct position
            text_W, text_H = text_img.size
            img.paste(text_img, [int(pts[2] - padding - text_W), int(pts[3] - padding - text_H)])
            # crop the image
            img = img.crop([
                min(pts[0], int(pts[2] - padding - text_W)),
                min(end_line_y, int(pts[3] - padding - text_H)),
                end_line_x,
                pts[5]
            ])

        return img

    def get_random_surface_text(self):
        '''
        Generates a random surface measurement
        :return: string
        '''
        if random.random() > 0.2:
            # random float
            f = random.random() * 3
            # random number of digits
            digits = random.randint(1, 3)
            f *= 10 ** digits
            f = round(f)
            f /= 10 ** digits
            text = str(f)
            # add random prefix
            prefix = random.choice(["Ra ", "Rz "])
            text = prefix + text
        else:
            text = random.choice(string.ascii_lowercase)

        return text

    def get_random_measurement_text(self):
        '''
        Generates a random measurement
        :return: string
        '''
        # random float
        f = random.random() * 3
        # random number of digits
        digits = random.randint(1, 3)
        f *= 10 ** digits
        f = round(f)
        f /= 10 ** digits
        text = str(f)
        # add random prefix
        prefix = random.choice(["+", "-", "±"])
        text = prefix + text

        return text

    def get_surface_block_line(self, typeface, large_typeface, pattern, scale, line_color=(0, 0, 0), line_width=3,
                               padding=10, extra_kerning = 0, text_color = (0,0,0), text_right=True):
        '''
        Generates a surface block line using a pattern, a typeface, scale for the triangle and font size, a line_color and width and a padding. If text_right, text will be pasted to the right side of the triangle, otherwise to the left side.
        :return: PIL image, generated texts
        '''
        texts = []
        img = Image.new(mode='RGB', size=(2048, 2048), color=(255, 255, 255))
        if pattern == 'equation':
            # left side of equation
            text = self.get_random_surface_text()
            text_img = get_image_from_text(text, typeface, extra_kerning, text_color, mode="RGB")
            left = self.get_surface_sign(text_img, scale, line_color, line_width, padding, text_right)
            texts.append([text, [0, 0, left.size[0], left.size[1]], "surface"])

            img.paste(left, [0, 0])

            # get '=' image
            draw = ImageDraw.Draw(img)
            draw.text(xy=(left.size[0] + padding, int(scale * 0.8)), text='=', fill=(0, 0, 0), font=typeface,
                      anchor="lt")
            bbox = draw.textbbox(xy=(left.size[0] + padding, int(scale * 0.8)), text='=', font=typeface,
                                 anchor="lt")  # left, top, right, bottom
            texts.append(['=', [bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]], "surface"])

            # right side of equation
            text = self.get_random_surface_text()
            text_img = get_image_from_text(text, typeface, extra_kerning, text_color, mode="RGB")
            right = self.get_surface_sign(text_img, scale, line_color, line_width, padding, text_right)
            img.paste(right, [bbox[2] + padding, 0])
            texts.append([text, [bbox[2] + padding, 0, right.size[0], right.size[1]], "surface"])

            img = img.crop([0, 0, bbox[2] + padding + right.size[0], max(left.size[1], right.size[1])])
        elif pattern == 'parenthesis':
            # left side of equation
            text = self.get_random_surface_text()
            text_img = get_image_from_text(text, typeface, extra_kerning, text_color, mode="RGB")
            left = self.get_surface_sign(text_img, scale, line_color, line_width, padding, text_right)
            texts.append([text, [0, 0, left.size[0], left.size[1]], "surface"])

            img.paste(left, [0, 0])

            # (
            draw = ImageDraw.Draw(img)
            draw.text(xy=(left.size[0] + padding, 0), text='(', fill=(0, 0, 0), font=large_typeface, anchor="lt")
            bbox = draw.textbbox(xy=(left.size[0] + padding, 0), text='(', font=large_typeface,
                                 anchor="lt")  # left, top, right, bottom
            texts.append(['(', [bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]], "surface"])

            current_x = bbox[2]

            n_surfaces = random.choice([1, 2, 3])

            max_y = 0

            for _ in range(n_surfaces):
                text = self.get_random_surface_text()
                text_img = get_image_from_text(text, typeface, extra_kerning, text_color, mode="RGB")
                right = self.get_surface_sign(text_img, scale, line_color, line_width, padding, text_right)
                img_w, img_h = right.size
                if img_h > max_y:
                    max_y = img_h
                img.paste(right, [current_x + padding, 0])
                texts.append([text, [current_x + padding, 0, img_w, img_h], "surface"])
                current_x += padding + img_w

            # (
            draw = ImageDraw.Draw(img)
            draw.text(xy=(current_x + padding, 0), text=')', fill=(0, 0, 0), font=large_typeface, anchor="lt")
            bbox = draw.textbbox(xy=(current_x + padding, 0), text=')', font=large_typeface,
                                 anchor="lt")  # left, top, right, bottom
            texts.append([')', [bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]], "surface"])

            img = img.crop([0, 0, bbox[2], max_y])
        elif pattern == 'single':
            text = self.get_random_surface_text()
            text_img = get_image_from_text(text, typeface, extra_kerning, text_color, mode="RGB")
            surf_img = self.get_surface_sign(text_img, scale, line_color, line_width, padding, text_right)
            texts.append([text, [0, 0, surf_img.size[0], surf_img.size[1]], "surface"])

            img_w, img_h = surf_img.size
            img.paste(surf_img, [0, 0])
            img = img.crop([0, 0, img_w, img_h])
        else:
            img = None
            texts = None

        return img, texts

    def get_surface_block(self, line_width=3, line_color=(0, 0, 0), padding=10, extra_kerning= 0, text_color = (0,0,0)):
        '''
        Generates a random image of a surface block.
        :return: img, generated texts
        '''
        # determine parameters
        scale = random.choice(list(range(50, 70)))

        available_fonts = self.text_gen.fonts_paths.copy()
        font = random.choice(available_fonts)
        typeface = ImageFont.truetype(font, int(scale / 2))

        padding += extra_kerning

        large_typeface = ImageFont.truetype(font, int(scale * 2))

        if random.random() > 0.9:
            text_right = False
        else:
            text_right = True

        rows = random.choices([1, 2, 3, 4], [0.8, 0.1, 0.075, 0.025])[0]
        pattern = random.choices(['equation', 'parenthesis', 'single'], [1, 1, 1])[0]

        # new empty image
        img = Image.new(mode='RGB', size=(2048, 2048), color=(255, 255, 255))

        # generate rows
        offset_y = padding * 3
        max_x = 0
        texts = []
        for i in range(rows):
            line_img, gen_texts = self.get_surface_block_line(typeface, large_typeface, pattern, scale, line_color,
                                                              line_width, padding, extra_kerning, text_color, text_right)
            offset_texts = self.offset_text(gen_texts, 0, offset_y)
            texts.extend(offset_texts)
            line_w, line_h = line_img.size
            if line_w > max_x:
                max_x = line_w
            # paste row into image
            img.paste(line_img, [0, 0 + offset_y])
            offset_y += line_h + padding * 3

        # crop image to content
        img = img.crop([0, 0, max_x, offset_y])

        return img, texts

    def add_surface_block(self, draw_img, img, bbs, line_width, line_color, extra_kerning, text_color):
        '''
        Generates an image for surface annotation and pastes it into the img.
        :return: img, bbs, gen_texts, draw_img
        '''
        gen_image, gen_texts = self.get_surface_block(line_width, line_color,10, extra_kerning, text_color)
        block_width, block_height = gen_image.size

        corner = np.array([random.choice([0, self.H]), random.choice([0, self.W])])
        position = self.get_random_block_position(bbs, block_width, block_height, corner)

        if position is not None:
            bbs.append([position[0], position[0] + block_height, position[1], position[1] + block_width])

            img.paste(gen_image, [position[1], position[0]])
            offset_texts = self.offset_text(gen_texts, position[1], position[0])
        else:
            offset_texts = []

        return img, bbs, offset_texts, draw_img

    @staticmethod
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

    def add_info_blocks(self, img, bbs, text_in_image, line_color, line_width, extra_kerning, text_color):
        n_info_blocks = random.choices(population=[1, 2, 3], weights=[0.75, 0.15, 0.1], k=1)[0]

        main_block_img, texts = self.generate_info_block(0.35, 0.1, 0.15, 0.2, line_color, line_width, extra_kerning, text_color, True)
        main_block_width, main_block_height = main_block_img.size

        bbs.append([self.H - main_block_height, self.H, self.W - main_block_width, self.W])
        img.paste(main_block_img, [self.W - main_block_width, self.H - main_block_height])
        texts = self.offset_text(texts, self.W - main_block_width, self.H - main_block_height)

        text_in_image.extend(texts)
        # -------------------------------
        #       MISC INFO BLOCKS
        # -------------------------------
        if n_info_blocks == 3:
            # top left
            misc_image, texts = self.generate_info_block(0.2, 0.2, 0.1, 0.1, line_color, line_width, extra_kerning, text_color)
            misc_image_width, misc_image_height = misc_image.size

            bbs.append([0, misc_image_height, 0, misc_image_width])
            img.paste(misc_image, [0, 0])
            # dont need to offset because it starts at 0,0
            text_in_image.extend(texts)

            # top right
            misc_image, texts = self.generate_info_block(0.2, 0.2, 0.1, 0.1, line_color, line_width, extra_kerning, text_color)
            misc_image_width, misc_image_height = misc_image.size

            bbs.append([0, misc_image_height, self.W - misc_image_width, self.W])
            img.paste(misc_image, [self.W - misc_image_width, 0])

            texts = self.offset_text(texts, self.W - misc_image_width, 0)
            text_in_image.extend(texts)

        elif n_info_blocks == 2:
            is_top_left = random.choice([True, False])
            if is_top_left:
                misc_image, texts = self.generate_info_block(0.2, 0.2, 0.1, 0.1, line_color, line_width, extra_kerning, text_color)
                misc_image_width, misc_image_height = misc_image.size

                bbs.append([0, misc_image_height, 0, misc_image_width])
                img.paste(misc_image, [0, 0])
                text_in_image.extend(texts)
            else:  # top right
                misc_image, texts = self.generate_info_block(0.2, 0.2, 0.1, 0.1, line_color, line_width, extra_kerning, text_color)
                misc_image_width, misc_image_height = misc_image.size

                bbs.append([0, misc_image_height, self.W - misc_image_width, self.W])
                img.paste(misc_image, [self.W - misc_image_width, 0])
                # offset and extend the main text list
                texts = self.offset_text(texts, self.W - misc_image_width, 0)
                text_in_image.extend(texts)
        return img, bbs, text_in_image

    def get_edge_image(self, typeface, line_width, line_color, scale, padding, extra_kerning, text_color):
        padding += extra_kerning
        # new empty image
        img = np.full((1024, 1024, 3), 255)
        # convert to int32, so that: https://stackoverflow.com/questions/23830618/python-opencv-typeerror-layout-of-the-output-array-incompatible-with-cvmat
        img = img.astype(np.int32)
        # arrow in positive y and negative x
        img = cv2.arrowedLine(img, np.array([512, 512]), np.array([512 - scale, 512 + scale]), line_color, line_width,
                              tipLength=0.2)
        # line in positive x (to the left)
        img = cv2.line(img, np.array([512, 512]), np.array([512 + scale, 512]), line_color, line_width)
        # line in negative y (vertical)
        img = cv2.line(img, np.array([512, 512]), np.array([512, 512 - scale]), line_color, line_width)

        # convert to PIL image
        img = np.uint8(img)
        conv_img = Image.fromarray(img)

        # get measurement image
        text = self.get_random_measurement_text()
        text_img = get_image_from_text(text, typeface, extra_kerning, text_color, mode="RGB")
        img_w, img_h = text_img.size

        # paste into image
        conv_img.paste(text_img, [512 + padding, 512 - img_h - padding])

        # crop image to content
        crop_x = 512 - scale - padding
        crop_y = min(512 - img_h - padding, 512 + scale - padding)

        conv_img = conv_img.crop([crop_x,
                                  crop_y,
                                  max(512 + img_w + padding, 512 - scale + padding),
                                  512 + scale + padding,
                                  ])
        # append texts
        texts = [[text, [
            scale,
            0,
            img_w + 3 * padding ,
            scale], "edge"]]

        return conv_img, texts

    def get_edge_block(self, line_width, line_color, extra_kerning, text_color):
        '''
        Generates a random image of a surface block.
        :return: img, generated texts
        '''
        # determine parameters
        scale = random.choice(list(range(50, 70)))
        texts = []
        available_fonts = self.text_gen.fonts_paths.copy()
        font = random.choice(available_fonts)
        typeface = ImageFont.truetype(font, int(scale / 2))
        edge_image, gen_texts = self.get_edge_image(typeface, line_width, line_color, scale, 10, extra_kerning, text_color)
        texts.extend(gen_texts)
        if random.random() > 0.5:
            # another one next to it
            another_edge_image, gen_texts = self.get_edge_image(typeface, line_width, line_color, scale, 10, extra_kerning, text_color)
            both_images = Image.new("RGB", (
            edge_image.size[0] + another_edge_image.size[0], edge_image.size[1] + another_edge_image.size[1]),
                                    color=(255, 255, 255))
            both_images.paste(edge_image, [0, 0])
            both_images.paste(another_edge_image, [edge_image.size[0], 0])
            texts.extend(self.offset_text(gen_texts, edge_image.size[0], 0))
            edge_image = both_images
        return edge_image, texts

    def add_edge_box(self, draw_img, img, bbs, line_width, line_color, extra_kerning, text_color):
        '''
        Generates an image for surface annotation and pastes it into the img.
        :return: img, bbs, gen_texts, draw_img
        '''
        gen_image, gen_texts = self.get_edge_block(line_width, line_color, extra_kerning, text_color)
        block_width, block_height = gen_image.size

        corner = np.array([random.choice([0, self.H]), random.choice([0, self.W])])

        position = self.get_random_block_position(bbs, block_width, block_height, corner)
        if position is not None:
            bbs.append([position[0], position[0] + block_height, position[1], position[1] + block_width])

            img.paste(gen_image, [position[1], position[0]])
            offset_texts = self.offset_text(gen_texts, position[1], position[0])
        else:
            offset_texts = []
        return img, bbs, offset_texts, draw_img

    def add_drawing(self, img, bbs, resolution, drawing_gen):
        '''
        Generates technical drawing and pastes it into the img.
        :return: img, bbs, gen_texts
        '''

        if random.choice([True, False]):  # 50% chance to stretch in one direction
            if random.choice([True, False]):
                aspect_ratio = [random.choice([1.5, 2, 2.5, 3]), 1]
            else:
                aspect_ratio = [1, random.choice([1.5, 2, 2.5, 3])]
        else:
            aspect_ratio = [1, 1]

        drawing, gen_texts = drawing_gen.next(resolution, aspect_ratio)

        block_width, block_height = drawing.size

        corner = np.array([int(self.W / 2), int(self.H / 2)])
        position = self.get_random_block_position(bbs, block_width, block_height, corner)
        if position is not None:
            bbs.append([position[0], position[0] + block_height, position[1], position[1] + block_width])

            img.paste(drawing, [position[1], position[0]])
            offset_texts = self.offset_text(gen_texts, position[1], position[0])
        else:
            offset_texts = []
        return img, bbs, offset_texts

    # def add_title_block(self, img, bbs, typeface, drawing_bb, extra_kerning, text_color):
    #
    #     text = random.choice(string.ascii_uppercase)
    #     if random.random() > 0.9:
    #         text += "-" + text
    #     text_image = get_image_from_text(text, typeface, extra_kerning, text_color, mode="RGB")
    #     W, H = text_image.size
    #     gen_texts = [[text, [0, 0, W, H]]]
    #     # choose point where to paste
    #     # this is always going to be a corner of the drawing
    #     [ymin, ymax, xmin, xmax] = drawing_bb
    #     anchor = np.array([xmin, ymin])
    #     if random.choice([True, False]):
    #         anchor = np.array([anchor[0], ymax])
    #         anchor -= np.array([0, H])
    #     if random.choice([True, False]):
    #         anchor = np.array([xmax, anchor[1]])
    #         anchor -= np.array([W, 0])
    #
    #     bbs.append([anchor[1], anchor[1] + H, anchor[0], anchor[0] + W])
    #
    #     img.paste(text_image, [anchor[0], anchor[1]])
    #     offset_texts = self.offset_text(gen_texts, anchor[0], anchor[1])
    #
    #     return img, bbs, offset_texts

    def draw_coords(self, img, frame_positions, line_color, line_width, typeface, text_color):
        '''
        Draws a coordinate system into img using the positions of the outer frame, a line color and width and a given typeface
        :return: PIL image, texts: [text, [x,y,w,h,],...]
        '''
        coords = ""

        if random.choice([True, False]):  # add coordinates
            if random.choice([True, False]):  # on all sides
                coords += "lrtb"
            else:  # on 2 sides only
                if random.choice([True, False]):
                    coords += random.choice(["l", "r"])
                    coords += random.choice(["t", "b"])
        else:
            return img, []

        [minx, miny, frame_W, frame_H] = frame_positions

        coord_size = random.choice(range(30, 50)) # distance inner frame to outer frame
        half_coord_size = int(coord_size/2) # for easier computation later
        n_coords_horizontally = random.choice(range(4,9)) # number of cells
        n_coords_vertically = random.choice(range(4,9))
        coord_width = int(frame_W / n_coords_horizontally)
        coord_height = int(frame_H / n_coords_vertically)


        draw = ImageDraw.ImageDraw(img)

        outer_frame_coords = np.array([minx, miny, minx+frame_W, miny+frame_H])
        coord_block_centers = []
        if "t" in coords: # top
            # draw outer frame
            outer_frame_coords += np.array([0,-coord_size,0,0])
            # draw lines between outer and inner frame that separate the cells
            offset_x = coord_width + minx
            for i in range(n_coords_horizontally-1):
                draw.line([offset_x,miny,offset_x,miny-coord_size], fill=line_color, width=line_width)
                offset_x += coord_width
            # get the positions for the texts
            for i in range(n_coords_horizontally):
                coord_block_centers.append([minx + int((i+0.5) * coord_width),miny-half_coord_size])
        # do the same for all other sides
        if "b" in coords: # bottom
            outer_frame_coords += np.array([0,0,0,coord_size])
            offset_x = coord_width + minx
            for i in range(n_coords_horizontally - 1):
                draw.line([offset_x, miny + frame_H, offset_x, miny + frame_H + coord_size], fill=line_color, width=line_width)
                offset_x += coord_width
            for i in range(n_coords_horizontally):
                coord_block_centers.append([minx + int((i+0.5) * coord_width),miny+frame_H+half_coord_size])
        if "l" in coords: # left
            outer_frame_coords += np.array([-coord_size,0,0,0])
            offset_y = coord_height + miny
            for i in range(n_coords_vertically - 1):
                draw.line([minx-coord_size,offset_y,minx,offset_y], fill=line_color,
                          width=line_width)
                offset_y += coord_height
            for i in range(n_coords_horizontally):
                coord_block_centers.append([minx-half_coord_size, miny + int((i+0.5) * coord_height)])
        if "r" in coords: # right
            outer_frame_coords += np.array([0,0,coord_size,0])
            offset_y = coord_height + miny
            for i in range(n_coords_vertically - 1):
                draw.line([minx + frame_W,offset_y,minx + frame_W + coord_size,offset_y], fill=line_color,
                          width=line_width)
                offset_y += coord_height
            for i in range(n_coords_horizontally):
                coord_block_centers.append([minx+frame_W+half_coord_size, miny + int((i+0.5) * coord_height)])

        # actually draw the rect now
        draw.rectangle(list(outer_frame_coords), fill=None, outline=line_color, width=line_width)
        # paste the texts in
        texts = []
        for center_coord in coord_block_centers:
            text = random.choice(string.ascii_uppercase + "0123456789")
            text_img = get_image_from_text(text, typeface, 0, text_color, "RGB")
            text_img_w, text_img_h = text_img.size
            top_left = list(np.array(center_coord) - np.round(np.array([text_img_w, text_img_h])/2).astype(int))
            img.paste(text_img, top_left)
            texts.append([text, [top_left[0], top_left[1], text_img_w, text_img_h], "coord"])

        return img, texts

    def next(self):
        '''
        Generates a random drawing with an information block.
        :return: PIL image
        '''
        # will use PIL, since text_gen uses PILLOW
        img = Image.new(mode='RGB', size=(self.W, self.H), color=(255, 255, 255))

        line_lightness = random.randint(0, 122)
        line_color = (line_lightness, line_lightness, line_lightness)
        line_width = random.choice([1, 2, 3])

        text_lightness = random.randint(0, 50)
        text_color = (text_lightness, text_lightness, text_lightness)

        extra_kerning = random.choices(range(15), [20].extend([1]*14))[0]

        draw_img = ImageDraw.ImageDraw(img)
        bbs = []

        text_in_image = []

        # -------------------------------
        #     INFO BLOCKS
        # -------------------------------

        img, bbs, text_in_image = self.add_info_blocks(img, bbs, text_in_image, line_color, line_width, extra_kerning, text_color)

        # -------------------------------
        #       TEXT BLOCKS
        # -------------------------------

        for _ in range(random.choices([1, 2, 3], weights=[0.8, 0.15, 0.05])[0]):
            # add textboxes randomly
            img, bbs, gen_texts, draw_img = self.add_text_box(draw_img, img, bbs, line_color, line_width, extra_kerning, text_color)
            text_in_image.extend(gen_texts)

        # -------------------------------
        #      SURFACE + EDGES
        # -------------------------------

        if random.random() > 0.4:
            img, bbs, gen_texts, draw_img = self.add_surface_block(draw_img, img, bbs, line_width, line_color, extra_kerning, text_color)
            text_in_image.extend(gen_texts)

        if random.random() > 0.1:
            img, bbs, gen_texts, draw_img = self.add_edge_box(draw_img, img, bbs, line_width, line_color, extra_kerning, text_color)
            text_in_image.extend(gen_texts)

        # -------------------------------
        #           DRAWING
        # -------------------------------
        available_fonts = self.text_gen.fonts_paths.copy()
        chosen_font = random.choice(available_fonts)
        title_typeface = ImageFont.truetype(chosen_font, size=random.choice(range(50, 100)))

        drawing_gen = DrawingGenerator(line_width, line_lightness, 10, 100, self.tokens, self.norms, self.materials, extra_kerning, text_color, title_typeface)

        if random.random() > 0.5:
            img, bbs, gen_texts = self.add_drawing(img, bbs, 400, drawing_gen)
            text_in_image.extend(gen_texts)

        img, bbs, gen_texts = self.add_drawing(img, bbs, 300, drawing_gen)
        text_in_image.extend(gen_texts)

        img, bbs, gen_texts = self.add_drawing(img, bbs, 200, drawing_gen)
        text_in_image.extend(gen_texts)

        if random.random() > 0.5:
            img, bbs, gen_texts = self.add_drawing(img, bbs, 100, drawing_gen)
            text_in_image.extend(gen_texts)

        # -------------------------------
        #           3d Views
        # -------------------------------
        try:
            view_model = next(self.view_gen)
            model_W, model_H = view_model.size
            # random scale
            scale_factor = random.random() * 0.3 + 0.2
            view_model = view_model.resize((int(model_W * scale_factor), int(model_H * scale_factor)))
            model_W, model_H = view_model.size
            position = self.get_random_block_position(bbs, model_W, model_H, [random.choice([0, self.W]), random.choice([0, self.H])])
            if position is not None:
                img.paste(view_model, [position[1], position[0]])
                bbs.append([position[0], position[0] + model_H, position[1], position[1] + model_W])
        except Exception:
            print("3d model error")

        # -------------------------------
        #    ADDITIONAL LARGE TEXT
        # -------------------------------

        for _ in range(random.choice(range(1,16))):

            text_img, text = self.text_gen.next(font_size=random.choice(range(50,100)),
                                                font_path=None, # this way it chooses from all fonts, even Bungee
                                                stretch_factor=1,
                                                extra_kerning = random.choice(range(5,20)),
                                                text_color = text_color)
            text_img_W, text_img_H = text_img.size
            text_pos = self.get_random_block_position(bbs, text_img_W, text_img_H, [random.choice([0, self.W]), random.choice([0, self.H])])
            if text_pos is not None:
                img.paste(text_img, [text_pos[1], text_pos[0]])
                bbs.append([text_pos[0], text_pos[0] + text_img_H, text_pos[1], text_pos[1] + text_img_W ])
                text_in_image.extend([[text, [text_pos[1], text_pos[0], text_img_W, text_img_H], "large"]])

        # -------------------------------
        #            FRAME
        # -------------------------------

        spacing_left = random.choice(range(50, 200))
        spacing_right = random.choice(range(50, 200))
        spacing_top = random.choice(range(50, 200))
        spacing_bottom = random.choice(range(50, 200))

        new_W = self.W - spacing_right - spacing_left
        new_H = self.H - spacing_top - spacing_bottom

        frame_img = Image.new("RGB", (self.W, self.H), (255,255,255))

        frame_img.paste(img.resize((new_W, new_H)), (spacing_left, spacing_top))

        text_in_image = scale_text(text_in_image, new_W/self.W, new_H/self.H)
        text_in_image = self.offset_text(text_in_image, spacing_left, spacing_top)

        frame_draw = ImageDraw.ImageDraw(frame_img)
        frame_draw.rectangle([spacing_left, spacing_top, spacing_left + new_W, spacing_top + new_H], fill=None, outline=line_color, width=line_width)

        img = frame_img

        # -------------------------------
        #         COORDINATES
        # -------------------------------

        coordinates_typeface = ImageFont.truetype(random.choice(self.text_gen.fonts_paths),
                                            size=random.choice(range(20,30)))

        frame_positions = [spacing_left, spacing_top, new_W, new_H]

        img, gen_texts = self.draw_coords(img, frame_positions, line_color, line_width, coordinates_typeface, text_color)
        text_in_image.extend(gen_texts)

        #--------------------------------
        #      SCALE TO FINAL SIZE
        #--------------------------------

        x_rescale = self.final_W/self.W
        y_rescale = self.final_H/self.H
        img = img.resize((self.final_W, self.final_H))
        # bbs for text need to be changed as well
        text_in_image = scale_text(text_in_image, x_rescale, y_rescale)

        # -------------------------------
        #       HIGHLIGHT TEXT
        # -------------------------------

        # draw_img = ImageDraw.ImageDraw(img)
        # for txt in text_in_image:
        #     [xmin, ymin, w, h] = txt[1]
        #     draw_img.rectangle([xmin, ymin, xmin + w, ymin + h], None, (0, 255, 0), 2)

        # -------------------------------
        #         POST-PROCESSING
        # -------------------------------

        # apply salt and pepper noise in distinct steps
        if random.random() > 0.95:  # salt noise foreground
            img = self.text_gen.salt(img, 0.05, rgb=True)

        if random.random() > 0.98:  # pepper noise foreground
            img = self.text_gen.pepper(img, 0.02, rgb=True)

        if random.random() > 0.95:  # perlin noise background
            print("adding p noise")
            img = self.text_gen.add_perlin_noise(img, downsample_size=(256, 256), alpha=0.1)

        if random.random() > 0.3:  # smooth image
            img = img.filter(ImageFilter.SMOOTH)

        return img, text_in_image


if __name__ == "__main__":
    TOTAL_SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    VAL_SIZE = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    base_path = sys.argv[3] if len(sys.argv) > 3 else "../data/generated_drawings/"  # base path for the dataset
    token_path = sys.argv[4] if len(sys.argv) > 4 else "../resources/pickle/dictionary.pickle"  # pickle dump of a list of words that can be generated in the drawing
    norm_path = sys.argv[5] if len(sys.argv) > 5 else "../resources/pickle/common_norms.pkl"  # pickle dump of a list of string with norms that may be included in the table
    material_path = sys.argv[6] if len(sys.argv) > 6 else "../resources/pickle/materials.pkl"  # pickle dump of a list of strings with materials
    models_path = sys.argv[7] if len(sys.argv) > 7 else "../resources/3d_models"  # 3d models that may be used to generate images. see: https://github.com/stnoah1/mcb
    # load all the pickled data
    tokens, norms, materials, materials_flat = load_data(token_path, norm_path, material_path)
    view_gen = View3DGenerator(models_path)
    draw_gen = TechDrawGenerator(tokens, norms, materials_flat,view_gen, base_font_path="../resources/fonts")


    # preparing both dicts for population
    data_dict_train = {
        "metainfo": {
            "dataset_type": "TextDetDataset",
            "task_name": "textdet",
            "category": [{"id": 0, "name": "text"}]
        },
        "data_list": []
    }

    data_dict_test = {
        "metainfo": {
            "dataset_type": "TextDetDataset",
            "task_name": "textdet",
            "category": [{"id": 0, "name": "text"}]
        },
        "data_list": []
    }

    image_dir = os.path.join(base_path, "images")
    os.makedirs(image_dir, exist_ok=True)

    for i in range(TOTAL_SIZE):
        print(i)
        img_width = draw_gen.W
        img_height = draw_gen.H
        img_dict = {
            "instances": [],
            "img_path": f"{i}.png",
            "height": img_height,
            "width": img_width
        }

        img, texts = next(draw_gen)
        for text in texts:
            [xmin, ymin, W, H] = text[1]
            # convert from int64 to int to make it json serializable
            xmin = int(xmin)
            ymin = int(ymin)
            W = int(W)
            H = int(H)
            poly_dict = {
                "polygon": [xmin, ymin, xmin+W, ymin, xmin+W, ymin+H, xmin, ymin+H, xmin, ymin],
                "bbox": [xmin, ymin, xmin+W, ymin+H],
                # bounding box of rectangle
                "bbox_label": 0,
                "ignore": 0,
            }
            img_dict["instances"].append(poly_dict)
        img.save(os.path.join(image_dir, f"{i}.png"))
        # if test/ val set not full
        if len(data_dict_test["data_list"]) < VAL_SIZE:
            # randomly put img in test / val or train set
            if random.choice([True, False]):
                data_dict_train["data_list"].append(img_dict)
            else:
                data_dict_test["data_list"].append(img_dict)
        # if alraedy full only populate train set
        else:
            data_dict_train["data_list"].append(img_dict)

        # save both json files
        with open(os.path.join(base_path, 'det_train.json'), 'w', encoding='utf-8') as f:
            json.dump(data_dict_train, f, ensure_ascii=True, indent=4)

        with open(os.path.join(base_path, 'det_test.json'), 'w', encoding='utf-8') as f:
            json.dump(data_dict_test, f, ensure_ascii=True, indent=4)