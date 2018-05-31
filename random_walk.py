import csv
from astro_object import AstroObject
import numpy as np
import pandas as pd
from itertools import combinations
from group_objects import MrBoxAstroObjects
from skimage.segmentation import random_walker

# initialize MRJob
mr_job = MrBoxAstroObjects(args=['-r', 'local', '5218587.csv'])
with mr_job.make_runner() as runner:
    runner.run()
for line in runner.stream_output():
    key, value = mr_job.parse_output_line(line)

def build_adjacency_matrix(astro_list):
    """

    :param key:
    :param value:
    :return:
    """
    # create empty adjacency matrix
    dimension = len(astro_list)
    adjacency_matrix = np.zeros((dimension, dimension))

    for one_ind in range(len(astro_list)):
        astro_1 = astro_list[one_ind]
        for two_ind in range(one_ind + 1, len(astro_list)):
            astro_2 = astro_list[two_ind]
            # right ascension
            a = (astro_1.ra - astro_2.ra) ** 2
            # declination
            b = (astro_1.dec - astro_2.dec) ** 2
            # proper motion right ascension
            c = (astro_1.ra_motion - astro_2.ra_motion) ** 2
            # proper motion declination
            d = (astro_1.dec_motion - astro_2.dec_motion) ** 2

            # Calculate the Euclidean Distance
            euclid_dist = np.sqrt(sum([a, b, c, d]))

            # fill adjacency matrix
            adjacency_matrix[one_ind][two_ind] = euclid_dist
            # adjacency_matrix[two_ind][one_ind] = euclid_dist

            return adjacency_matrix

def get_pairings(key, value):
    """
    This function creates pairings of astro_objects within a
    single boundary box.
    """
    comb_list = []
    comb = combinations(value, 2)
    for i in comb:
        comb_list.append(i)

    return comb_list


def fill_adjacency_matrix(astro_object_tuple):
    """
	"""


    # get list of combinations
    combination_list = get_pairings(astro_object_tuple)

    # initialize a dataframe to store Euclidean Distances
    index = list(astro_object_tuple)


    columns = list(astro_object_tuple)
    df = pd.DataFrame(index=index, columns=columns)

    # iterate through list of combinations
    for pair in combination_list:
        astro_1 = pair[0]
    astro_2 = pair[1]




    # Fill in Dataframe
    df.set_value("astro_1", "astro_2", euclid_dist)
    df.fillna(value=0, inplace=True)

    # cast to numpy array
    adjacency_matrix = df.values

    return adjacency_matrix

# l = [1,2,3,4,56,7,8,9]
# get_indices(l)