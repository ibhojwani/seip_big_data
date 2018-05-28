from mrjob.job import MRJob
from mrjob.step import MRStep
from numpy import sqrt, histogram, mean, array
from numpy.random import randint
from heapq import heappush, heappop
from scipy.interpolate import UnivariateSpline

def euc_dist(x1, x2, y1, y2, z1, z2, w1, w2):
    ''' This calculates the euclidean distance
    between two points in 4 dimensional space
    Inputs:
        - x1,x2 (floats): right ascension of points 1 and 2 ### ISHAAN PLEASE ADD UNITS
        - y1,y2 (floats): declination of points 1 and 2
        - z1,z2 (floats): proper motion right ascension
        - w1,w2 (floats): proper motion declination
    Outputs:
        - distance between the points (float) in degrees
    '''
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
    ''' This is a simple heapsort function
    Inputs:
        - iterable (i.e., list)
    Outputs: 
        - the same iterable, sorted in ascending order
    '''
    h = []
    for value in iterable:
        heappush(h, value)
    return h

class FindEdgesAndDistance(MRJob):
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
                        #yield i[0], (dist, objid)

    def reducer(self, objid, values):
        vals = heapsort(values)
        cutoff = min(TOP_K, len(vals)) # ensure we don't have indexerrors
        vals = vals[:cutoff]
        # Ids are unique
        yield objid, ([i[0] for i in vals]) # get distances


    def mapper_2(self, objid, values):
        counts, edges = histogram(values, BINS, density = True)       
        y = array([0] + list(counts))
        x = array(list(edges))
        spl = UnivariateSpline(x = x, y = y, k = 4)
        deltas = spl.derivative().roots()
        try: # sometimes derivatives throw exceptions
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
    N = 500 # num. values to keep for comparing, 
    P = 0.5 # factor by which to divide N
    # think of P as the inverse proportion we keep when the list 
    # gets full, i.e., 0.25 -> 75% dropped
    TOP_K = 250 # the number of closest values we take
    BINS = 40 # number of bins into which we histogram the points
    FindEdgesAndDistance.run()
