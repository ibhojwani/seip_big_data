"""
CS12300 Spring 2018
TBD
Tyler Amos, Ishaan Bhojwani, Kevin Sun, Alexander Tyan

Algorithm II implemenation for finding Young Stellar Objects (YSOs) in
the ALLWISE catalog.

Partitions all objects into a given number of bins based on proximity.
Uses a random walk algorithm to calculate densities of astronomical
objects in each bin, and then a thresholding algorithm which filters out
low denisty areas. Then passes all objects in high density areas to a
kmeans algorithm which finds the 2 color centroids. Any object further
than a certain number of stdev's from its color centroid is considered
an outlier. Then returns those objects.
"""

from mrjob.job import MRJob
from mrjob.step import MRStep
from mrjob.protocol import TextValueProtocol
import numpy as np

import astro_object
import alg_2_util
from kmeans import KMeansMR
from stdev import StdevMR


class Algorithm2MR(KMeansMR, StdevMR):
    """
    MRjob object find YSO's. Sorts astro objects into bins and filters
    for clusters within each bin. Then finds color outliers.
    """

    # pass data internally with pickle, use TextValue for readable output
    OUTPUT_PROTOCOL = TextValueProtocol

    NUM_ITER = 40  # How many random walks to run
    NUM_JUMPS = 200  # How many jumps to make within each random walk
    SUBDIVS = 60  # How many ra/dec subdivs to make for thresholding
    STD_CUTOFF = 4

    def mapper_clust(self, _, line):
        '''
        MRjob mapper. Translates csv input into AstroObject and yields,
        along with location bin. 
        Inputs:
            line: str, line of csv file
        Yields:
            tuple containing ra/dec bin of object and object itself
        '''
        # Construct an astro object and push the attributes in:
        astr = astro_object.AstroObject(data_row=line)

        # yield only if there is an astro object
        if astr.is_complete():
            # sort astro object into bins based on ra and dec values
            ra_bin, dec_bin = alg_2_util.sort_bins(
                astr.ra, astr.dec, ra_bins, dec_bins)

            yield (ra_bin, dec_bin), astr

    def reducer_clust(self, bounds, astr_gen):
        '''
        MRjob reducer. Within a given bin, finds clusters of objects.
        Uses a random walk algorithm to find which objects are in close
        proximity to other objects. Those with higher visitation counts
        from the random walk will be in clusters. Then divides the bin
        into cells, and calculates a threshold using the skimage minimum
        algorithm. If the total visitation count of all objects within
        a cell is higher than the threshold, the cell is considered to
        be a cluster and all objects within are yielded.
        Inputs:
            bounds: tuple of 2 ints, signifying the ra/dec bin.
            astr_gen: generator of AstroObjects within the bin
        Yields: None and AstroObject of any object in cluster
        '''
        # random walk needs a list. The size of 'bounds' is chosen so
        # this is possible / so that there are no memory errors.
        astr_l = []
        for i in astr_gen:
            astr_l.append(i)  # bounds size is chosen so this is possible

        # Build prob matrix and complete random walk for each bin
        prob_mtrx = alg_2_util.build_adjacency_matrix(astr_l)
        rand_walk = alg_2_util.random_walk(
            prob_mtrx, self.NUM_ITER, self.NUM_JUMPS, astr_l)

        # Threshold and filter, and yield any objects which remain
        yield from alg_2_util.apply_threshold(bounds, rand_walk, NUM_BINS,
                                              self.SUBDIVS)

    def mapper_return(self, center, astr):
        '''
        Final step. Return object if it is outside a given range from
        the center of its color group. This filters for color outliers.
        Inputs:
            center: identifier for color centroid
            astr: AstroObject to yield if an outlier
        Yields: None, AstroObject
        '''
        if astr.dist_from_center > self.stdev[center] * self.STD_CUTOFF:
            try:
                yield None, astr.__repr__()
            except:
                pass

    def steps(self):
        '''
        MRjob step definition.
        '''
        clustering = [MRStep(mapper=self.mapper_clust,
                             reducer=self.reducer_clust)]

        # These steps, from the parent classes, find color outliers.
        kmeans = self.get_steps_kmeans()
        std = self.get_steps_std()

        final = [MRStep(mapper=self.mapper_return)]
        
        return clustering + kmeans + std + final


if __name__ == '__main__':
    NUM_BINS = 360  # How many bins to partition ra/dec into

    # Ranges of ra and dec
    RA_MIN = 0
    RA_MAX = 360
    DEC_MIN = -90
    DEC_MAX = 90

    # Initialize bins using full ra/dec range (0 to 360, -90 to 90)
    ra_bins, dec_bins = alg_2_util.create_bin(
        RA_MIN, RA_MAX, DEC_MIN, DEC_MAX, NUM_BINS, NUM_BINS)

    # Get those Yung Stellar Objects
    Algorithm2MR.run()
