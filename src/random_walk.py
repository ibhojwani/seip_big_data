from astro_object import AstroObject
import numpy as np
from group_objects import MrBoxAstroObjects
import copy


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


def random_walk(prob_mat, start_row, iterations, astro_objects_list):
    """
    Reference for function: https://medium.com/@sddkal/random-walks-on-adjacency-matrices-a127446a6777

    Input:
        - prob_mat: numpy array, probabilities of visting other points
        - start_row: int, which row/point to start at
        - iterations: int, number of iterations to do random walk
    """
    if type(prob_mat).__module__ == 'numpy':
        #create empty matrix to store random walk results
        dimension = len(prob_mat)
        random_walk_matrix = np.zeros((dimension, dimension))

        # create array of possible outcomes
        possible_outcomes = np.arange(prob_mat.shape[0])

        # begin at pre-defined row
        curr_index = start_row

        # Copy astro object list:
        astro_objects_list_copy = copy.deepcopy(astro_objects_list)

        # begin random walk
        for k in range(iterations):
            probs = prob_mat[curr_index]  # probability of transitions

            # sample from probs
            new_spot_index = np.random.choice(possible_outcomes, p=probs)

            # increment counts in the astro object attribute
            astro_objects_list_copy[new_spot_index].rand_walk_visits += 1

            # make the new spot index the current index
            curr_index = new_spot_index

        return astro_objects_list_copy
    return None






