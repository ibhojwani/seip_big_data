import csv
from astro_object import AstroObject
import numpy as np
import pandas as pd
from itertools import combinations
from group_objects import MrBoxAstroObjects
from skimage.segmentation import random_walker
from collections import Counter

def recast_astro_objects(astro_list):
    """

    :param astro_list:
    :return:
    """
    l = []
    for astro_dict in astro_list:
        astro_object = AstroObject()  # instantiate astro object
        astro_object.from_dict(astro_dict)  # cast back into astro object
        l.append(astro_object)

    return l


def build_adjacency_matrix(astro_list):
    """
    :param key:
    :param value:
    :return:
    """
    if len(astro_list) <= 1:
        return None
    # create empty adjacency matrix
    dimension = len(astro_list)
    adjacency_matrix = np.zeros((dimension, dimension))

    for one_ind in range(len(astro_list)):
        astro_1 = astro_list[one_ind]
        for two_ind in range(one_ind + 1, len(astro_list)):
            astro_2 = astro_list[two_ind]
            dist = astro_1.euc_dist(astro_2)

            # fill adjacency matrix
            adjacency_matrix[one_ind][two_ind] = dist
            adjacency_matrix[two_ind][one_ind] = dist

    # transform distances in adjacency matrix
    trans_matrix = transform_dist_matrix(adjacency_matrix)

    # fill the diagonal with zeroes
    np.fill_diagonal(trans_matrix, val=0)


    # normalize the transformed matrix across rows
    norm_trans_matrix = row_normalize_matrix(trans_matrix)

    return norm_trans_matrix


def transform_dist_matrix(dist_adj_mat):
    """

    :param dist_adj_mat:
    :return:
    """
    func = np.vectorize(transform_distance)

    return func(dist_adj_mat)


def transform_distance(distance):
    """

    :param mat_row:
    :return:
    """
    transformed_dist = 1 / (1 + distance)

    return transformed_dist


def row_normalize_matrix(transformed_matrix):
    """

    :return:
    """
    row_sums = transformed_matrix.sum(axis=1)
    normalized_matrix = transformed_matrix / row_sums[:, np.newaxis]

    return normalized_matrix


def random_walk(prob_mat, start_row, iterations, astro_list):
    """
    Reference for function: https://medium.com/@sddkal/random-walks-on-adjacency-matrices-a127446a6777

    Input:
        - prob_mat: numpy array, probabilities of visting other points
        - start_row: int, which row/point to start at
        - iterations: int, number of iterations to do random walk
    """
    #if type(prob_mat).__module__ == 'numpy':
    # create empty matrix to store random walk results
    dimension = len(prob_mat)
    random_walk_matrix = np.zeros((dimension, dimension))

    # create array of possible outcomes
    possible_outcomes = np.arange(prob_mat.shape[0])

    # begin at pre-defined row
    curr_index = start_row

    # Initialize a Counter object keep num of visitations to each
    # astro object:
    visits_counter = Counter()

    # begin random walk
    for k in range(iterations):
        probs = prob_mat[curr_index]  # probability of transitions

        # sample from probs
        new_spot_index = np.random.choice(possible_outcomes, p=probs)

        # increment counts in random_walk_matrix
        print("ASTROOJB ID:")
        print(astro_list[new_spot_index])
        #visits_counter[]
        random_walk_matrix[curr_index][new_spot_index] += 1
        random_walk_matrix[new_spot_index][curr_index] += 1

        # make the new spot index the current index
        curr_index = new_spot_index

    return random_walk_matrix
    #return None

#
# np.random.seed(15)
# # random_matrix = [np.random.randint(0, 20, (5,5))]
# # # print(random_matrix)
# # trans_mat = transform_dist_matrix(random_matrix)
# # # print( "++++++++" )
# # # print(trans_mat)
# # # print( "++++++++" )
# # normalized_mat = row_normalize_matrix(trans_mat)
# # print(normalized_mat)
# # print("++++++++++")
# # # print(normalized_mat.sum(axis=1))
# normalized_mat = build_adjacency_matrix(random_matrix)
# rw_matrix = random_walk(normalized_mat, start_row=0, iterations=100)
# print(rw_matrix)


if __name__ == "__main__":
    # initialize MRJob
    mr_job = MrBoxAstroObjects(args=['-r', 'local', '5218587.csv'])
    with mr_job.make_runner() as runner:
        runner.run()
        for line in runner.stream_output():
            key, value = mr_job.parse_output_line(line)
            l = recast_astro_objects(value)
            matrix = build_adjacency_matrix(l)
            # print("INPUT MATRIX")
            # print(matrix)
            rw_matrix = random_walk(matrix, start_row=0,
                                    iterations=100)
            # print("RANDOM WALK MATRIX:")
            # print(rw_matrix)
            # print("================================================")
            # print(matrix.sum(axis=1))
            # new_matrix = calc_matrix(matrix)
            # print(new_matrix)
            # print("+++++++++++++++++++++++")
            # print(new_matrix.sum(axis=1))
