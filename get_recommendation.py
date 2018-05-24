from mrjob.job import MRJob
from mrjob.step import MRStep
import csv
import numpy as np


class MR_get_recommendation(MRJob):
    """
    Find recommendations for which stellar objects to check.
    """
    def mapper_0(self, _, line):
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

    def mapper_1(self, _, line):
        # Split the line into variables;
        # Get delta vector from the attributes;
        # Calculate vector's min and max ranges (error bounds) based on delta vector
        # Establish bins (based on direction and magnitude)
        # Put the delta vector to a bin based on delta vector value (not error bounds)
        # ? Key is object id;
        # ? Value is a tuple of all its attributes, including min and max ranges.
        # ? yield key, value tuple

    def combiner_1(self, obj_id, attrib_tuple):
        #



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
