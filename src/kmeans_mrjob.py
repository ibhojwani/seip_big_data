'''
CS12300
TBD
Implements the standard kmeans algorithm in MRJob to find centroids in
color data. Runs for a max number of iterations. If centroids converge then skips remaining iterations.
'''

from mrjob.job import MRJob
from mrjob.step import MRStep
from astro_object import AstroObject
from numpy.random import randint
from math import inf, sqrt


class KMeansMR(MRJob):

    def mapper(self, _, line):
        '''
        Calculate which centroid each object is closest to w/ squared
        eculidian distance, and yield the object coords and centroid.
        '''

        # Does nothing if centroids have converged
        if not done_flag:

            astr = AstroObject()
            color1 = None
            color2 = None

            if len(line) == 2:
                # Parses input from previous step
                color1 = line[0]
                color2 = line[1]

            else:
                # Parses fresh input from file
                astr.fill_small(line)
                if astr.w1 and astr.w2 and astr.w3 and astr.w4:
                    color1 = astr.w1 - astr.w2
                    color2 = astr.w3 - astr.w4

            # Calc closest centroid, yield that centroid and obj colors
            if color1 != None:
                closest = (inf, None)
                for i, center in enumerate(centroids):
                    dist = calc_dist(color1, color2, center[0], center[1])
                    if dist < closest[0]:
                        closest = (dist, i)

                yield closest[1], (color1, color2)

    def reducer_init(self):
        self.done = done_flag
        self.counter = 0
        self.color1_sum = 0
        self.color2_sum = 0

    def reducer(self, center, values):
        # get new centroids by averaging the locations of current groups
        if not self.done:
            for item in values:
                self.counter += 1
                self.color1_sum += item[0]
                self.color2_sum += item[1]
                yield None, item

            # Assign new centroids and compare to old. If they converge
            # then skip rest of steps
            centroids[center] = (round(self.color1_sum / self.counter, 5),
                                 round(self.color2_sum / self.counter, 5))
            if centroids == centroids_old:
                self.done = True

    def reducer_return(self, key, value):
        '''
        Stops extraneous output from previous reducers.
        '''
        return None

    def steps(self):
        k_means = [MRStep(mapper=self.mapper, reducer_init=self.reducer_init,
                          reducer=self.reducer)] * iterations
        return k_means + [MRStep(reducer=self.reducer_return)]


def calc_dist(x1, y1, x2, y2):
    '''
    Calculates squared euclid distance in 2 dimensions.
    Inputs:
        x1, y1: float, coords of object 1
        x2, y2: float, coords of object 2
    '''
    a = (x1 - x2)**2
    b = (y1 - y2)**2

    return a + b


if __name__ == "__main__":
    k = 2
    iterations = 5
    centroids = [(0, 0), (0.6, 4)]  # Approx location of centroids
    done_flag = False
    centroids_old = centroids.copy()
    KMeansMR.run()

    with open("kmeans_out.txt", "w") as f:
        f.write(str(centroids[0]) + " " + str(centroids[1]))


# approx centroid coords:
# [(0.063340125883, 0.92520348118), (0.371392924109, 2.92363654725)]
