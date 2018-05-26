from math import sqrt
from pyspark.mllib.clustering import KMeans, KMeansModel
from pyspark import SparkConf, SparkContext
from sys import argv


def get_outliers(datafile, k):
    # Set up Spark context
    conf = SparkConf()
    sc = SparkContext(conf=conf)

    # Load and parse sensor data
    data = prep_data(datafile, sc)

    # Builds k-means clusters
    clusters = KMeans.train(
        data.map(lambda row: row[-2:]), 2, maxIterations=500)

    # Predict groups for each value, and store as last column in RDD
    data = data.map(lambda row: row.append(
        clusters.predict([row[-2], row[-1]])))

    # Calc std deviations
    # TODO optimize this?
    stdev_l = [data.filter(lambda row: row[-1] == 0).sampleStdev(),
               data.filter(lambda row: row[-1] == 1).sampleStdev()]

    # Get outliers
    data = data.filter(lambda row: get_dist(
        clusters, row) >= 2 * stdev_l[row[-1]])

    sc.stop()
    return data


def prep_data(path, sc):
    '''
    '''
    data = sc.textFile(path)

    # Remove header
    header = data.first()
    data = data.filter(lambda line: line != header)
    # str -> float
    data = data.map(lambda line: [float(x)
                                  for i, x in enumerate(line.split(",")) if i])
    # Calc color values
    data = data.map(lambda row: get_color(row))

    return data


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
    return sqrt(col_1 - center[0]) ** 2 + (col_2 - center[1]) ** 2


if __name__ == "__main__":
    datafile = argv[1]
    k = argv[2]
    get_outliers(datafile, k)


'''

spark-submit --master local[*] cs120/cs123/seip_big_data/outliers.py cs120/cs123/seip_big_data/data/5218562.csv 2


'''
