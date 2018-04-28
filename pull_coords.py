'''
'''

import re
from requests import get
from bs4 import BeautifulSoup


STARTING_URL = "http://www.unitar.org/unosat/maps/SYR"


def pull_info():
    '''
    Build a list of dmg report objects w/ coords.
    '''
    initial_soup = BeautifulSoup(get(STARTING_URL).content(), "html.parser")
    link_list = initial_soup.find_all("a")
    damage_assessments = []

    for lnk in link_list:
        if lnk.contents and ("damage" in lnk.contents[0].lower()):
            dmg_assess = DamageAssessment(lnk["href"])

            if dmg_assess.top_left:
                damage_assessments.append(dmg_assess)

    return damage_assessments


class DamageAssessment(object):

    def __init__(self, url):
        self.url = url
        self.soup = BeautifulSoup(get(url).content(), "html.parser")
        self.title = self.soup.title
        self.top_left, self.bottom_right = self.get_coords()

    def get_coords(self):
        '''
        Pulls top le ft and bottom right coords from page.
        '''
        coords = re.findall(r"\d\d\.\d\d\d\d\d\d\d", str(self.soup))

        if len(coords) > 4:
            print("less found at {}".format(self.url))
            return None, None
        if len(coords) > 4:
            print("more found at {}".format(self.url))
            return None, None

        top_left = coords[:2]
        bottom_right = coords[2:]

        return top_left, bottom_right

    def __repr__(self):
        return "url: {}, title: {}, TopLeft: {}, BottomRight: {}"\
            .format(self.url, self.title, self.top_left, self.bottom_right)


if __name__ == "__main__":
    print(pull_info())
