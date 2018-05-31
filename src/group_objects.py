import astro_object
from mrjob.job import MRJob
from mrjob.step import MRStep
import numpy as np


# def which_bin(value_to_sort, bin_array):
#     """
#     Determines the edges of the bin into which the value falls; inclusive of
#     upper boundary
#     :param value_to_sort: float, ra or dec value
#     :param bin_array: numpy array of dimensions (number of boundaries, )
#     :return: int, bin index, starting with 1
#     """
#     upper_edge = bin_array.max()
#     for index in range(bin_array.shape[0]):
#         if value_to_sort < bin_array[index]:
#             return bin_array[index - 1], bin_array[index]
#         elif value_to_sort == upper_edge:
#             return bin_array[index - 2], upper_edge


class MrBoxAstroObjects(MRJob):
    """
    Sort astro objects into boxes
    """

    def mapper_init_box(self):
        self.ra_min = 0
        self.ra_max = 360
        self.dec_min = -90
        self.dec_max = 90
        self.num_ra_bins = 360
        self.num_dec_bins = 360

        # "+1" Because the bins are in between numbers, so (number of bins) is
        # (number of boundaries - 1)
        self.ra_bins = np.linspace(start=self.ra_min, stop=self.ra_max,
                                   num=self.num_ra_bins + 1)
        self.dec_bins = np.linspace(start=self.dec_min, stop=self.dec_max,
                                    num=self.num_dec_bins + 1)

    def mapper_box(self, _, line):
        # Construct an astro object and push the attributes in:
        astr = astro_object.AstroObject(line)

        if astr.objid:
            ra_bin = int(np.digitize([astr.ra], self.ra_bins)[0])
            dec_bin = int(np.digitize([astr.dec], self.dec_bins)[0])

            yield (ra_bin, dec_bin), astr

    # def combiner_box(self, boounds, astr):
    #     yield bounds, astr

    def reducer_box(self, bounds, astr):
        yield bounds, astr

    def steps(self):
        return [
            MRStep(mapper_init=self.mapper_init_box,
                   mapper=self.mapper_box,
                   reducer=self.reducer_box)
        ]


if __name__ == '__main__':
    MrBoxAstroObjects.run()
