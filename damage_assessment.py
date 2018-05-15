'''
CMSC 123000
Team TBD

Pulls top left and bottom right coordinates from UNOSAT damage reports.
Returns a list of DamageAssessment objects.
'''

import re
import geopandas as gpd
from requests import get
from bs4 import BeautifulSoup
import datetime

STARTING_URL = "http://www.unitar.org/unosat/maps/SYR"


class DamageAssessment(object):
    def __init__(self, url):

        self.url = url
        self.title = None
        self.location = None
        self.id = None
        self.date_posted = None
        self.first_date = None
        self.last_date = None

        self.top_left_site = None
        self.bottom_left_site = None
        self.top_left_gpd = None
        self.bottom_right_gpd = None

        self.shp_url = None
        self.shp = None
        self.crs = None


def get_assessment_links(soup):
    '''
    Gets the links to all damage assessment pages.
    '''
    page_links = soup.find_all("a")
    link_list = []
    for link in page_links:
        if "damage" in link.text.lower():
            link_list.append(link)

    return link_list


def parse_assessment_pages(url, dmg_assess):
    ''' For a given DamageAssessment object, pull coords, date, id, and
        the shapefile URL.
        Inputs:
            url: url to parse
            dmg_assess: DamageAssessment object to modify
        Returns None, but modifies dmg_assess.
    '''
    dmg_soup = BeautifulSoup(get(url).contents, "html.parser")

    # If shapefile isn't on the page, return none
    for link in dmg_soup.find_all("a"):
        if "shapefile" in link.text.lower():
            dmg_assess.shp_url = link['href']

    if not dmg_assess.shp_url:
        return None

    # Pull the top left and bottom right coords and the date
    for section in dmg_soup.find_all("td"):
        if "Published" in section.text:
            dmg_assess.id = re.search(r"(?<=Product ID:\s)\d\d\d\d",
                                      section.text).group()
            raw_coords = re.findall(r"\d\d\.\d\d* x \d\d\.\d\d*", section.text)
            raw_date = re.search(r"\d \w\w\w, \d\d\d\d", section.text).group()
            break

    dmg_assess.title = dmg_soup.title
    dmg_assess.top_left_site = raw_coords[0].split(" x ")
    dmg_assess.bottom_right_site = raw_coords[1].split(" x ")
    dmg_assess.date_posted = datetime.datetime.strptime(raw_date, "%d %b, $Y")

    return None


def parse_shp(shp_path, dmg_assess):
    '''
    If shapefile is downloaded, parse it to get crs, bounds, location.
    '''
    shape = gpd.read_file(shp_path)
    dates = set()

    for raw_date in shape.SensorDate.unique():
        dates.add(datetime.datetime.strptime(raw_date, "%Y-%m-%d"))

    dmg_assess.crs = shape.crs
    dmg_assess.first_date = min(dates)
    dmg_assess.last_date = max(dates)

    return None


def build_assessments(download=0, count=0, url=STARTING_URL):
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

    return None


def download_shp(url):
    return None


def pull_info():
    '''
    Build a list of dmg report objects w/ coords.
    '''
    initial_soup = BeautifulSoup(get(STARTING_URL).content, "html.parser")
    link_list = initial_soup.find_all("a")
    damage_assessments = []

    for lnk in link_list:
        # Check if damage assessment
        if lnk.contents and ("damage" in lnk.contents[0].lower()):
            url = lnk['href']
            soup = BeautifulSoup(get(url).content, "html.parser")

            # Check that shape file is included on page
            if re.findall("Shapefile", str(soup.find_all("a"))):
                dmg_assess = DamageAssessment(soup, url)

                # If coordinates are listed, add dmg assess to list
                if dmg_assess.top_left and dmg_assess.bottom_right:
                    damage_assessments.append(dmg_assess)

    return damage_assessments


if __name__ == "__main__":
    print(pull_info())
