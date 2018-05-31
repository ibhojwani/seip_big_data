from mrjob.job import MRJob
from mrjob.step import MRStep
from astro_object import AstroObject
import numpy as np


def which_bin(value_to_sort, bin_array):
    """
    Determines the edges of the bin into which the value falls; inclusive of
    upper boundary
    :param value_to_sort: float, ra or dec value
    :param bin_array: numpy array of dimensions (number of boundaries, )
    :return: int, bin index, starting with 1
    """
    upper_edge = bin_array.max()
    for index in range(bin_array.shape[0]):
        if value_to_sort < bin_array[index]:
            return bin_array[index - 1], bin_array[index]
        elif value_to_sort == upper_edge:
            return bin_array[index - 2], upper_edge


class MrBoxAstroObjects(MRJob):
    """
    Sort astro objects into boxes
    """
    def mapper_init(self):
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

    def mapper(self, _, line):
        # Construct an astro object and push the attributes in:
        astro_obj = AstroObject()
        astro_obj.fill_attributes(line)

        if astro_obj.objid:
            # Astro objects coordinates:
            ra = float(astro_obj.ra)
            dec = float(astro_obj.dec)

            ra_bounds = which_bin(value_to_sort=ra, bin_array=self.ra_bins)
            dec_bounds = which_bin(value_to_sort=dec, bin_array=self.dec_bins)

            yield (ra_bounds, dec_bounds), astro_obj

    def combiner(self, bounds, astro_obj):
        yield bounds, astro_obj

    def reducer(self, bounds, astro_objs):
        flattened_list = []
        for list_of_objs in astro_objs:
            for obj in list_of_objs:
                flattened_list.append(obj)
        yield bounds, flattened_list

    def steps(self):
        return [
            MRStep(mapper_init=self.mapper_init,
                   mapper=self.mapper,
                   combiner=self.combiner,
                   reducer=self.reducer)
        ]


if __name__ == '__main__':
    MrBoxAstroObjects.run()

