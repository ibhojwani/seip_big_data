from mrjob.job import MRJob
from mrjob.step import MRStep
import csv
import numpy as np


class MR_get_sd(MRJob):
    """
    Find recommendations for which stellar objects to check.
    """


    def mapper(self, _, line):
        # Parse the CSV line:
        reader = csv.reader([line])
        line_list = next(reader)
        objid = line_list[-1]

        indexes = [4, 5, 6, 7, 8]

        pairs_list = []
        for num_1 in indexes:
            for num_2 in range(num_1 + 1, indexes[-1] + 1):
                pairs_list.append((num_1, num_2))

        # Skip the header row:
        # ra,dec,l,b,i1_f_ap1_bf,i2_f_ap1_bf,i3_f_ap1_bf
        # i4_f_ap1_bf,m1_f_ap_bf,i1_snr,i2_snr,i3_snr,i4_snr,m1_snr,objid

        if objid != "objid":
            # Calculate band differences:
            for sensor1, sensor2 in pairs_list:
                if sensor1 and sensor2:
                    key = str(sensor1) + "_" + str(sensor2)

                    try:
                        val = np.log(float(line_list[sensor1])) - \
                              np.log(float(line_list[sensor2]))
                        yield key, (val - MEAN_DICT[key])**2
                    except:
                        pass


    def combiner(self, label, diff_count):
        yield label, sum(diff_count)

    def reducer(self, label, sum_diff_count):
        yield label+"_SD", sum(sum_diff_count) / MEAN_DICT['n']


if __name__ == '__main__':

    MEAN_DICT = {}
    with open('means.csv') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            MEAN_DICT[row[0]] = float(row[1])

    MR_get_sd.run()