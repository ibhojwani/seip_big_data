'''
'''
from numpy import histogram2d, zeros
import astro_object
from group_objects import create_bins, sort_bins
from skimage.filters import try_all_threshold
from matplotlib import pyplot as plt


def watershed(random_walk, num_bins, ra1, ra2, dec1, dec2):
    '''
    Inputs:
        random_walk: a counter containing the visitation counts of a
            random walk algorithm, containing the AstroObjects and their
            visitation counts
    Returns: nested list containing lists of AstroObjects in a given
        cluster
    '''
    NUM_BINS = 45

    ra_bins, dec_bins = create_bins(
        num_ra_bins=NUM_BINS, num_dec_bins=NUM_BINS)

    prob_mtrx = zeros(len(ra_bins) - 1, len(dec_bins) - 1)

    for obj, prob in random_walk.items():
        ra_bin, dec_bin = sort_bins(obj.ra, obj.dec, ra_bins, dec_bins)
        prob_mtrx[ra_bin][dec_bin] += prob
        obj.bin_id = (ra_bin, dec_bin)

    try_all_threshold(prob_mtrx)
    plt.show()
