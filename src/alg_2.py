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
        self.ra_bins, self.dec_bins = alg_2_util.create_bins()

    def mapper(self, _, line):
        # Construct an astro object and push the attributes in:
        astr = astro_object.AstroObject(line)

        # yield only if there is an astro object
        if astr.objid:
            # sort astro object into bins based on ra and dec values
            ra_bin, dec_bin = alg_2_util.sort_bins(
                astr.ra, astr.dec, self.ra_bins, self.dec_bins)

            yield (ra_bin, dec_bin), astr

    def reducer(self, bounds, astr_gen):
        # compute probabilities for random walk
        astr_l = []
        for i in astr_gen:
            if not i.w1_snr:
                print(i)
            astr_l.append(i)
        prob_matrix = alg_2_util.build_adjacency_matrix(astr_l)
        # complete random walk for each bin
        rw_astr_list = alg_2_util.random_walk(prob_matrix,
                                              start_row=0,
                                              iterations=500,
                                              astro_objects_list=astr_l)  # TODO: MAKE THIS ACCEPT GENERATORS


if __name__ == '__main__':
    MrBoxAstroObjects.run()
