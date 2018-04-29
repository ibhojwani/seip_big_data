from planet import api
import json
import os
import sys

from osgeo import gdal
from requests.auth import HTTPBasicAuth
import os
import requests
import time
from subprocess import run
from tkinter import filedialog



from settings import DEFAULT_ITEM_TYPE
from settings import GEOJSON_DIRECTORY
from settings import ACTIVATION_REQUEST

class PlanetPipeline:
# This is the planet pipeline
# largely based on planet documentation
# https://planetlabs.github.io/planet-client-python/api/examples.html

    def __init__(self, geojson_directory = None, default_item_type = None):
        # if not specified, use constants
        if geojson_directory == None:
            geojson_directory = GEOJSON_DIRECTORY
        if default_item_type == None:
            default_item_type = DEFAULT_ITEM_TYPE

        self.item_type = default_item_type
        self.client = api.ClientV1()
        self.geojson_dir = geojson_directory

        self.search_results = {}

    def search_all(self, **kwargs):
        print("Searching all results...")
        for i in os.listdir(self.geojson_dir):
            with open(self.geojson_dir + "/" + i) as f:
                try:
                    geojson_content = json.load(f)['features'][0]['geometry']
                except:
                    continue
                result = self.search(geojson_file = geojson_content, **kwargs)
                if result:
                    self.search_results[result] = i

    def search(self, geojson_file, date_after, date_before, cloud_threshold,
               resolution_threshold,
               item_types = DEFAULT_ITEM_TYPE,
               print_field = None, print_lim = 10):
        query = self.make_filters(date_after = date_after,
                                  date_before = date_before,
                                  geojson_file = geojson_file,
                                  cloud_threshold = cloud_threshold,
                                  resolution_threshold = resolution_threshold)

        request = api.filters.build_search_request(query, item_types)
        # this will cause an exception if there are any API related errors
        results = self.client.quick_search(request, sort = "acquired asc")

        asset_type = 'analytic'
        desired_item_type = "PSScene3Band"
        
        for item in results.items_iter(15):
            try:
                item_id = item['id']
                item_type = item['properties']['item_type']
                assets = self.client.get_assets(item).get()
                for asset in sorted(assets.keys()):
                    if asset == asset_type:
                        # request asset activation
                        activation_request = item_id.join(ACTIVATION_REQUEST)
                        response = run(activation_request, shell=True, check=True)
                        return item_id
            except:
                pass

    def fetch_asset(self, item_id):
        print("Fetching Asset {}".format(item_id))

        asset_type = 'analytic'

        desired_item_type = "PSScene3Band"
        item_url = 'https://api.planet.com/data/v1/item-types/{}/items/{}/assets'.format(desired_item_type, item_id)

        # Request a new download URL
        result = requests.get(item_url, auth=HTTPBasicAuth(os.environ['PL_API_KEY'], ''))

        if result.json()[asset_type]['status'] != 'active':
            print("Asset {} is not yet active...".format(item_id))
            return False
        try:
            # assemble urls and file paths
            download_url = result.json()[asset_type]['location']
            vsicurl_url = '/vsicurl/' + download_url
            geom_id = str(self.search_results[item_id]).split(".")[0]
            output_file = "image_" + geom_id + "_" + item_id +  '_subarea.tif'
            geojson_file = self.geojson_dir + "/" + self.search_results[item_id]

            # get the image clipped to our geojson file size
            gdal.Warp(output_file, vsicurl_url, dstSRS = 'EPSG:4326',
                      cutlineDSName = geojson_file,
                      cropToCutline = True)
            return True

        except Exception as e:
            print("Something went wrong", e)

    def fetch_all(self):
        fetch_list = [(i,j) for i, j in self.search_results.items()]
        num_tries = 15
        counter = 0
        while counter < num_tries:
            for i, j in fetch_list:
                print("Looking for assets: {} \n".format(fetch_list))
                result = self.fetch_asset(i)
                if result:
                    print("Bingo! Got one: {}".format(i))
                    fetch_list.remove((i,j))
            time.sleep(60)
            counter += 1
            print("Percent Complete: {}".format(counter/num_tries))
        print("Completed attempt")

    def make_filters(self, date_after, date_before, geojson_file, 
        cloud_threshold, resolution_threshold):
        print("Making filters")

        resolution = api.filters.range_filter('gsd', lt = resolution_threshold)

        # make cloud cover filters
        clouds = api.filters.range_filter('cloud_cover', lt=cloud_threshold)

        # make date filters
        start = api.filters.date_range('acquired', gt=date_after)
        end = api.filters.date_range('acquired', lt=date_before)

        place = api.filters.geom_filter(geojson_file)

        # build a filter for the AOI
        query = api.filters.and_filter(place, start, end, clouds, resolution)

        return query
    
if __name__ == "__main__":
    p = PlanetPipeline()
    date_list = [("2017-06-01", "2017-06-30"),
                 ("2017-07-01", "2017-07-30"),
                 ]

    for i, j in date_list:
        p.search_all(date_after = i, date_before = j,
                 print_field = 'id', cloud_threshold = 0.9,
                 resolution_threshold = 3)
    p.fetch_all()
