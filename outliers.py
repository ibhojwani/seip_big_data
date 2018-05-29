'''
Parses IRSA data to look for color outliers. From preliminary analysis,
data is approx bimodal in distribution. This uses k-means to find the 
centers of each group, and then calculates the stdev of each group.
Objects are outliers if they sit outside of 2 stdevs from the centers 
of their groups.

Run locally with (depending on machine):
spark-submit --executor-memory 8G --driver-memory 2G --master local[*] cs120/cs123/seip_big_data/outliers.py cs120/cs123/seip_big_data/data/5218562.csv 2


TODO:
    dont need so many lambdas
    not cutting enough?
'''

from math import sqrt
from pyspark.mllib.clustering import KMeans, KMeansModel
from pyspark import SparkConf, SparkContext
from pyspark.sql import SparkSession
from sys import argv
from time import sleep


# Multiplier for stdev cutoff for outlier classification
CUTOFF = 4


def get_outliers(datafile, k, out_path):
    # Set up Spark context
    conf = SparkConf().setMaster("local")
    sc = SparkContext(conf=conf)
    spark = SparkSession.builder.getOrCreate()

    try:
        # Load and parse sensor data
        data = prep_data(datafile, spark)

        # Builds k-means clusters
        clusters = KMeans.train(
            data.map(lambda row: row[-2:]), 2, maxIterations=500)

        # Predict groups for each value, and store as last column in RDD
        data = data.map(lambda row: row +
                        [clusters.predict([row[-2], row[-1]])])
        # Calc std deviations
        # TODO optimize this?
        sleep(4)
        stdev_l = [data.filter(lambda row: row[-1] == 0).map(lambda row: get_dist(clusters, row[-3:])).sampleStdev(),
                   data.filter(lambda row: row[-1] == 1).map(lambda row: get_dist(clusters, row[-3:])).sampleStdev()]
        sleep(4)
        # Get outliers
        data = data.filter(lambda row: get_dist(
            clusters, row) >= CUTOFF * stdev_l[row[-1]])

    except:
        sc.stop()
        return False

    data.coalesce(1).saveAsTextFile(out_path)
    sc.stop()

    return data


def prep_data(path, spark):
    '''
    '''
    data = spark.read.load(path, format="csv", sep=":",
                           inferSchema='true', header='true').rdd
    # Remove header
    header = data.first()
    data = data.filter(lambda line: line != header)
    # str -> float
    data = data.map(lambda line: str_to_float(line))
    # Filter rows with None values
    data = data.filter(lambda line: None not in line)
    # Calc color values
    data = data.map(lambda row: get_color(row))

    return data


def str_to_float(line):
    split = line[0].split(",")
    floats = []
    for item in split[1:]:
        if item:
            floats.append(float(item))
        else:
            floats.append(None)
    return [split[0]] + floats


def get_color(row):
    ''' '''
    sensor_idx = (9, 10, 11, 12)  # This should be a param in final main() func

    color_1 = row[sensor_idx[0]] - row[sensor_idx[1]]
    color_2 = row[sensor_idx[2]] - row[sensor_idx[3]]
    return row + [color_1, color_2]


def get_dist(clusters, row):
    center = clusters.clusterCenters[row[-1]]
    col_1 = row[-3]
    col_2 = row[-2]
    return sqrt((col_1 - center[0]) ** 2 + (col_2 - center[1]) ** 2)


if __name__ == "__main__":
    datafile = argv[1]
    k = argv[2]
    out_path = argv[3]
    get_outliers(datafile, k, out_path)


'''
spark-submit --executor-memory 8G --driver-memory 2G --master local[*] outliers.py data/5218562.csv 2 outfile.txt
'''
