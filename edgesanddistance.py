from mrjob.job import MRJob
from numpy import sqrt
from numpy.random import randint
from heapq import heappush, heappop

# simple euclidean distance
euc_dist = lambda x1, x2, y1, y2: sqrt((x1 - x2)**2 + (y1 - y2)**2)

# From heapq docs
def heapsort(iterable):
    h = []
    for value in iterable:
        heappush(h, value)
    return [heappop(h) for i in range(TOP_K)]

class FindEdgesAndDistance(MRJob):

    def mapper_init(self):
        self.node_list = [] # (tuple of fields from line)
        self.list_len = 0

    def mapper(self, _, line):
        # get the data
        vals = line.split(",")
        objid = vals[0]
        heappush(self.node_list, (objid, vals))
        self.list_len += 1

        # If our node list is too large, we randomly toss values
        if self.list_len > K:
            new_size = int(round(K * P))
            remove = randint(low = 0, high = len(self.node_list),
                                size = new_size)
            tmp_nodes = [self.node_list[i] for i in remove]
            self.node_list = tmp_nodes
            self.list_len = new_size
        # Validate that our list is still the right size
        elif self.list_len > K * P:
            # Now iterate over the nodes and find distances
            for i in self.node_list:
                dist = euc_dist(float(vals[1]), float(i[1][1]),
                                float(vals[2]), float(i[1][2]))
                dist2 = euc_dist(float(vals[2]), float(i[1][2]),
                                float(vals[3]), float(i[1][3]))
                if dist != dist2 != 0:
                    yield objid, (dist, dist2, i[0])
                    yield i[0], (dist, dist2, objid)

    def reducer(self, id, values):
    	vals = heapsort(values)
    	yield id, (vals) # get the TOP_K  closest objects

if __name__ == '__main__':
    K = 1000 # num. values to keep for comparing, 
    P = 0.5 # factor by which to divide K
    # think of P as the inverse proportion we keep when the list 
    # gets full, i.e., 0.25 -> 75% dropped
    # it is also the minimum number of points against which
    # we compare a node in order to create edges
    TOP_K = 10 # the number of closest values we take
    FindEdgesAndDistance.run()
