"""
CS12300 Spring 2018
TBD
Tyler Amos, Ishaan Bhojwani, Kevin Sun, Alexander Tyan

Utility functions for algorithm 2 (alg_2.py).
"""

import numpy as np
from skimage.filter import threshold_minimum

from astro_object import AstroObject


def build_adjacency_matrix(astr_list):
    """
    Build a matrix of probabilities for random walk. Each value at
    location i, j is a probability of moving from i'th object to j'th
    object.
    :param astro_list: list of astro objects
    :return norm_trans_matrix: numpy matrix with each row i representing
        the probability of a jump from object i to j.
    """
    # If the list has 0 or 1 object, no travel possible between objects
    if len(astr_list) <= 1:
        return None

    # create empty adjacency matrix
    dimension = len(astr_list)
    adjacency_matrix = np.zeros((dimension, dimension))

    # Popualate matrix with distances between objects
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

    # Prep matrix for normalization (make higher dist -> lower number)
    trans_matrix = transform_dist_matrix(adjacency_matrix)

    # fill the diagonal with zeroes (so 0 prob of jumping to itself)
    np.fill_diagonal(trans_matrix, val=0)

    # normalize the transformed matrix across rows
    norm_trans_matrix = row_normalize_matrix(trans_matrix)

    return norm_trans_matrix


def transform_dist_matrix(dist_adj_mat):
    """
    Transforms a matrix of distances. Each distance is transformed with
    function transform_distance.
    :param dist_adj_mat: numpy array, matrix of distances between
        objects
    :return func(dist_adj_mat): numpy array, matrix of transformed
        distances
    """
    func = np.vectorize(transform_distance)
    return func(dist_adj_mat)


def transform_distance(distance):
    """
    Transform distance into a measure that turns larger distances into
    lower probabilities.
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
    Jumps randomly between astronomical objects. Probability that jump
    is made is dependent on probs in prob_mat, and is inversely
    proportional to distance between the objects. Keeps track of each
    objects visitation count. Higher visit counts signify an object
    with many objects around it (aka a good cluster candidate).
    NOTE: This is the most comp intense thing we do. Find a better way?
    Reference for function:
    https://medium.com/@sddkal/random-walks-on-adjacency-matrices-a127446a6777

    :param prob_mat: numpy array, probabilities of visting other points
    :param iterations: int, number of random walks to perform
    :param subiter: int number of jumps to perform each random walk
    :param astr_list: list of astro objects
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


def create_bin(ra1, ra2, dec1, dec2, n_ra, n_dec):
    """
    Create equally spaced bins for ra and dec coordinate ranges.
    :ra1, ra2, dec1, dec2: floats, bounds within to make bins
    :param n_ra: integer, how many bins for ra
    :param n_dec: integer, how many bins for dec
    :return ra_bins, dec_bins: tuple of 2 arrays with bin boundaries
    """

    # "+1" Because the bins are in between numbers, so (number of bins)
    # is (number of boundaries - 1)
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


def apply_threshold(bounds, random_walk, num_bins, subdivs):
    '''
    Partitions the sky into several cells and counts the total number
    of visitations to each cell (sum of all astr.rand_walk_visits). Then
    attempts to calcualte a threshold for which any cell with a greater
    number of total visitations is a cluster candidate (high visitation
    counts -> dense distribution of objects). Then applies the threshold
    and returns any objects within the dense cells.
    NOTE: why not use stdev to find higher density than normal bins,
    rather than threshold? Might be faster.
    Inputs:
        bounds: tuple of 2 ints. RA/Dec bins for the astro objects
        random_walk: a list of AstroObjects post random walk.
    Yields: AstroObjects within dense cells.
    '''
    if not random_walk:
        return None

    MIN_RA = 0  # Min ra possible
    MIN_DEC = -90  # Min dec possible
    RA_RANGE = 360  # range of ra values
    DEC_RANGE = 180  # range of dec values

    # Calculate actual bounds of ra/dec values for the AstroObjects
    # coming in, based on the 'bounds' identifier being passed in.
    ra_l = (RA_RANGE / num_bins) * bounds[0] + MIN_RA
    dec_l = (DEC_RANGE / num_bins) * bounds[1] + MIN_DEC
    ra_u = (RA_RANGE / num_bins) * (bounds[0] + 1) + MIN_RA
    dec_u = (DEC_RANGE / num_bins) * (bounds[1] + 1) + MIN_DEC

    # Using the above calculates, partition the objects based on ra/dec
    ra_bins, dec_bins = create_bin(ra_l, ra_u, dec_l, dec_u, subdivs, subdivs)

    # Build matrix of visit counts. Each cell is total counts for all
    # objects within that ra/dec bin.
    prob_mtrx = np.zeros((len(ra_bins) - 1, len(dec_bins) - 1))
    for astr in random_walk:
        ra_bin, dec_bin = sort_bins(astr.ra, astr.dec, ra_bins, dec_bins)
        prob_mtrx[ra_bin][dec_bin] += astr.rand_walk_visits
        astr.bin_id = [ra_bin, dec_bin]

    # Attempt to threshold and filter.
    try:
        thresh = threshold_minimum(prob_mtrx)
        clusters = (prob_mtrx >= thresh) * prob_mtrx
        clusters_idx = np.transpose(np.nonzero(clusters))

    except:
        return None

    # Check each object to see if its in a dense cell. If so, yield.
    # NOTE: Could this be done a more efficient way?
    for astr in random_walk:
        if astr.bin_id in clusters_idx:
            yield None, astr
