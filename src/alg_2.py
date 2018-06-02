"""
Algorithm II Implemenation.
"""
import astro_object
from mrjob.job import MRJob
from mrjob.step import MRStep
import mrjob
import numpy as np
import alg_2_util


class MrBoxAstroObjects(MRJob):
    """
    Sort astro objects into boxes and random walk within each box
    """

    # pass data internally with pickle
    INTERNAL_PROTOCOL = mrjob.protocol.PickleProtocol

    def mapper_init(self):
        # Initialize bins
        self.ra_bins, self.dec_bins = alg_2_util.create_bin(0, 360, -90, 90)

    def mapper(self, _, line):
        # Construct an astro object and push the attributes in:
        astr = astro_object.AstroObject(data_row=line)

        # yield only if there is an astro object
        if astr.is_complete():
            # sort astro object into bins based on ra and dec values
            ra_bin, dec_bin = alg_2_util.sort_bins(
                astr.ra, astr.dec, self.ra_bins, self.dec_bins)

            yield (ra_bin, dec_bin), astr

    def reducer(self, bounds, astr_gen):
        # compute probabilities for random walk
        astr_l = []
        for i in astr_gen:
            astr_l.append(i)  # bounds size is chosen so this is possible

        # Build prob matrix and complete random walk for each bin
        prob_matrix = alg_2_util.build_adjacency_matrix(astr_l)
        rw_astr_list = alg_2_util.random_walk(prob_matrix, 0, 500, astr_l)
        alg_2_util.watershed(bounds, rw_astr_list, 360)
        if rw_astr_list:
            yield bounds, rw_astr_list


if __name__ == '__main__':
    MrBoxAstroObjects.run()
