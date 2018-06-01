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



def create_bins(num_ra_bins=360, num_dec_bins=180):
    RA_MIN = 0
    RA_MAX = 360
    DEC_MIN = -90
    DEC_MAX = 90
    num_ra_bins = 360
    num_dec_bins = 360

    # "+1" Because the bins are in between numbers, so (number of bins) is
    # (number of boundaries - 1)
    ra_bins = np.linspace(start=RA_MIN, stop=RA_MAX,
                          num=num_ra_bins + 1)
    dec_bins = np.linspace(start=DEC_MIN, stop=DEC_MAX,
                           num=num_dec_bins + 1)

    return ra_bins, dec_bins


def sort_bins(ra, dec, ra_bins, dec_bins):

    ra_bin = np.digitize([ra], ra_bins)[0]
    dec_bin = np.digitize([dec], dec_bins)[0]

    return ra_bin - 1, dec_bin - 1


class MrBoxAstroObjects(MRJob):
    """
    Sort astro objects into boxes
    """

    def mapper_init_box(self):
        self.ra_bins, self.dec_bins = create_bins()

    def mapper_box(self, _, line):
        # Construct an astro object and push the attributes in:
        astr = astro_object.AstroObject(line)

        if astr.objid:
            ra_bin, dec_bin = sort_bins(
                astr.ra, astr.dec, self.ra_bins, self.dec_bins)

            yield (ra_bin, dec_bin), astr

    # def combiner_box(self, boounds, astr):
    #     yield bounds, astr

    def reducer_box(self, bounds, astr):
        yield bounds, astr

    def steps(self):
        return [
            MRStep(mapper_init=self.mapper_init_box,
                   mapper=self.mapper_box,
                   # combiner=combiner_box,
                   reducer=self.reducer_box)
        ]


if __name__ == '__main__':
    MrBoxAstroObjects.run()
