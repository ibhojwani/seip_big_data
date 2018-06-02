"""
Astro-object class.
"""
from numpy import sqrt


class AstroObject:
    def __init__(self, data_row=None, small=False, dic=None):
        """
        A class for an astronomical object from the ALLWISE catalog.
        Inputs:
            data_row: str, a single row of csv containing a single object
        """
        # ALLWISE catalog id
        self.objid = None

        # Positions and uncertainty
        self.ra = None
        self.dec = None
        self.ra_uncert = None
        self.dec_uncert = None

        # Motions and uncertainty
        self.ra_motion = None
        self.dec_motion = None
        self.ra_motion_uncert = None
        self.dec_motion_uncert = None

        # Magnitudes in different bands, with signal to noise ratio (snr)
        self.w1 = None
        self.w2 = None
        self.w3 = None
        self.w4 = None
        self.w1_snr = None
        self.w2_snr = None
        self.w3_snr = None
        self.w4_snr = None
        self.color1 = None
        self.color2 = None

        self.k_closest = []
        self.bin_id = None
        self.dist_from_center = None
        self.rand_walk_visits = 0

        # If info is provided, initialize
        if data_row:
            self.fill_attributes(data_row)

        elif dic:
            if small:
                self.fill_small(dic)
            else:
                self.from_dict(dic)

    def fill_attributes(self, data_row):
        """
        Fill the attributes using a CSV row
        :param data_row: string, represents a CSV row
        :return: fill attributes
        """
        line_list = data_row.split(",")
        if line_list[0] == "designation":
            return None
        try:
            self.objid = line_list[0]

            self.ra = float(line_list[1])
            self.dec = float(line_list[2])
            self.ra_uncert = float(line_list[3])
            self.dec_uncert = float(line_list[4])
            self.ra_motion = float(line_list[5])
            self.dec_motion = float(line_list[6])
            self.ra_motion_uncert = float(line_list[7])
            self.dec_motion_uncert = float(line_list[8])
            self.w1 = float(line_list[9])
            self.w2 = float(line_list[10])
            self.w3 = float(line_list[11])
            self.w4 = float(line_list[12])
            self.w1_snr = float(line_list[13])
            self.w2_snr = float(line_list[14])
            self.w3_snr = float(line_list[15])
            self.w4_snr = float(line_list[16])
            self.color1 = self.w1 - self.w2
            self.color2 = self.w3 - self.w4
        except:
            print(line_list)

    def fill_small(self, line_list):
        self.objid = line_list[0]
        self.ra = float(line_list[1])
        self.dec = float(line_list[2])
        self.ra_motion = float(line_list[5])
        self.dec_motion = float(line_list[6])
        self.w1 = float(line_list[9])
        self.w2 = float(line_list[10])
        self.w3 = float(line_list[11])
        self.w4 = float(line_list[12])

    def package_small(self):
        to_add = ["ra", "dec", "objid", "ra_motion",
                  "dec_motion", "w1", "w2", "w3", "w4"]
        d = self.__dict__
        rv = {}
        for field in to_add:
            rv[field] = d[field]

        return rv

    @staticmethod
    def sq_euc_2d(x1, y1, x2, y2):
        '''
        Calculates squared euclid distance in 2 dimensions.
        Inputs:
            x1, y1: float, coords of object 1
            x2, y2: float, coords of object 2
        '''
        a = (x1 - x2)**2
        b = (y1 - y2)**2

        return a + b

    def euc_dist_4d(self, other):
        """
        This calculates the euclidean distance
        between two objects in 4 dimensional space (ra, dec, ra motion,
        dec motion)
        Inputs:
            other: AstroObject to comapre to.
        Outputs:
            - distance between the points (float) in degrees
        """
        MAS_TO_DEG = 1 / 3600000  # Conversion from millisecond to degree

        ra1 = self.ra
        ra2 = other.ra

        dec1 = self.dec
        dec2 = other.dec

        # Note: not using MAS_TO_DEG because this devalues direction
        pmra1 = self.ra_motion
        pmra2 = other.ra_motion

        pmdec1 = self.dec_motion
        pmdec2 = other.dec_motion

        a = (ra1 - ra2) ** 2
        b = (dec1 - dec2) ** 2
        c = (pmra1 - pmra2) ** 2
        d = (pmdec1 - pmdec2) ** 2

        return sqrt(sum([a, b, c, d]))

    def from_dict(self, d):
        for field in d.keys():
            setattr(self, field, d[field])

    # Unused as of now but might be useful.
    def __lt__(self, other):
        if self.bin_id[0] < other.bin_id[0]:
            return True
        if self.bin_id[0] == other.bin_id[0]:
            if self.bin_id[1] < other.bin_id[1]:
                return True
        return False

    def __gt__(self, other):
        if self.bin_id[0] > other.bin_id[0]:
            return True
        if self.bin_id[0] == other.bin_id[0]:
            if self.bin_id[1] > other.bin_id[1]:
                return True
        return False

    def __repr__(self):
        if self.objid:
            return self.objid
        else:
            return ""

    def __hash__(self):
        # use the hashcode of self.objid since that is used
        # for equality checks as well
        return hash(self.objid)
