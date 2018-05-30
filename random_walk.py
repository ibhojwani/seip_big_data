import csv
from astro_object import AstroObject
import numpy as np 
import pandas as pd
from itertools import combinations
from skimage.segmentation import random_walker


def get_pairings(astro_object_tuple):
	"""
	This function creates tuples of pairings.
	"""
	astro_list = list(astro_object_tuple)
	comb_list = []
	comb = combinations(astro_list, 2)
	for i in comb:
		comb_list.append(i)

	return comb_list


def fill_adjacency_matrix(astro_object_tuple):
	"""
	"""
	# create empty adjacency matrix
	dimension = len(astro_object_tuple)
	adjacency_matrix = np.zeros((dimension, dimension))

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
		# right ascension
		a = (astro_1.ra - astro_2.ra)**2
		# declination
		b = (astro_1.dec - astro_2.dec)**2
		# proper motion right ascension
		c = (astro_1.ra_motion - astro_2.ra_motion)**2
		# proper motion declination
		d = (astro_1.dec_motion - astro_2.dec_motion)**2

		# Calculate the Euclidean Distance
		euclid_dist = sqrt(sum([a, b, c, d]))

		# Fill in Dataframe
		df.set_value("astro_1", "astro_2", euclid_dist)
		df.fillna(value=0, inplace=True)

		# cast to numpy array
		adjacency_matrix = df.values

	return adjacency_matrix













