# This file implements the random walk process

import astro_object
from mrjob.job import MRJob
import csv


def read_csv_line(line):
	"""
	This function returns each individual row from a csv file
	"""
	for row in csv.reader([line]):
		return row

