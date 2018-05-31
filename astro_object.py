import csv

'''
'''


class AstroObject:
    def __init__(self):
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

    def fill_attributes(self, data_row):
        """
        Fill the attributes using a CSV row
        :param data_row: string, represents a CSV row
        :return: fill attributes
        """
        reader = csv.reader([data_row])
        line_list = next(reader)

        if line_list[0] != 'designation':
            self.objid = line_list[0]
            self.ra = line_list[1]
            self.dec = line_list[2]
            self.ra_uncert = line_list[3]
            self.dec_uncert = line_list[4]
            self.ra_motion = line_list[5]
            self.dec_motion = line_list[6]
            self.ra_motion_uncert = line_list[7]
            self.dec_motion_uncert = line_list[8]
            self.w1 = line_list[9]
            self.w2 = line_list[10]
            self.w3 = line_list[11]
            self.w4 = line_list[12]
            self.w1_snr = line_list[13]
            self.w2_snr = line_list[14]
            self.w3_snr = line_list[15]
            self.w4_snr = line_list[16]

    def __repr__(self):
        return self.objid
