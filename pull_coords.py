'''
CMSC 123000
Team TBD

Pulls top left and bottom right coordinates from UNOSAT damage reports.
Returns a list of DamageAssessment objects.
'''

import re

from requests import get
from bs4 import BeautifulSoup


STARTING_URL = "http://www.unitar.org/unosat/maps/SYR"


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


class DamageAssessment(object):

    def __init__(self, soup, url):
        self.url = url
        self.soup = soup
        self.title = self.soup.title
        self.top_left, self.bottom_right = self.get_coords()
        self.images = []

    def get_coords(self):
        '''
        Pulls top left and bottom right coords from page.
        '''
        coord_section = str(self.soup.find_all('td'))
        raw_coords = re.findall(r"\d\d\.\d\d* x \d\d\.\d\d*", coord_section)

        top_left = raw_coords[0].split(" x ")
        bottom_right = raw_coords[1].split(" x ")

        return top_left, bottom_right

    def __repr__(self):
        return "url: {}, title: {}, TopLeft: {}, BottomRight: {}"\
            .format(self.url, self.title, self.top_left, self.bottom_right)


if __name__ == "__main__":
    print(pull_info())
