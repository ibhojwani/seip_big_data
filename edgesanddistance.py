from mrjob.job import MRJob
from mrjob.step import MRStep
from numpy import sqrt, histogram, mean, array
from numpy.random import randint
from heapq import heappush, heappop
from scipy.interpolate import UnivariateSpline

# simple euclidean distance in 4d space
def euc_dist(x1, x2, y1, y2, z1, z2, w1, w2):
    z1 = z1 / 3600000 # correct units
    z2 = z2 / 3600000
    w1 = w1 / 3600000
    w2 = w2 / 3600000
    a = (x1 - x2)**2 # right ascension
    b = (y1 - y2)**2 # declination
    c = (z1 - z2)**2 # proper motion right ascension
    d = (w1 - w2)**2 # proper motion declination
    return sqrt(sum([a, b, c, d]))

# From heapq docs
def heapsort(iterable):
    h = []
    for value in iterable:
        heappush(h, value)
    return h

class FindEdgesAndDistance(MRJob):

    def mapper_init(self):
        self.node_list = [] # (tuple of fields from line)
        self.list_len = 0

    def mapper(self, _, line):
        # get the data
        vals = line.split(",")
        objid = vals[0]
        if objid != "designation": # header

            heappush(self.node_list, (objid, vals))
            self.list_len += 1

            # If our node list is too large, we randomly toss values
            if self.list_len > N:
                new_size = int(round(N * P))
                keep = randint(low = 0, high = len(self.node_list),
                                    size = new_size)
                tmp_nodes = [self.node_list[i] for i in keep]
                self.node_list = tmp_nodes
                self.list_len = new_size
            # Validate that our list is still the right size
            if self.list_len > N * P:
                # Now iterate over the nodes and find distances
                for i in self.node_list:
                    x1 = float(vals[1]) # right ascension
                    x2 = float(i[1][1]) # ditto
                    y1 = float(vals[2]) # declination
                    y2 = float(i[1][2]) # ditto 
                    z1 = float(vals[5]) # motion in right ascension
                    z2 = float(i[1][5]) # ditto
                    w1 = float(vals[6]) # motion in declination
                    w2 = float(i[1][6]) # ditto
                    dist = euc_dist(x1, x2, y1, y2, z1, z2, w1, w2)
                    if dist != 0: # not interested in self-dist
                        yield objid, (dist, i[0])

    def reducer(self, objid, values):
        vals = heapsort(values)
        cutoff = min(TOP_K, len(vals)) # ensure we don't have indexerrors
        vals = vals[:cutoff]
        # Ids are unique
        distances = [i[0] for i in vals]
        objects = [i[1] for i in vals]
        counts, edges = histogram(distances, BINS, density = True)
        yield objid, (tuple(counts), tuple(edges))

    def mapper_2(self, objid, values):
        counts, edges = values
        y = array([0] + list(counts))
        x = array(list(edges))
        spl = UnivariateSpline(x = x, y = y, k = 4)
        deltas = spl.derivative().roots()
        try:
            if deltas[0] < 1:
                yield objid, (deltas[0])
        except:
            pass


    def steps(self):
        return [
            MRStep(mapper_init = self.mapper_init,
                    mapper = self.mapper,
                   reducer = self.reducer),
            MRStep(mapper = self.mapper_2),
        ]



if __name__ == '__main__':
    N = 5000 # num. values to keep for comparing, 
    P = 0.5 # factor by which to divide N
    # think of P as the inverse proportion we keep when the list 
    # gets full, i.e., 0.25 -> 75% dropped
    # it is also the minimum number of points against which
    # we compare a node in order to create edges
    TOP_K = 1000 # the number of closest values we take
    BINS = 40 # number of bins to histogram the points
    SAMPLE_N = 2 # bandwidth for finding average
    FindEdgesAndDistance.run()
