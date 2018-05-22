import csv
import os
from time import sleep
from requests import get
from astroquery.irsa import Irsa
from xml.etree import ElementTree

# Base query
BASE = "https://irsa.ipac.caltech.edu/TAP/async?QUERY=SELECT+{}+FROM+{}+WHERE+CONTAINS(POINT('J2000',ra,dec),POLYGON('J2000',{}))=1&FORMAT=CSV&PHASE=RUN"

# Columns to pull
columns = ["ra",
           "dec",
           "l",
           "b",
           "i1_f_ap1_bf",
           "i2_f_ap1_bf",
           "i3_f_ap1_bf",
           "i4_f_ap1_bf",
           "m1_f_ap_bf",
           "i1_snr",
           "i2_snr",
           "i3_snr",
           "i4_snr",
           "m1_snr",
           "objid"
           ]


def get_data(ra_num, dec_num, out_dir, catalog="allwise_p3as_psd", debug=0):
    '''
    Downloads point source data from IRSA SEIP database.
    Rough estimates (size vs rows):
        size 25 -> 1 mil rows
        size 20 -> 700k rows
        size 10 -> 500k rows
    Inputs:
        ra_num: int, num partitions of right ascension
        dec_num: int, num partitions of declination
        catalog: string, IRSA catalog to query from
        out_dir: string, directory name to save files to
        debug: int, reduces num queries to given number. 0 includes all.
    Returns None, but writes to files in out_dir.
    '''
    assert (ra_num > 0) and (dec_num > 0), "Error: Partition count must be > 0"
    col_query = ",".join(columns)
    poly_list = build_polygons(ra_num, dec_num)
    if debug:
        lower = (len(poly_list) // 2) - (debug // 2)
        upper = (len(poly_list) // 2) + (debug // 2)
        poly_list = poly_list[lower:upper]
    status_list = init_queries(poly_list, catalog)

    # Periodically check if query is done
    num_done = 0
    completion_msgs = ["COMPLETD", "ERROR", "ABORTED"]
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    num_queries = len(poly_list)

    while num_done < num_queries:
        print("Working...")
        for i, query in enumerate(status_list):
            # continue if already processed result
            if query[1] in completion_msgs:
                continue

            # Otherwise, dwnld if complete, print if error or aborted
            status = ElementTree.fromstring(get(query[0]).content)[2].text
            if status == "COMPLETED":
                result = get(query[0] + "/results/result", stream=True)
                with open("{}/{}.csv".format(out_dir, str(poly_list[0])), "wb") as f:
                    for block in result.iter_content(1024):
                        f.write(block)
                num_done += 1
                query[1] = status
                continue

            elif status == "ERROR":
                print("ERROR with query {}".format(poly_list[i]))
                num_done += 1
                query[1] = status
                continue

            elif status == "ABORTED":
                print("ABORTED with query {}".format(poly_list[i]))
                num_done += 1
                query[1] = status
                continue

        print("Processed {}/{}".format(num_done, num_queries))
        sleep(4)


def build_polygons(ra_num, dec_num):
    '''
    Builds a list of boxes which cover the whole sky to run queries on.
    Inputs:
        ra_num: int, num boxes to divide right ascension into
        dec_num: int, num boxes to divide declination into
    Returns: list of tuples -- ("J2000", center ra, center dec, width, height).
        Width and height are in decimal degrees, "J2000" is coord system.

    Ex. ra_div = 10, dec_div = 10 would return 100 boxes, each 36x36 degrees.
    '''
    poly_list = []
    # bounds of ra and dec
    RA_BDS = (0, 360)
    DEC_BDS = (-90, 90)
    # Get box dimensions
    ra_size = (RA_BDS[1] - RA_BDS[0]) / ra_num
    dec_size = (DEC_BDS[1] - DEC_BDS[0]) / dec_num

    for d in range(dec_num):
        for r in range(ra_num):
            bot_left = (RA_BDS[0] + r * ra_size, DEC_BDS[0] + d * dec_size)
            bot_right = (bot_left[0] + ra_size, bot_left[1])
            top_left = (bot_left[0], bot_left[1] + dec_size)
            top_right = (bot_right[0], bot_right[1] + dec_size)
            poly_list.append([bot_left, bot_right, top_left, top_right])

    return poly_list


def init_queries(poly_list, catalog):
    '''
    Initializes the queries from IRSA so they can be processed
    simultaneously.
    Inputs:
        poly_list: List of sky box partitions
        catalog: catalog ID to be pulled from
            ALLWISE ID: allwise_p3as_psd
            SEIP ID: slphotdr4
    Returns list of tuples containing url's of query status pages and
        their most recent status update.
    '''
    status_list = []
    replaces = [" ", "(", ")", "[", "]"]

    for poly in poly_list:
        poly_str = str(poly)
        for char in replaces:
            poly_str = poly_str.replace(char, "")

        query = BASE.format("*", catalog, poly_str)
        print(query)
        info_xml_url = get(query, stream=True).url  # It redirects to info XML
        info_xml = ElementTree.fromstring(get(info_xml_url).content)
        status = info_xml[2].text
        status_list.append([info_xml_url, status])

    return status_list
# ",".join(columns)
