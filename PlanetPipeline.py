from planet import api
import json
import os
import sys

from osgeo import gdal
from requests.auth import HTTPBasicAuth
import os
import requests
import time


from settings import DEFAULT_ITEM_TYPE
from settings import GEOJSON_DIRECTORY

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
        
        self.geometries = []
        self.load_city_boundaries(geojson_directory)
        
        self.search_results = []
        
    def load_city_boundaries(self, geojson_directory):
        for i in os.listdir(geojson_directory):
            with open(geojson_directory + "/" + i) as f:
                # load geojson and take the parts we need to filter
                loaded_file = json.load(f)['features'][0]['geometry']
                self.geometries.append({i: loaded_file})
        self.geojson_dir = geojson_directory

    def search_all(self, **kwargs):
        for i in os.listdir(self.geojson_dir):
                with open(self.geojson_dir + "/" + i) as f:
                    self.search(f, **kwargs)

    def make_filters(self, date_after, date_before, geojson_file,
                     cloud_threshold, resolution_threshold):
        resolution = api.filters.range_filter('gsd', lt = resolution_threshold)
        
        # make cloud cover filters
        clouds = api.filters.range_filter('cloud_cover', lt=cloud_threshold)
        
        # make date filters
        start = api.filters.date_range('acquired', gt=date_after)
        end = api.filters.date_range('acquired', lt=date_before)
        
        # load geojson and take the parts we need to filter
        aoi = json.load(geojson_file)['features'][0]['geometry']
        place = api.filters.geom_filter(aoi)

        # build a filter for the AOI
        query = api.filters.and_filter(place, start, end, clouds, resolution)
        
        return query

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

        if print_field != None:
            # items_iter returns an iterator over API response pages
            for item in results.items_iter(print_lim):
              # each item is a GeoJSON feature
              #print(item)
              sys.stdout.write('%s\n' % item[print_field])
            sys.stdout.write('\n')
            
        self.retrieval_list = []
        for item in results.items_iter(print_lim):
            self.fetch_trimmed_image(item)
            break
            
    def fetch_trimmed_image(self, item):
        asset_activated = False
        count = 0
        print("Starting to get asset")

        while asset_activated == False:
            count += 1
            # Get asset and its activation status
            assets = self.client.get_assets(item).get()
            asset = assets.get('analytic')
            asset_status = asset["status"]
    
            # If asset is already active, we are done
            if asset_status == 'active':
                print("Asset is active and ready to download")
                down_link = asset['location']
                item_url = 'https://api.planet.com/data/v1/item-types/{}/items/{}/assets'.format(item_type, item_id)

                # Request a new download URL
                #result = requests.get(item_url, auth=HTTPBasicAuth(os.environ['PL_API_KEY'], ''))
                #self.search_results = results
                #print(retrieval_list) # keep results for later
                vsicurl_url = '/vsicurl/' + down_link
                output_file = item['id'] + '_subarea.tif'

                # GDAL Warp crops the image by our AOI, and saves it
                gdal.Warp(output_file, vsicurl_url, dstSRS = 'EPSG:4326', cutlineDSName = 'geojson_cities_2/map.geojson', cropToCutline = True)
                break
   
            # Still activating. Wait and check again.
            else:
                if count > 100:
                    break
                print("...Still waiting for asset activation...")
                time.sleep(10)

                

if __name__ == "__main__":
    p = PlanetPipeline()
    p.search_all(date_after = "2017-06-01", date_before = "2017-06-10",
                 print_field = 'id', cloud_threshold = 0.9,
                 resolution_threshold = 3) 
