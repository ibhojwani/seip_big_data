"""
Algorithm II Implemenation.
"""
import astro_object
from mrjob.job import MRJob
from mrjob.step import MRStep
import mrjob
import numpy as np
import random_walk


def create_bins(num_ra_bins=360, num_dec_bins=360):
    """
    Create equally spaced bins for ra and dec coordinate ranges
    :param num_ra_bins: integer, how many bins for ra
    :param num_dec_bins: integer, how many bins for dec
    :return ra_bins, dec_bins: tuple of numpy arrays with bin boundaries
    """
    RA_MIN = 0
    RA_MAX = 360
    DEC_MIN = -90
    DEC_MAX = 90
    num_ra_bins = num_ra_bins
    num_dec_bins = num_dec_bins

    # "+1" Because the bins are in between numbers, so (number of bins) is
    # (number of boundaries - 1)
    ra_bins = np.linspace(start=RA_MIN, stop=RA_MAX,
                          num=num_ra_bins + 1)
    dec_bins = np.linspace(start=DEC_MIN, stop=DEC_MAX,
                           num=num_dec_bins + 1)

    return ra_bins, dec_bins


def sort_bins(ra, dec, ra_bins, dec_bins):
    """
    Sorts an astro object in a specific bin based on that astro object's
    right ascension and declination values.
    :param ra: float, right ascension
    :param dec: float, declination
    :param ra_bins: float
    :param dec_bins: float
    :return ra_bin, dec_bin: floats
    """
    ra_bin = int(np.digitize([ra], ra_bins)[0])
    dec_bin = int(np.digitize([dec], dec_bins)[0])

    return ra_bin - 1, dec_bin - 1


class MrBoxAstroObjects(MRJob):
    """
    Sort astro objects into boxes and random walk within each box
    """
    # get input as raw strings
    INPUT_PROTOCOL = mrjob.protocol.RawValueProtocol
    # pass data internally with pickle
    INTERNAL_PROTOCOL = mrjob.protocol.PickleProtocol
    # write output as JSON
    OUTPUT_PROTOCOL = mrjob.protocol.PickleProtocol

    def mapper_init_box(self):
        # Initialize bins
        self.ra_bins, self.dec_bins = create_bins()

    def mapper_box(self, _, line):
        # Construct an astro object and push the attributes in:
        astr = astro_object.AstroObject(line)

        # yield only if there is an astro object
        if astr.objid:
            # sort astro object into bins based on ra and dec values
            ra_bin, dec_bin = sort_bins(
                astr.ra, astr.dec, self.ra_bins, self.dec_bins)

            yield (ra_bin, dec_bin), astr

    def combiner_box(self, bounds, astr):
        # Collect from a generator and collapse across same bound
        # within each node:
        astr_list = list(astr)
        yield bounds, astr_list

    def reducer_box(self, bounds, astr_lists):
        # collapse lists of astro objects from different nodes across
        # same bins together

        # Flatten the list:
        flat_astr_list = []
        for astro_list in astr_lists:
            for astro_obj in astro_list:
                flat_astr_list.append(astro_obj)
        yield bounds, flat_astr_list

    def mapper_rand_walk(self, bounds, flat_astr_list):
        # compute probabilities for random walk
        prob_matrix = random_walk.build_adjacency_matrix(flat_astr_list)

        # complete random walk for each bin; fills int
        # counts of visits for each astro object in the flat_astr_list,
        # but yields a deep copy of that list:
        rw_astro_list = random_walk.random_walk(prob_matrix,
                                                start_row=0,
                                                iterations=500,
                                                astro_objects_list=flat_astr_list)
        yield bounds, rw_astro_list

    def steps(self):
        return [
            MRStep(mapper_init=self.mapper_init_box,
                   mapper=self.mapper_box,
                   combiner=self.combiner_box,
                   reducer=self.reducer_box),
            MRStep(mapper=self.mapper_rand_walk)
        ]


if __name__ == '__main__':
    MrBoxAstroObjects.run()
