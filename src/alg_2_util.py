"""
Functions for Random Walks. Used in group_objects.py MRJob implementation.
"""
from astro_object import AstroObject
import numpy as np
import copy  # For deep copying a list of Astro Objects


def recast_astro_objects(astro_list):
    """
    Take a list of dictionaries with astro objects info and convert to
    a list of astro objects
    :param astro_list: list of dictionaries
    :return l: list of astro objects, with attributes filled in.
    """
    l = []
    for astro_dict in astro_list:
        astro_object = AstroObject()  # instantiate astro object
        astro_object.from_dict(astro_dict)  # cast back into astro object
        l.append(astro_object)

    return l


def build_adjacency_matrix(astr_list):
    """
    Build a matrix of probabilities for random walk. Each value at location
    i, j is a probability of moving from i'th object to j'th object and
    vice-versa
    :param astro_list: list of astro objects
    :return norm_trans_matrix: numpy array, probability matrix, with rows adding
    to 1
    """
    # If the list has 0 or 1 object, no travel between objects is possible:
    if len(astr_list) <= 1:
        return None

    # create empty adjacency matrix
    dimension = len(astr_list)
    adjacency_matrix = np.zeros((dimension, dimension))

    for one_ind in range(len(astr_list)):
        astr_1 = astr_list[one_ind]

        if astr_1.is_complete():
            for two_ind in range(one_ind + 1, len(astr_list)):
                astr_2 = astr_list[two_ind]

                if astr_2.is_complete:
                    # fill adjacency matrix
                    dist = astr_1.euc_dist_4d(astr_2)
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
    Helper function, transforms a matrix of distances to a matrix of trans-
    formed distances. Each distance is transformed with function transform_distance
    :param dist_adj_mat: numpy array, matrix of distances between objects
    :return func(dist_adj_mat): numpy array, matrix of transformed distances
    """
    func = np.vectorize(transform_distance)
    return func(dist_adj_mat)


def transform_distance(distance):
    """
    Transform a distance into a measure that recallibrates the distance to
    give higher values to closer objects
    :param distance: float
    :return transformed_dist: float
    """
    transformed_dist = 1 / (1 + distance)

    return transformed_dist


def row_normalize_matrix(transformed_matrix):
    """
    Normalize values in a matrix across rows; i.e. rows add to one
    :param transformed_matrix: numpy array, matrix of values to normalize
    :return normalized_matrix: numpy array, normalized matrix
    """
    row_sums = transformed_matrix.sum(axis=1)  # Across rows normalization
    normalized_matrix = transformed_matrix / row_sums[:, np.newaxis]

    return normalized_matrix


def random_walk(prob_mat, start_row, iterations, astro_objects_list):
    """
    Reference for function:
    https://medium.com/@sddkal/random-walks-on-adjacency-matrices-a127446a6777

    :param prob_mat: numpy array, probabilities of visting other points
    :param start_row: int, which row/point to start at
    :param iterations: int, number of iterations to do random walk
    :param astro_objects_list: list of astro objects
    :return astro_objects_list_copy or None: list of astro objects, with
    visitation counts updated (None if bad probability matrix input)
    """
    # Check that probability matrix is a numpy array. It shouldn't be if
    # there were no objects between which to compare distances:
    if type(prob_mat).__module__ == 'numpy':

        # create array of possible outcomes
        possible_outcomes = np.arange(prob_mat.shape[0])

        # begin at pre-defined row
        curr_index = start_row

        # Deepcopy astro object list:
        astro_objects_list_copy = copy.deepcopy(astro_objects_list)

        # create empty matrix to store random walk results
        dimension = len(prob_mat)
        random_walk_matrix = np.zeros((dimension, dimension))

        # begin random walk
        for k in range(iterations):
            probs = prob_mat[curr_index]  # probability of transitions

            # sample from probs
            new_spot_index = np.random.choice(possible_outcomes, p=probs)

            # increment counts in the astro object attribute
            astro_objects_list_copy[new_spot_index].rand_walk_visits += 1

            random_walk_matrix[curr_index][new_spot_index] += 1
            random_walk_matrix[new_spot_index][curr_index] += 1

            # make the new spot index the current index
            curr_index = new_spot_index
        return astro_objects_list_copy
    return None


def create_bins(num_ra_bins=360, num_dec_bins=360):
    """
    Create equally spaced bins for ra and dec coordinate ranges
    :param num_ra_bins: integer, how many bins for ra
    :param num_dec_bins: integer, how many bins for dec
    :return ra_bins, dec_bins: tuple of numpy arrays with bin boundaries
    """
    RA_MIN = 0
    RA_MAX = 360
    DEC_MIN = -90
    DEC_MAX = 90
    num_ra_bins = num_ra_bins
    num_dec_bins = num_dec_bins

    # "+1" Because the bins are in between numbers, so (number of bins) is
    # (number of boundaries - 1)
    ra_bins = np.linspace(start=RA_MIN, stop=RA_MAX,
                          num=num_ra_bins + 1)
    dec_bins = np.linspace(start=DEC_MIN, stop=DEC_MAX,
                           num=num_dec_bins + 1)

    return ra_bins, dec_bins


def sort_bins(ra, dec, ra_bins, dec_bins):
    """
    Sorts an astro object in a specific bin based on that astro object's
    right ascension and declination values.
    :param ra: float, right ascension
    :param dec: float, declination
    :param ra_bins: float
    :param dec_bins: float
    :return ra_bin, dec_bin: floats
    """
    ra_bin = int(np.digitize([ra], ra_bins)[0])
    dec_bin = int(np.digitize([dec], dec_bins)[0])

    return ra_bin - 1, dec_bin - 1
