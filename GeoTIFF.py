import rasterio
from scipy import ndimage as ndi
from scipy.ndimage import gaussian_filter
from scipy import misc
import matplotlib.pyplot as plt
import numpy as np


class GeoTiff:
    """
    Object representing data from a GeoTIFF image.
    """
    def __init__(self):
        """
        Object constructor method.
        """
        self.bands = {}
        self.gauss_bands = {}
        self.sharp_bands = {}
        self.num_bands = None
        self.labels = None
        self.ndvi = None

    def ingest_data(self, input_file, num_bands, labels):
        """
        Push GeoTIFF data into the object.
        :param input_file: str, of input GeoTiff address
        :param num_bands: int, number of bands in the input GeoTIFF
        :param labels: list of strings, where items are band labels
        :return:
        """
        self.labels = labels
        self.num_bands = num_bands
        with rasterio.open(input_file, "r") as dataset:
            for i in range(1, self.num_bands + 1):
                band = dataset.read(i)
                self.bands[self.labels[i - 1]] = band

    def calculate_ndvi(self):
        """
        Calculate NDVI scores using GeoTIFF bands.
        """
        self.ndvi = (self.bands["n"].astype(float) - self.bands["r"].astype(float)) \
                    / (self.bands["n"].astype(float) + self.bands["r"].astype(float))

    def gaussify_bands(self, sigma):
        """
        Introduce normal smoothing to pixels.
        :param sigma: standard deviation input for the gaussian distribution
        """
        for key, band in self.bands.items():
            self.gauss_bands[key] = gaussian_filter(input=band, sigma=sigma)

    def sharpen_bands(self):
        """
        Produce a matrix with edge detection.
        """
        for label in self.labels:
            self.sharp_bands[label] = self.bands[label] - self.gauss_bands[
                label]

    def draw_matrix(self, destination, version, band):
        """
        Take a numpy array representation and output a visual .jpg.
        :param destination: str, where to print out the matrix
        :param version: str, which matrix, e.g. "band", "gauss", "sharp", "ndvi"
        :param band: str, band choice, e.g. "b", "g", "r", "n", "ndvi"
        """
        if version == "band":
            matrix = self.bands[band]
        elif version == "gauss":
            matrix = self.gauss_bands[band]
        elif version == "sharp":
            matrix = self.sharp_bands[band]
        else:
            matrix = self.ndvi
        fig = plt.figure(figsize=(100, 50))
        ax = fig.add_subplot(121)
        ax.imshow(matrix)
        plt.savefig(destination)


aleppo_full = GeoTiff()
aleppo_full.ingest_data(input_file="data/experimental/aleppo_full_order/20180206_073917_0f42_3B_AnalyticMS.tif",
                         num_bands=4, labels=["b", "g", "r", "n"])
# Allow division by zero
np.seterr(divide='ignore', invalid='ignore')
aleppo_full.calculate_ndvi()
aleppo_full.gaussify_bands(sigma=10)
# aleppo_full.sharpen_bands()
print(aleppo_full.gauss_bands)

