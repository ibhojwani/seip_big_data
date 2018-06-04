'''
CS123 Spring 2018
TBD
Ishaan Bhojwani, Tyler Amos, Kevin Sun, Alexander Tyan

This file provides an MRjob job to take a collection of astronomical
objects as either csv of AstroObject generator input and find centroids
of their color distribution. From preliminary analysis, there exist 2
centroids for these color groups, around which color is approx normally
distributed. Finding these centroids allows for color outlier analysis.
'''

from mrjob.job import MRJob
from mrjob.step import MRStep
from mrjob.protocol import PickleProtocol

from astro_object import AstroObject


class KMeansMR(MRJob):
    '''
    MRjob object to find color outliers.
    '''

    INTERNAL_PROTOCOL = PickleProtocol

    # num kmeans iterations. We set good initial vals so dont need many
    ITERATIONS = 15  
    STD_CUTOFF = 3.5

    centroids = [(0, 0), (0.6, 4)]  # Approx location of centroids
    centroids_old = centroids.copy()
    stdev = {}
    means = {}

    def mapper_kmeans(self, _, line):
        '''
        Calculate which centroid each object is closest to w/ squared
        eculidian distance, and yield the object coords and centroid.
        Yields:
            centroid: int, index in centroids list of centroid closest
            values: AstroObject

        Note: we are choosing to keep distance from center as an attr
        in AstroObject as opposed to recalculating it every time.
        Because it is needed in multiple places, we think this tradeoff
        is worth it. We may be wrong.
        '''
        centroid, values = map_kmeans(self.centroids, line)
        if values != centroid != None:
            yield centroid, values

    def reducer_kmeans_init(self):
        self.sums = {}

    def reducer_kmeans(self, center, astr_gen):
        # NOTE: USE YIELD FROM?
        # get new centroids by averaging the locations of current groups
        counter = 0
        color1_sum = 0
        color2_sum = 0
        for astr in astr_gen:
            counter += 1
            color1_sum += astr.color1
            color2_sum += astr.color2
            yield center, astr

            # Assign new centroids and compare to old. If they converge
            # then skip rest of steps
        self.centroids[center] = (round(color1_sum / counter, 5),
                                  round(color2_sum / counter, 5))

    def get_steps_kmeans(self):
        return [MRStep(mapper=self.mapper_kmeans,
                       reducer_init=self.reducer_kmeans_init,
                       reducer=self.reducer_kmeans)] * self.ITERATIONS

    def steps(self):
        return self.get_steps_kmeans()


def map_kmeans(centroids, astr):
    if isinstance(astr, str):
        # Parses fresh input from file. Else, assumed to be AstroObject.
        astr = AstroObject(data_row=astr)

    if type(astr) != AstroObject:
        return None, None

    # Calc closest centroid, yield that centroid and obj colors
    if astr.is_complete():
        center_idx = None
        closest = float('inf')
        for i, center in enumerate(centroids):
            dist = astr.sq_euc_2d(
                astr.color1, astr.color2, center[0], center[1])
            if dist < closest:
                closest = dist
                center_idx = i

        astr.dist_from_center = closest
        # Package relevant info as a hashable type to yield
        # Yield centroid id, astro object, and distance to center
        return center_idx, astr

    return None, None
