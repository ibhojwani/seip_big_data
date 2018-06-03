from mrjob.job import MRJob
from mrjob.protocol import PickleProtocol
from mrjob.step import MRStep
from math import sqrt


class StdevMR(MRJob):
    '''
    MRjob object to find outliers through standard deviation.
    '''

    INTERNAL_PROTOCOL = PickleProtocol

    STD_CUTOFF = 3.5

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


if __name__ == "__main__":
    StdevMR.run()
