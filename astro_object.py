'''
'''


class AstroObject():
    def __init__(self, data_row):
        '''
        A class for an astronomical object from the ALLWISE catalog.
        Inputs:
            data_row: str, a single row of csv containing a single object
        '''
        raw_vals = data_row.split(",")

        # ALLWISE catalog id
        self.objid = raw_vals[0]

        # Positions and uncertainty
        self.ra = raw_vals[1]
        self.dec = raw_vals[2]
        self.ra_uncert = raw_vals[3]
        self.dec_uncert = raw_vals[4]

        # Motions and uncertainty
        self.ra_motion = raw_vals[5]
        self.dec_motion = raw_vals[6]
        self.ra_motion_uncert = raw_vals[7]
        self.dec_motion_uncert = raw_vals[8]

        # Magnitudes in different bands, with signal to noise ratio (snr)
        self.w1 = raw_vals[9]
        self.w2 = raw_vals[10]
        self.w3 = raw_vals[11]
        self.w4 = raw_vals[12]
        self.w1_snr = raw_vals[13]
        self.w2_snr = raw_vals[14]
        self.w3_snr = raw_vals[15]
        self.w4_snr = raw_vals[16]

    def __repr__(self):
        print(self.objid)
