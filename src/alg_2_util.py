"""
Functions for Random Walks. Used in group_objects.py MRJob implementation.
"""
import numpy as np
import copy  # For deep copying a list of Astro Objects
from skimage.filters import try_all_threshold
import skimage.filters
from matplotlib import pyplot as plt
from time import sleep
from math import inf

import astro_object
from astro_object import AstroObject


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
    transformed_dist = 1 / (1 + distance**1.5)

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


def random_walk(prob_mat, iterations, subiter, astr_l):
    """
    Reference for function:
    https://medium.com/@sddkal/random-walks-on-adjacency-matrices-a127446a6777

    :param prob_mat: numpy array, probabilities of visting other points
    :param start_row: int, which row/point to start at
    :param iterations: int, number of iterations to do random walk
    :param astro_objects_list: list of astro objects
    :return astr_l or None: list of astro objects, with
    visitation counts updated (None if bad probability matrix input)
    """
    # Check that probability matrix is a numpy array. It shouldn't be if
    # there were no objects between which to compare distances:
    if type(prob_mat).__module__ != 'numpy':
        return None
    # create array of possible outcomes
    possible_outcomes = np.arange(prob_mat.shape[0])
    # begin at pre-defined row

    # begin random walk
    for i in range(iterations):
        cur_index = np.random.choice(possible_outcomes)
        for j in range(subiter):
            probs = prob_mat[cur_index]  # probability of transitions

            # sample from probs
            cur_index = np.random.choice(possible_outcomes, p=probs)

            # increment counts in the astro object attribute
            astr_l[cur_index].rand_walk_visits += 1

    return astr_l


def create_bin(ra1, ra2, dec1, dec2, n_ra=360, n_dec=360):
    """
    Create equally spaced bins for ra and dec coordinate ranges
    :param n_ra: integer, how many bins for ra
    :param n_dec: integer, how many bins for dec
    :ra1, ra2, dec1, dec2: floats, bounds within to make bins
    :return ra_bins, dec_bins: tuple of numpy arrays with bin boundaries
    """

    # "+1" Because the bins are in between numbers, so (number of bins) is
    # (number of boundaries - 1)
    ra_bins = np.linspace(start=ra1, stop=ra2, num=n_ra + 1)
    dec_bins = np.linspace(start=dec1, stop=dec2, num=n_dec + 1)

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

    return ra_bin - 1, dec_bin - 1  # -1 due to how digitize bins


def apply_threshold(bounds, random_walk, num_bins):
    '''
    Inputs:
        random_walk: a counter containing the visitation counts of a
            random walk algorithm, containing the AstroObjects and their
            visitation counts
    Returns: nested list containing lists of AstroObjects in a given
        cluster
    '''
    if not random_walk:
        return None

    MIN_RA = 0
    MIN_DEC = -90
    RA_RANGE = 360
    DEC_RANGE = 180

    ra_l = (RA_RANGE / num_bins) * bounds[0] + MIN_RA
    dec_l = (DEC_RANGE / num_bins) * bounds[1] + MIN_DEC
    ra_u = (RA_RANGE / num_bins) * (bounds[0] + 1) + MIN_RA
    dec_u = (DEC_RANGE / num_bins) * (bounds[1] + 1) + MIN_DEC

    ra_bins, dec_bins = create_bin(
        ra_l, ra_u, dec_l, dec_u, n_ra=10, n_dec=10)
    lowest_ra = inf
    lowest_dec = inf
    for i in random_walk:
        if i.ra < lowest_ra:
            lowest_ra = i.ra
        if i.dec < lowest_dec:
            lowest_dec = i.dec

    prob_mtrx = np.zeros((len(ra_bins) - 1, len(dec_bins) - 1))

    for astr in random_walk:
        ra_bin, dec_bin = sort_bins(astr.ra, astr.dec, ra_bins, dec_bins)
        prob_mtrx[ra_bin][dec_bin] += astr.rand_walk_visits
        astr.bin_id = [ra_bin, dec_bin]

    try:
        thresh = skimage.filters.threshold_minimum(prob_mtrx)
        clusters = (prob_mtrx >= thresh) * prob_mtrx
        clusters_idx = np.transpose(np.nonzero(clusters))

    except:
        return None

    for astr in random_walk:
        if astr.bin_id in clusters_idx:
            yield None, astr
