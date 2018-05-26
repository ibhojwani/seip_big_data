from numpy import array
from pyspark.mllib.clustering import KMeans, KMeansModel
from pyspark import SparkConf, SparkContext


def build_kmeans(datafile, k):
    # Set up Spark context
    conf = SparkConf().setAppName("TBD_kmeans").setMaster("local[4]")
    sc = SparkContext(conf=conf)

    # Load and parse sensor data
    data = prep_data(datafile, sc)

    clusters = KMeans.train(data[-2:], 2, maxIterations=10)

    return clusters


def prep_data(path, sc):
    '''
    '''
    data = sc.textFile(path)

    # Remove header
    header = data.first()
    data = data.filter(lambda line: line != header)
    # str -> float
    data = data.map(lambda line: float(x)
                    for i, x in enumerate(line.split(",")) if i)
    # Calc color values
    data = data.map(lambda row: get_color(row))

    data =

    return data


def get_color(row):
    ''' '''
    sensor_idx = (9, 10, 11, 12)  # This should be a param in final main() func

    color_1 = row[sensor_idx[0]] - row[sensor_idx[1]]
    color_2 = row[sensor_idx[2]] - row[sensor_idx[3]]
    return row.append(color_1, color_2)


def get_outliers(clusters, row):
    group = clusters.predict(array([row[-1]]))
