'''
CMSC 123000
Team TBD

Pulls top left and bottom right coordinates from UNOSAT damage reports.
Returns a list of DamageAssessment objects.
'''

import re
import zipfile
import geopandas as gpd
import datetime
import os
from copy import deepcopy
from requests import get
from bs4 import BeautifulSoup
from shutil import rmtree

STARTING_URL = "http://www.unitar.org/unosat/maps/SYR"


class OnlineInfo(object):
    def __init__(self, url):
        self.url = url
        self.title = None
        self.id = None
        self.date_posted = None

        self.top_left_site = None
        self.bottom_left_site = None

        self.shp_url = None
        self.dir_path

    def parse_assessment_pages(self):
        ''' For a given DamageAssessment object, pull coords, date, id,
            and the shapefile URL.
            Inputs:
                url: url to parse
            Returns None, but modifies self.
        '''
        dmg_soup = BeautifulSoup(get(self.url).content, "html.parser")

        # If shapefile isn't on the page, return none
        for link in dmg_soup.find_all("a"):
            if "shapefile" in link.text.lower():
                self.shp_url = link['href']

        if not self.shp_url:
            return None

        # Pull the top left and bottom right coords and the date
        for section in dmg_soup.find_all("td"):
            if "Published" in section.text:
                self.id = re.search(r"(?<=Product ID:\s)\d\d\d\d",
                                    section.text).group()
                raw_coords = re.findall(r"\d\d\.\d\d* x \d\d\.\d\d*",
                                        section.text)
                raw_date = re.search(r"\d \w\w\w, \d\d\d\d",
                                     section.text).group()
                break

        self.title = dmg_soup.title
        self.top_left_site = raw_coords[0].split(" x ")
        self.bottom_right_site = raw_coords[1].split(" x ")
        self.date_posted = datetime.datetime.strptime(raw_date, "%d %b, %Y")

        return None

    def download_shp(self):
        '''
        Given a download url, downloads and unzips the shape file.
        Returns None
        '''
        item = get(self.shp_url)
        dir_name_zip = "{}.zip".format(self.id)
        self.dir_path = "{}".format(self.id)

        # Download shapefile zip
        with open(dir_name_zip, "wb") as f:
            for chunk in item.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        # Unzip directory
        zipped = zipfile.ZipFile(dir_name_zip, "r")
        zipped.extractall(self.dir_path)
        zipped.close()

        # Add path to .sph file. shp is 2 folders deep.
        middle_dir = self.dir_path + "/" + os.listdir(
            self.dir_path)[0]
        for file in os.listdir(middle_dir):
            if file.endswith(".shp"):
                self.dir_path = middle_dir + "/" + file


class DamageAssessment(OnlineInfo):
    def __init__(self, url):
        self.location = None
        self.first_date = None
        self.last_date = None

        self.top_left_gpd = None
        self.bottom_right_gpd = None

        self.shp_path = None
        self.shp_parent = None
        self.crs = None

    def parse_shp(self):
        '''
        If shapefile is downloaded, parse it to get crs, bounds,
        location.
        '''
        shape = gpd.read_file(self.shp_path)
        dates = set()
        total_bounds = shape.total_bounds
        MIN_X = 0
        MIN_Y = 1
        MAX_X = 2
        MAX_Y = 3

        # for raw_date in shape.SensorDate.unique():
        # dates.add(datetime.datetime.strptime(raw_date, "%Y-%m-%d"))
        self.top_left_gpd = (total_bounds[MIN_X], total_bounds[MAX_Y])
        self.bottom_right_gdp = (total_bounds[MAX_X], total_bounds[MIN_Y])
        self.crs = shape.crs
        # self.first_date = min(dates)
        # self.last_date = max(dates)

        return None


def find_shp(direc, shp_list):
    '''
    Recursively search for all .shp files in subdirectories.
    Inputs:
        direc: string path of directory to search
        shp_list: empty list for shp file paths
    Returns: None, but modifies shp_list
    '''
    if direc.endswith(".shp"):
        shp_list.append(os.path.relpath(direc))
        return shp_list

    if os.path.isfile(direc):
        return None

    for sub_dir in os.listdir(direc):
        find_shp(direc + "/" + sub_dir, shp_list)

    return shp_list


def get_assessment_links(soup):
    '''
    Gets the links to all damage assessment pages.
    '''
    page_links = soup.find_all("a")
    link_list = []
    for link in page_links:
        if (link.contents) and ("damage" in link.text.lower()):
            link_list.append(link)

    return link_list


def build_assessments(download=0, count=0, url=None, write=True, assessments=[]):
    '''
    Builds and returns a list of DamageAssessment objects.
    Inputs:
        download: whether or not to download shape (.shp) files.
            0: Do not download (does not get info from .shp)
            1: Download, get info, then delete
            2: Download, get info, and store on disk
        count: number of damage reports returned. count = 0 returns all.
        url: If a particular damage report is wanted, use this to
            specify which one with url (of dmg rept page, NOT of .shp).
    Returns a list of DamageAssessment objects.
    '''
    assert not (count
                and url), "If specific assessment url given, count must be 0"

    # Prepare links to search
    if url:
        link_list = [url]
    else:
        initial_soup = BeautifulSoup(get(STARTING_URL).content, "html.parser")
        link_list = get_assessment_links(initial_soup)
        if count:
            link_list = link_list[:count]

    # Iterate through and build DamageAssessment objects
    for link in link_list:
        print(link)
        # Initialize object
        page_info = OnlineInfo(link['href'])
        # Pull info from page
        try:
            # Parses web page for info
            page_info.parse_assessment_pages()

            if not page_info.id:  # If invalid page, skip
                continue
            if not download:  # If no download requested, do no more
                assessments.append(page_info)
                continue

            # Dwnld, parse shp, and delete, depending on 'download' param.
            download_shp(page_info)

            dmg_assess.parse_shp()
            if download == 1:
                rmtree(dmg_assess.shp_parent)

            assessments.append(dmg_assess)
        except:
            print(dmg_assess)
            return assessments

    return assessments
