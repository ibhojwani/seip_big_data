from mrjob.job import MRJob
from mrjob.step import MRStep
import csv
import numpy as np


class MR_get_outliers(MRJob):
    """
    Find recommendations for which stellar objects to check.
    """

    def mapper(self, _, line):
        # Parse the CSV line:
        reader = csv.reader([line])
        line_list = next(reader)
        objid = line_list[1]

        sensor_idxs = [9, 10, 11, 12]

        pairs_list = []
        for num_1 in sensor_idxs:
            for num_2 in range(num_1 + 1, sensor_idxs[-1] + 1):
                pairs_list.append((num_1, num_2))

        # Skip the header row:
        # "designation", "ra_pm", "dec_pm", "sigra_pm", "sigdec_pm",
        # "pmra", "pmdec", "sigpmra", "sigpmdec", "w1mpro", "w2mpro",
        # "w3mpro", "w4mpro", "w1snr", "w2snr", "w3snr", "w4snr"

        if objid != "objid":
            # Calculate band differences:
            for sensor1, sensor2 in pairs_list:
                if sensor1 and sensor2:
                    key = str(sensor1) + "_" + str(sensor2)

                    try:
                        val = (float(line_list[sensor1]) -
                            float(line_list[sensor2])
                        if val > (2 * MEAN_DICT[key+"_SD"]) + MEAN_DICT[key]:
                            yield objid, val
                        if val < (2 * MEAN_DICT[key+"_SD"]) - MEAN_DICT[key]:
                            yield objid, val
                    except:
                        pass

    def reducer(self, obj_id, val):
        yield obj_id, None


if __name__ == '__main__':

    MEAN_DICT={}
    with open('centres.csv') as f:
        reader=csv.reader(f, delimiter='\t')
        for row in reader:
            MEAN_DICT[row[0]]=float(row[1])

    MR_get_outliers.run()
