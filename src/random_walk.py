import csv
from astro_object import AstroObject
import numpy as np
import pandas as pd
from itertools import combinations
from group_objects import MrBoxAstroObjects
from skimage.segmentation import random_walker


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
            dist = astro_1.euclid_dist(astro_2)

            # fill adjacency matrix (only fill one side?)
            adjacency_matrix[one_ind][two_ind] = dist
            adjacency_matrix[two_ind][one_ind] = dist

    return adjacency_matrix


# initialize MRJob
mr_job = MrBoxAstroObjects(args=['-r', 'local', '5218587.csv'])
with mr_job.make_runner() as runner:
    runner.run()
    for line in runner.stream_output():
        key, value = mr_job.parse_output_line(line)
        matrix = build_adjacency_matrix(value)
        print(matrix)
