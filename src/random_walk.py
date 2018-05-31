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
        astro_1 = AstroObject()
        astro_1 = astro_list[one_ind]
        for two_ind in range(one_ind + 1, len(astro_list)):
            astro_2 = astro_list[two_ind]
            dist = astro_1.euclid_dist(astro_2)

            # fill adjacency matrix (only fill one side?)
            adjacency_matrix[one_ind][two_ind] = dist
            adjacency_matrix[two_ind][one_ind] = dist

    return adjacency_matrix


def random_walk(adj_mat, start_row, iterations):
	"""
	Reference for function: https://medium.com/@sddkal/random-walks-on-adjacency-matrices-a127446a6777

	Input:
		- adj_mat: numpy array, probabilities of visting other points
		- start_row: int, which row/point to start at
		- iterations: int, number of iterations to do random walk
	"""

    # create empty matrix to store random walk results
    dimension = len(adj_mat)
    random_walk_matrix = np.zeros((dimension, dimension))

    # create array of possible outcomes
    possible_outcomes = np.arange(adj_mat.shape[0])

    # begin random walk
    for k in range(iterations):
    	# begin at pre-defined row 
        curr_index = start_row

        while True:
            probs = adj_mat[curr_index] # probability of transitions
            
            # sample from probs
            new_spot_index = np.random.choice(possible_outcomes,p=probs) 

            # increment counts in random_walk_matrix
            random_walk_matrix[curr_index][new_spot_index] += 1
            random_walk_matrix[new_spot_index][curr_index] += 1

            # make the new spot index the current index
            curr_index = new_spot_index
            
            # if target is our initial point then stop walking
            if new_spot_index == start_row: 
                break
            
    return random_walk_matrix


if __name__ == "__main__":
    # initialize MRJob
    mr_job = MrBoxAstroObjects(args=['-r', 'local', '../data/5218587.csv'])
    with mr_job.make_runner() as runner:
        runner.run()
        for line in runner.stream_output():
            key, value = mr_job.parse_output_line(line)
            matrix = build_adjacency_matrix(value)
            print(matrix)




















