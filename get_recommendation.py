'''
CMSC 12300 Spr 2018
TBD
Creates an MRJob object to calculate the mean color-color values in a
variety of bands
'''


from mrjob.job import MRJob
from mrjob.step import MRStep
import csv
import numpy as np

# Data Headers:
# "designation", "ra_pm", "dec_pm", "sigra_pm", "sigdec_pm",
# "pmra", "pmdec", "sigpmra", "sigpmdec", "w1mpro", "w2mpro",
# "w3mpro", "w4mpro", "w1snr", "w2snr", "w3snr", "w4snr"


class MR_get_recommendation(MRJob):
    """
    Calculate mean color-color values of astronomical objects.
    """

    def mapper_0(self, _, line):
        # Parse the CSV line:
        reader = csv.reader([line])
        line_list = next(reader)
        objid = line_list[-1]

        sensor_idxs = [9, 10, 11, 12]

        pairs_list = []
        for num_1 in sensor_idxs:
            for num_2 in range(num_1 + 1, sensor_idxs[-1] + 1):
                pairs_list.append((num_1, num_2))

        if objid != "objid":  # Skips first row
            # Calculate band differences:
            for sensor1, sensor2 in pairs_list:
                if sensor1 and sensor2:
                    key = str(sensor1) + "_" + str(sensor2)

                    try:
                        yield key, np.log(float(line_list[sensor1])) - \
                            np.log(float(line_list[sensor2]))
                    except:
                        pass
            yield "n", 1

    def combiner_0(self, label, diff_count):
        yield label, sum(diff_count)

    def reducer_0_init(self):
        self.totals = {}

    def reducer_0(self, label, sum_diff_count):
        self.totals[label] = sum(sum_diff_count)

    def reducer_final_0(self, ):
        for key, value in self.totals.items():
            if key != "n":
                yield key, value / self.totals["n"]
            else:
                yield key, value

    def steps(self):
        return [
            MRStep(mapper=self.mapper_0,
                   combiner=self.combiner_0,
                   reducer_init=self.reducer_0_init,
                   reducer=self.reducer_0,
                   reducer_final=self.reducer_final_0),
        ]


if __name__ == '__main__':
    MR_get_recommendation.run()
