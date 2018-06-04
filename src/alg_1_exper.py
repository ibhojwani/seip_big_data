#!/usr/bin/python

'''
CS12300 Spring 2018
TBD
Tyler Amos, Ishaan Bhojwani, Kevin Sun, Alexander Tyan

Algorithm I implementation for finding Young Stellar Objects (YSO's) in
the ALLWISE catalog.

Color-color ratios for objects in the infrared tend to fall into 2
groups. This uses a k-means algorithm to separate the groups and find
outliers within those groups.Then, it estimates distances between
groups of outliers and draws a radius around each outlier where a
potential cluster could fall. Finally, it finds those objects with a
uniquely small radius, implying it lies in a dense region. These objects
are then returned as YSO candidates.
'''


from mrjob.protocol import TextValueProtocol


from numpy.random import randint
from numpy import histogram, array
from scipy.interpolate import UnivariateSpline
from heapq import heapify



from mrjob.job import MRJob
from mrjob.protocol import PickleProtocol
from mrjob.step import MRStep
from math import sqrt


class AstroObject:
    def __init__(self, data_row=None, dic=False):
        """
        A class for an astronomical object from the ALLWISE catalog.
        Inputs:
            data_row: str, a single row of csv containing a single object
        """

        # ALLWISE catalog id
        self.objid = None
        # Positions and uncertainty
        self.ra = None
        self.dec = None
        # Motions and uncertainty
        self.ra_motion = None
        self.dec_motion = None
        # Magnitudes in different bands, with signal to noise ratio (snr)
        self.w1 = None
        self.w2 = None
        self.w3 = None
        self.w4 = None
        self.color1 = None
        self.color2 = None

        # Used in functions
        self.k_closest = []
        self.bin_id = None
        self.dist_from_center = None
        self.rand_walk_visits = 0

        # If info is provided, initialize
        if data_row:
            if dic:
                self.from_dict(data_row)
            else:
                self.fill_attributes(data_row)
        elif dic:
            raise Exception("Must provide data row if dic=True")

    def fill_attributes(self, line_list):
        if isinstance(line_list, str):
            line_list = line_list.split(",")

        try:
            self.objid = line_list[0]
            self.ra = float(line_list[1])
            self.dec = float(line_list[2])
            self.ra_motion = float(line_list[5])
            self.dec_motion = float(line_list[6])
            self.w1 = float(line_list[9])
            self.w2 = float(line_list[10])
            self.w3 = float(line_list[11])
            self.w4 = float(line_list[12])
            self.color1 = self.w1 - self.w2
            self.color2 = self.w3 - self.w4
        except:
            return False

        return True

    def package_small(self):
        to_add = ["ra", "dec", "objid", "ra_motion", "color1", "color2",
                  "dec_motion", "dist_from_center"]
        d = self.__dict__
        rv = {}
        for field in to_add:
            rv[field] = d[field]

        return rv

    @staticmethod
    def sq_euc_2d(x1, y1, x2, y2):
        '''
        Calculates squared euclid distance in 2 dimensions.
        Inputs:
            x1, y1: float, coords of object 1
            x2, y2: float, coords of object 2
        '''
        a = (x1 - x2)**2
        b = (y1 - y2)**2

        return a + b

    def euc_dist_4d(self, other):
        """
        This calculates the euclidean distance
        between two objects in 4 dimensional space (ra, dec, ra motion,
        dec motion)
        Inputs:
            other: AstroObject to comapre to.
        Outputs:
            - distance between the points (float) in degrees
        """
        MAS_TO_DEG = 1 / 3600000  # Conversion from millisecond to degree

        ra1 = self.ra
        ra2 = other.ra

        dec1 = self.dec
        dec2 = other.dec

        # Note: not using MAS_TO_DEG because this devalues direction
        pmra1 = self.ra_motion
        pmra2 = other.ra_motion

        pmdec1 = self.dec_motion
        pmdec2 = other.dec_motion

        a = (ra1 - ra2) ** 2
        b = (dec1 - dec2) ** 2
        c = (pmra1 - pmra2) ** 2
        d = (pmdec1 - pmdec2) ** 2

        return sqrt(sum([a, b, c, d]))

    def from_dict(self, d):
        for field in d.keys():
            setattr(self, field, d[field])

    def is_complete(self):
        '''
        Checks that the most important values are present. The data is not
        clean so this may not always be the case, although we try to filter for
        it in our API pull.
        '''
        to_check = ["ra", "dec", "objid", "ra_motion",
                    "dec_motion", "color1", "color2"]
        for value in to_check:
            if not self.__dict__[value]:
                return False
        return True

    def __lt__(self, other):
        if self.dist_from_center < other.dist_from_center:
            return True
        return False

    def __gt__(self, other):
        if self.dist_from_center > other.dist_from_center:
            return True
        return False

    def __repr__(self):
        if self.objid:
            rv = ""
            for field in self.__dict__.keys():
                rv += "{}:{},".format(field, self.__dict__[field])
            return rv[:-1]
        else:
            return ""


