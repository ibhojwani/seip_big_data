from mrjob.job import MRJob
from mrjob.step import MRStep
from astro_object import AstroObject
from numpy.random import randint
from math import inf, sqrt


class KMeansMR(MRJob):

    def mapper(self, _, line):
        astr = AstroObject()
        color1 = None
        color2 = None

        if len(line) == 2:
            color1 = line[0]
            color2 = line[1]

        else:
            astr.fill_attributes(line)
            if astr.w1 and astr.w2 and astr.w3 and astr.w4:
                color1 = astr.w1 - astr.w2
                color2 = astr.w3 - astr.w4

        if color1 and color2:
            closest = (inf, None)
            for i, center in enumerate(centroids):
                dist = calc_dist(color1, color2, center[0], center[1])
                if dist < closest[0]:
                    closest = (dist, i)

            yield closest[1], (color1, color2)

    def reducer_init(self):
        self.counter = 0
        self.color1_sum = 0
        self.color2_sum = 0

    def reducer(self, center, values):
        for item in values:
            self.counter += 1
            self.color1_sum += item[0]
            self.color2_sum += item[1]
            yield None, item

        centroids[center] = (self.color1_sum / self.counter,
                             self.color2_sum / self.counter)

    # def reducer_return(self, trash, garbage):
    #     yield centroids
    def reducer_final(self):
        for center in centroids:
            yield center[0], center[1]

    def steps(self):
        k_means = [MRStep(mapper=self.mapper, reducer_init=self.reducer_init,
                          reducer=self.reducer)] * iterations
        return k_means  # + [MRStep(reducer=self.reducer_return)]


def calc_dist(x1, y1, x2, y2):
    a = (x1 - x2)**2
    b = (y1 - y2)**2

    return sqrt(a + b)


def generate_centroids(k):
    color1_rand = randint(0, 10, k)
    color2_rand = randint(0, 10, k)

    return [(color1_rand[i], color2_rand[i]) for i in range(k)]


if __name__ == "__main__":
    k = 2
    iterations = 50
    centroids = generate_centroids(k)

    KMeansMR.run()

    print(centroids)
