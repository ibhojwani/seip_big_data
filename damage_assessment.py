'''
CMSC 123000
Team TBD

Pulls top left and bottom right coordinates from UNOSAT damage reports.
Returns a list of DamageAssessment objects.
'''

import re
import zipfile
import geopandas as gpd
from requests import get
from bs4 import BeautifulSoup
import datetime
from os import listdir
from shutil import rmtree

STARTING_URL = "http://www.unitar.org/unosat/maps/SYR"


class DamageAssessment(object):
    def __init__(self, url):

        self.url = url
        self.title = None
        self.location = None  ###
        self.id = None
        self.date_posted = None
        self.first_date = None
        self.last_date = None

        self.top_left_site = None
        self.bottom_left_site = None
        self.top_left_gpd = None
        self.bottom_right_gpd = None

        self.shp_url = None
        self.shp_path = None
        self.shp_parent = None
        self.crs = None

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

        for raw_date in shape.SensorDate.unique():
            dates.add(datetime.datetime.strptime(raw_date, "%Y-%m-%d"))
        self.top_left_gpd = (total_bounds[MIN_X], total_bounds[MAX_Y])
        self.bottom_right_gdp = (total_bounds[MAX_X], total_bounds[MIN_Y])
        self.crs = shape.crs
        self.first_date = min(dates)
        self.last_date = max(dates)

        return None


def download_shp(dmg_assess):
    '''
    Given a download url, downloads and unzips the shape file.
    Inputs:
        url: url of shapefile download
        dmg_assess: DamageAssessment object to download for
    Returns None
    '''
    item = get(dmg_assess.shp_url)
    dir_name_zip = "{}.zip".format(dmg_assess.id)
    dmg_assess.shp_parent = "{}".format(dmg_assess.id)

    # Download shapefile zip
    with open(dir_name_zip, "wb") as f:
        for chunk in item.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    # Unzip directory
    zipped = zipfile.ZipFile(dir_name_zip, "r")
    zipped.extractall(dmg_assess.shp_parent)
    zipped.close()

    # Add path to .sph file. shp is 2 folders deep.
    middle_dir = dmg_assess.shp_parent + "/" + listdir(
        dmg_assess.shp_parent)[0]
    for file in listdir(middle_dir):
        if file.endswith(".shp"):
            dmg_assess.shp_path = middle_dir + "/" + file


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


def build_assessments(download=0, count=0, url=None, write=True):
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
    damage_assessments = []
    if url:
        link_list = [url]
    else:
        initial_soup = BeautifulSoup(get(STARTING_URL).content, "html.parser")
        link_list = get_assessment_links(initial_soup)
        if count:
            link_list = link_list[:count]

    for link in link_list:
        print(link)
        # Initialize object
        dmg_assess = DamageAssessment(link['href'])
        # Pull info from page
        dmg_assess.parse_assessment_pages()

        if not dmg_assess.id:
            continue

        # Dwnld, parse shp, and delete, depending on 'download' param.
        if download:
            download_shp(dmg_assess)
            dmg_assess.parse_shp()
            if download == 1:
                rmtree(dmg_assess.shp_parent)

        damage_assessments.append(dmg_assess)

    return damage_assessments
