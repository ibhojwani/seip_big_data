'''
'''


from numpy import linspace, histogram2d
from itertools import product
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
    ra_bins = linspace(ra1, ra2, num_bins, endpoint=False)
    dec_bins = linspace(dec1, dec2, num_bins, endpoint=False)

    ra_list = []
    dec_list = []
    weights = []

    for obj, prob in random_walk.items():
        ra_list.append(obj.ra)
        dec_list.append(obj.dec)
        weights.append(prob)

    hist = histogram2d(ra_list, dec_list, bins=[
                       ra_bins, dec_bins], weights=weights)

    try_all_threshold(hist)
    plt.show()
