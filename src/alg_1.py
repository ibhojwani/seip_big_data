'''
CS12300 Spring 2018
TBD
Tyler Amos, Ishaan Bhojwani, Kevin Sun, Alexander Tyan

Algorithm I implementation for finding Young Stellar Objects (YSO's) in
the ALLWISE catalog.

Color-color ratios for objects in the infrared tend to fall into 2
groups. This uses a k-means algorithm to separate the groups and find
outliers within those groups. Then, it estimates distances between
groups of outliers and draws a radius around each outlier where a
potential cluster could fall. Finally, it finds those objects with a
uniquely small radius, implying it lies in a dense region. These objects
are then returned as YSO candidates.
'''

from mrjob.job import MRJob
from mrjob.step import MRStep
from mrjob.protocol import UltraJSONValueProtocol

import alg_1_util
from kmeans import KMeansMR
from stdev import StdevMR


class Algorithm1MR(KMeansMR, StdevMR):
    '''
    MRjob object to find YSO's. Searches for color outliers and then
    searches for clusters of outliers.
    '''
    MAX_LEN = 1000  # Max number of outliers to compare to for clusters
    LEN_MULT = 0.5  # Reduction factor when MAX_LEN is reached
    TOP_K = 250  # Number of closest objects to draw radii with
    BINS = 15  # Number of bins into which we histogram the points
    STD_CUTOFF = 2.5

    OUTPUT_PROTOCOL = UltraJSONValueProtocol

    def mapper_clust_init(self):
        '''
        MRjob mapper init.
        '''
        self.list_len = 0
        self.node_list = []

    def mapper_clust(self, center, astr):
        '''
        Mrjob mapper. For a given AstroObject, yields distance from
        object to each of a subset of objects in the sky.
        Also filters for color outliers.
        Inputs:
            center: color centroid. Used to judge color outlier status.
            astr: AstroObject
        Yields: AstroObject and distance from one other object
        '''
        if astr.dist_from_center > self.stdev[center] * self.STD_CUTOFF:
            yield from alg_1_util.map_clust(astr, self.MAX_LEN, self.LEN_MULT,
                                            self.node_list)

    def combiner_clust(self, astr, dist_gen):
        '''
        For a given AstroObject, yield a radius in which a cluster would
        lie, if one exists. NOTE: this is not in a reducer because a
        given AstroObject is only seen by one node during the mapper.
        Inputs:
            astr: AstroObject to draw radius around
            dist_gen: generator of distances to other nearby outliers
        Yields: 1 (junk key) and AstroObject w/ radius as attribute
        '''
        yield from alg_1_util.comb_clust(astr, dist_gen, self.TOP_K, self.BINS)

    def mapper_return(self, junk, astr):
        '''
        Filters for AstroObjects with very small cluster radii.
        Inputs:
            junk: int, but not used
            astr: AstroObject
        Yields: junk, AstroObject
        '''
        if astr.dist_from_center < self.stdev[junk] / self.STD_CUTOFF:
            yield junk, astr

    def steps(self):
        # Find color outliers
        kmeans = self.get_steps_kmeans()
        stdev = self.get_steps_std()

        # Filter outliers, and cluster them together
        cluster = [MRStep(mapper_init=self.mapper_clust_init,
                          mapper=self.mapper_clust,
                          combiner=self.combiner_clust)]

        # Repeat stdev filtering on radius of clusters, and then return
        # objects which have a very small radius
        final = [MRStep(mapper=self.mapper_return)]

        return kmeans + stdev + cluster + stdev + final


if __name__ == '__main__':
    Algorithm1MR.run()
