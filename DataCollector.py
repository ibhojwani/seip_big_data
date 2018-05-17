import damage_assessment
import geopandas as gpd


class DataCollector:

	def __init__(self, download_shp = 2):
		self.shapefiles = None
		print("Collecting Shapefiles")
		self.shapefiles = damage_assessment.build_assessments(download = download_shp)





if __name__ == "__main__":
	d = DataCollector()
	print(d.shapefiles)