class AstroObjectBig(AstroObject):

    def __init__(self, data_row=None, dic=False):
        super().__init__(data_row, dic)

        self.ra_uncert = None
        self.dec_uncert = None
        self.ra_motion_uncert = None
        self.dec_motion_uncert = None
        self.w1_snr = None
        self.w2_snr = None
        self.w3_snr = None
        self.w4_snr = None

    def fill_attributes(self, line_list):
        """
        Fill the attributes using a CSV row
        :param data_row: string, represents a CSV row
        :return: fill attributes
        """
        if isinstance(line_list, str):
            line_list = line_list.split(",")
        if line_list[0] == "designation":
            return None
        try:
            self.objid = line_list[0]

            self.ra = float(line_list[1])
            self.dec = float(line_list[2])
            self.ra_uncert = float(line_list[3])
            self.dec_uncert = float(line_list[4])
            self.ra_motion = float(line_list[5])
            self.dec_motion = float(line_list[6])
            self.ra_motion_uncert = float(line_list[7])
            self.dec_motion_uncert = float(line_list[8])
            self.w1 = float(line_list[9])
            self.w2 = float(line_list[10])
            self.w3 = float(line_list[11])
            self.w4 = float(line_list[12])
            self.w1_snr = float(line_list[13])
            self.w2_snr = float(line_list[14])
            self.w3_snr = float(line_list[15])
            self.w4_snr = float(line_list[16])
            self.color1 = self.w1 - self.w2
            self.color2 = self.w3 - self.w4
        except:
            pass



class StdevMR(MRJob):
    '''
    MRjob object to find outliers through standard deviation.
    '''

    INTERNAL_PROTOCOL = PickleProtocol

    stdev = {}
    means = {}

    def reducer_std_mean(self, center, astr_gen):
        total = 0
        count = 0

        for astr in astr_gen:
            total += astr.dist_from_center
            count += 1
            yield center, astr

        self.means[center] = total / count

    def mapper_std_diff(self, center, astr):
        '''
        Yields center, object, and difference between mean and distance
        '''
        mean = self.means[center]
        yield center, (astr, astr.dist_from_center - mean)

    def reducer_std_diff_init(self):
        self.count = 0

    def reducer_std_diff(self, center, values):
        self.stdev[center] = 0
        for item in values:
            self.stdev[center] += item[1]**2
            self.count += 1
            yield center, item[0]

        # Get final stdev
        self.stdev[center] = sqrt(self.stdev[center] / self.count)

    def get_steps_std(self):
        return [MRStep(reducer=self.reducer_std_mean),
                MRStep(mapper=self.mapper_std_diff,
                       reducer_init=self.reducer_std_diff_init,
                       reducer=self.reducer_std_diff)]

    def steps(self):
        return self.get_steps_std()




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






def cut_list(l, max_len, mult):
    new_list = []

    for i in range(int(round(max_len * mult))):
        idx = randint(low=0, high=len(l))
        new_list.append(l[idx])

    return new_list


def map_clust(astr, max_len, len_mult, node_list):
    '''
    For a given AstroObject, yield the object and distances to a random
    collection of color outliers in the sky.
    Inputs:
        astr: AstroObject to compare
        max_len: int, max number of other outliers to store in memory
        len_mult: float in (0,1), multiplier to reduce max_len by
        node_list: list of other objects in sky to compare to,
            persistent for each mapper
    Yields: Astro object and distance to another outlier in the sky
    '''
    new_node_list = node_list
    new_node_list.append(astr)

    # If our node list is too large, toss oldest (first) values
    if len(new_node_list) > max_len:
        new_start = len(new_node_list) - round(max_len * len_mult)
        new_node_list = new_node_list[new_start:]

    # Validate that our list is still the right size
    if len(new_node_list) > max_len * len_mult:
        # Now iterate over the nodes and find distances
        for astr2 in new_node_list:
            dist = astr.euc_dist_4d(astr2)
            yield astr, dist

    node_list[:] = new_node_list


def comb_clust(astr, dist_gen, top_k, num_bins):
    '''
    Takes an AstroObject and a generator of distances from the object
    to other outliers in the sky. Returns a radius within which a
    cluster may lie, if any exist.
    Inputs:
        astr: AstroObject to analyze. Radius is put in dist_from_center
            attribute.
        dist_gen: generator of distances to a set of nearby outliers
        top_k: how many outliers to examine
        num_bins: how finely to calculate counts
    Yields: 1 (junk value), AstroObject w/ dist_from_center attribute
    '''

    heap = [val for val in dist_gen]
    if not heap:
        return None
    heapify(heap)
    cutoff = min(top_k, len(heap))  # ensure we don't have indexerrors
    heap = heap[:cutoff]
    counts, edges = histogram([i for i in heap], num_bins, density=True)
    y = array([0] + list(counts))
    x = array(list(edges))  # get distances
    # we need to give some approximate knots
    # calculate the derivates
    d1 = UnivariateSpline(x=x, y=y, k=4).derivative().roots()
    try:
        astr.dist_from_center = min(d1)
        yield 1, astr
    except:
        pass


class Algorithm1MR(KMeansMR, StdevMR):
    '''
    MRjob object to find YSO's. Searches for color outliers and then
    searches for clusters of outliers.
    '''

    OUTPUT_PROTOCOL = TextValueProtocol
    def mapper_clust_init(self):
        '''
        MRjob mapper init.
        '''
        self.list_len = 0
        self.node_list = []
        self.MAX_LEN = 1000  # Max number of outliers to compare to for clusters
        self.LEN_MULT = 0.5  # Reduction factor when MAX_LEN is reached
        self.TOP_K = 250  # Number of closest objects to draw radii with
        self.BINS = 15  # Number of bins into which we histogram the points
        self.STD_CUTOFF = 2.5



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
            yield from map_clust(astr, self.MAX_LEN, self.LEN_MULT,
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
        yield from comb_clust(astr, dist_gen, self.TOP_K, self.BINS)

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

    def reducer_return(self, junk, astr_gen):
        for astr in astr_gen:
            yield junk, astr.__repr__()

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
        final = [MRStep(mapper=self.mapper_return,
                        reducer=self.reducer_return)]

        return kmeans + stdev + cluster + stdev + final


if __name__ == '__main__':
    Algorithm1MR.run()
