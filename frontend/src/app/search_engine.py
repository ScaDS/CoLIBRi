import itertools

import numpy as np
from scipy.spatial import distance
from sklearn.neighbors import BallTree


class SearchEngine:
    def __init__(self, dataset, ids, metric, weights):
        """
        Class encapsulating a sklearn BallTree.
        This search tree uses hyperspheres to recursively divide the search space, similar to a kd-tree.
        :param dataset: array of vectors in the search space. shape: (n_samples, n_vector_dimenions)
        :param ids: list of ids to return when searching. should be of same length as the dataset
        :param metric: should be one of BallTree.valid_metrics
        :param weights: array of weights to use when computing distances. should be of length 7
        """
        self.ids = ids
        if metric == "colibri_distance":
            metric = self.colibri_distance
        self.weights = weights
        self.search_tree = BallTree(dataset, metric=metric)

    def query(self, query_vector, k):
        """
        Query the search tree using the query vector and return the ids of the k closest vectors.
        :param query_vector: search vector
        :param k: number of closest ids to return
        :return: k closest ids
        """
        dist, ind = self.search_tree.query(query_vector, k)
        return [self.ids[i] for i in ind[0]], dist

    def colibri_distance(self, v1, v2):
        """
        Computes distance between search vectors.
        :param v1: vector 1
        :param v2: vector 2
        :return: distance between v1 and v2
        """
        v1_split = split_search_vector(v1)
        v2_split = split_search_vector(v2)

        distance_functions = [
            # material
            distance.jaccard,  # [0,1], 0 is the same, 1 is max distance
            # tolerance
            distance.jaccard,
            # surface
            surface_distance,
            # gdt
            cosine_distance_no_nans,  # [0,1], 0 is the same, 1 is max distance
            # norms
            distance.jaccard,
            # outer dim
            dimension_distance,
            # clip embedding
            cosine_distance_no_nans,
        ]

        if not len(v1_split) == len(v2_split) == len(distance_functions) == len(self.weights):
            raise Exception("weights should be of same length as vector sections")

        distances = []
        for distance_function, v1_part_vector, v2_part_vector, weight in zip(
            distance_functions, v1_split, v2_split, self.weights, strict=True
        ):
            distances.append(distance_function(v1_part_vector, v2_part_vector) * weight)

        return sum(distances)


def split_search_vector(search_vector):
    """
    Splits the search vector into its components:
    Material: length 116
    Tolerance: length 7
    Surface: length 1
    GDTs: length 12
    Norms: length 52
    Outer Measures: length 3
    Clip embeddings: length 512

    and returns a list of those vectors.
    """
    # lengths of the sections of the vectors
    mat_length = 116
    tol_length = 7
    n_grade_length = 1
    gdt_length = 12
    norm_length = 52
    outer_measure_length = 3
    clip_length = 512
    section_lengths = [
        mat_length,
        tol_length,
        n_grade_length,
        gdt_length,
        norm_length,
        outer_measure_length,
        clip_length,
    ]

    # iterate over the section, split them into separate vectors
    current_pointer = 0
    split_search_vector = []
    for length in section_lengths:
        split_search_vector.append(search_vector[current_pointer : current_pointer + length])
        current_pointer += length
    return split_search_vector


def standardize_and_compute_l2_dist(v1, v2, means, stds):
    """
    Standardizes the vectors v1 and v2 using the means and standard deviations (z score).
    Afterward, computes Euclidean distances between the normalized vectors.
    The distance is devided by the length of the vector.
    :param v1: vector 1
    :param v2: vector 2
    :param means: z score mean
    :param stds: z score standard deviation
    :return: euclidian distance between v1 and v2
    """
    # convert to numpy arrays
    v1 = np.array(v1)
    v2 = np.array(v2)
    means = np.array(means)
    stds = np.array(stds)

    # compute z score standardization
    v1_std = (v1 - means) / stds
    v2_std = (v2 - means) / stds

    # Euclidian distance
    return distance.euclidean(v1_std, v2_std) / len(v1)


def surface_distance(v1, v2):
    """
    Computes the surface distance between two vectors.
    Runs standardize_and_compute_l2_dist with the mean and stds of the surface vector
    """
    means = [7.047478619876142]
    stds = [0.92944175211206]
    return standardize_and_compute_l2_dist(v1, v2, means, stds)


def dimension_distance(v1, v2):
    """
    Computes the best euclidean distance between two vectors by permutating the first one and computing the euclidean
    distance (normalized by vector length).
    :param v1: vector 1
    :param v2: vector 2
    :return: distance of the outer dimensions described in v1 and v2
    """
    # means and standard deviation for dimensions
    means = [41.90041286, 133.08905338, 0]
    stds = [88.95143844, 232.11359118, 1.0]

    # get all permutations of v1
    permutations = list(itertools.permutations(v1))
    best_distance = 1.0
    # use euclidian distance to compute the best permutation for the dimensions
    for perm in permutations:
        dist = standardize_and_compute_l2_dist(perm, v2, means, stds)
        if dist < best_distance:
            best_distance = dist

    return best_distance


def cosine_distance_no_nans(v1, v2):
    if sum(v1) == 0 or sum(v2) == 1.0:
        return 0
    else:
        return distance.cosine(v1, v2)
