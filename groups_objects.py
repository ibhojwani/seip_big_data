from mrjob.job import MRJob
from astro_object import AstroObject
import numpy as np


class MrBoxAstroObjects(MRJob):
    """
    Sort astro objects into boxes
    """
    def mapper_init(self):
        self.dec_min = -90
        self.dec_max = 90
        self.ra_min = 0
        self.ra_max = 360
        self.dec_bins = np.linspace(start=self.dec_min, stop=self.dec_max,
                                    num=self.num_dec_bins + 1)
        self.ra_bins = np.linspace(start=self.ra_min, stop=self.ra_max,
                                   num=self.num_ra_bins + 1)

    def mapper(self, _, line):
        # Construct an astro object and push the attributes in:
        astro_obj = AstroObject()
        astro_obj.fill_attributes(line)

        # Astro objects coordinates:
        ra = astro_obj.ra
        dec = astro_obj.dec











if __name__ == '__main__':
    MrBoxAstroObjects.run()

