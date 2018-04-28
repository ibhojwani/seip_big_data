from planet import api
import json
import os
import sys

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

    def search(self, geojson_file, item_types = DEFAULT_ITEM_TYPE,
               print_field = None, print_lim = 10):
        
        # load geojson and take the parts we need to filter
        aoi = json.load(geojson_file)['features'][0]['geometry']

        # build a filter for the AOI
        query = api.filters.and_filter(api.filters.geom_filter(aoi))
        request = api.filters.build_search_request(query, item_types)
        # this will cause an exception if there are any API related errors
        results = self.client.quick_search(request)

        if print_field != None:
            # items_iter returns an iterator over API response pages
            for item in results.items_iter(print_lim):
              # each item is a GeoJSON feature
              sys.stdout.write('%s\n' % item[print_field])
            sys.stdout.write('\n')
              
        self.search_results = results # keep results for later

if __name__ == "__main__":
    p = PlanetPipeline()
    p.search_all(print_field = 'id')
                
