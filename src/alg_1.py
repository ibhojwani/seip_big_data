
import alg_1_util
from astro_object import AstroObject

from mrjob.job import MRJob
from mrjob.step import MRStep
from mrjob.protocol import RawValueProtocol

from math import inf, sqrt
from numpy import sqrt, histogram
from numpy.random import randint

from heapq import heappush, heappop


class MRTask1(MRJob):
    OUTPUT_PROTOCOL = RawValueProtocol

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
        centroid, values = alg_1_util.map_kmeans(line, centroids)
        if values != centroid != None:
            yield centroid, values

    def reducer_kmeans_init(self):
        self.counter = 0
        self.sums = {}

    def reducer_kmeans(self, center, values):
        # NOTE: USE YIELD FROM?
        # get new centroids by averaging the locations of current groups
        counter = 0
        color1_sum = 0
        color2_sum = 0
        for item in values:
            self.counter += 1
            counter += 1
            color1_sum += item['color1']
            color2_sum += item['color2']
            yield center, item

            # Assign new centroids and compare to old. If they converge
            # then skip rest of steps
        centroids[center] = (round(color1_sum / counter, 5),
                             round(color2_sum / counter, 5))
        print(centroids[center], self.counter)

    def reducer_std_mean(self, center, values):
        # NOTE: USE YIELD FROM?
        total = 0
        count = 0

        for item in values:
            total += item['dist_from_center']
            count += 1
            yield center, item

        means[str(center)] = total / count

    def mapper_std_diff(self, center, values):
        '''
        Yields center, object, and difference between mean and distance
        '''
        mean = means[str(center)]
        yield center, (values, values['dist_from_center'] - mean)

    def reducer_std_diff_init(self):
        self.count = 0

    def reducer_std_diff(self, center, values):
        # NOTE: USE YIELD FROM?
        str_center = str(center)
        stdev[str_center] = 0
        for item in values:
            stdev[str_center] += item[1]**2
            self.count += 1
            yield center, item[0]

        # Get final stdev
        stdev[str_center] = sqrt(stdev[str_center] / self.count)

    def mapper_clust_init(self):
        self.list_len = 0
        self.node_list = []

    def mapper_clust(self, center, values):
        mod_std = stdev[str(center)] * std_cutoff
        yield from alg_1_util.map_clust(values, mod_std, max_len, len_mult,
                                        self.node_list)

    def combiner_clust(self, astr, values):
        yield from alg_1_util.comb_clust(astr, values, TOP_K, BINS)

    def reducer_clust(self, _, astr_gen):
        for astr in astr_gen:
            yield _, astr

    def mapper_return(self, junk, astr):
        if astr['dist_from_center'] < stdev[str(junk)] / std_cutoff:
            yield junk, astr

    def reducer_return(self, junk, astr_gen):
        for astr in astr_gen:
            yield None, astr['objid']

    def steps(self):
        k_means = [MRStep(mapper=self.mapper_kmeans,
                          reducer_init=self.reducer_kmeans_init,
                          reducer=self.reducer_kmeans)] * iterations

        std = [MRStep(reducer=self.reducer_std_mean),
               MRStep(mapper=self.mapper_std_diff,
                      reducer_init=self.reducer_std_diff_init,
                      reducer=self.reducer_std_diff)]

        cluster = [MRStep(mapper_init=self.mapper_clust_init,
                          mapper=self.mapper_clust,
                          combiner=self.combiner_clust,
                          reducer=self.reducer_clust)]

        final = [MRStep(mapper=self.mapper_return,
                        reducer=self.reducer_return)]

        return k_means + std + cluster + std + final


if __name__ == '__main__':
    iterations = 1
    centroids = [(0, 0), (0.6, 4)]  # Approx location of centroids
    centroids_old = centroids.copy()
    std_cutoff = 3.5
    stdev = {}
    means = {}

    max_len = 1000  # num. values to keep for comparing,
    len_mult = 0.5  # factor by which to divide N
    # think of P as the inverse proportion we keep when the list
    # gets full, i.e., 0.25 -> 75% dropped
    TOP_K = 250  # the number of closest values we take
    BINS = 40  # number of bins into which we histogram the points
    k = 2

    MRTask1.run()

# approx centroid coords:
# [(0.063340125883, 0.92520348118), (0.371392924109, 2.92363654725)]

    ''' This class finds a subset of edges and nodes
    where each edge is the distance between two objects
    and the node is the object itself.
    It implements the following algorithm:
    i) initialize a node container and container size variable
    ii) for each line:
        - add the node to our node list
        - increment the container size by 1
        - if the node list is too large:
           - remove nodes at random until the list is size N * P
        - if the node list is sufficently full (size N * P)
          - calculate the distance from this point to all others
          in the node list
          - yield the object's id and its distance to each point
    iii) for each object
        - sort the list of edges by distance in ascending order
        - take the TOP_K edges (the closest TOP_K)
        - create a density function of the distances from
        the object
        - fit a spline function along this density curve
        - find the first saddle point in this spline, usually
        a local minimum (derived from examining results)
        if the first saddle point is less than 1
         - return the object and its saddle point
    Interpret the saddle point as the outer boundary of objects
    of interest in the vicinity of this point.
    '''
