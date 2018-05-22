import csv
import os
from time import sleep
from requests import get
from astroquery.irsa import Irsa
from xml.etree import ElementTree

# Base query
BASE = "https://irsa.ipac.caltech.edu/TAP/async?QUERY=SELECT+{}+FROM+{}+WHERE+{}&FORMAT=CSV&PHASE=RUN"

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


def get_data(num_bins, min_snr, top_div, out_dir, catalog="allwise_p3as_psd", debug=0):
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
    # assert (ra_num > 0) and (dec_num > 0), "Error: Partition count must be > 0"
    col_query = ",".join(columns)
    where_list = build_snr_bins(num_bins, min_snr, top_div)
    if debug:
        lower = (len(where_list) // 2) - (debug // 2)
        upper = (len(where_list) // 2) + (debug // 2)
        where_list = where_list[lower:upper]
    status_list = init_queries(where_list, catalog)

    # Periodically check if query is done
    num_done = 0
    completion_msgs = ["COMPLETED", "ERROR", "ABORTED"]
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    num_queries = len(where_list)

    while num_done < num_queries:
        print("Working...")
        for i, query in enumerate(status_list):
            # continue if already processed result
            if query[1] in completion_msgs:
                continue
            # Otherwise, dwnld if complete, print if error or aborted
            status = ElementTree.fromstring(get(query[0]).content)[2].text
            print(status)
            if status == "COMPLETED":
                result = get(query[0] + "/results/result", stream=True)
                with open("{}/{}.csv".format(out_dir, str(where_list[i])), "wb") as f:
                    for block in result.iter_content(1024):
                        f.write(block)
                num_done += 1
                query[1] = status
                continue

            elif status == "ERROR":
                print("ERROR with query {}".format(where_list[i]))
                num_done += 1
                query[1] = status
                continue

            elif status == "ABORTED":
                print("ABORTED with query {}".format(where_list[i]))
                num_done += 1
                query[1] = status
                continue

        print("Processed {}/{}".format(num_done, num_queries))
        sleep(4)


def build_snr_bins(num_bins, min_snr, top_div):
    assert top_div >= min_snr, "top_div must be >= min_snr"
    bin_list = [min_snr]
    step = round((top_div - min_snr) / (num_bins - 1), 3)
    for i in range(num_bins - 1):
        bin_list.append(bin_list[-1] + step)

    channels = ["w1", "w2", "w3", "w4"]
    where_template = "{}snr>={}+AND+{}snr<{}"
    where_list = []

    for i, snr in enumerate(bin_list):
        where = []
        if i < len(bin_list) - 1:
            snr_2 = bin_list[i + 1]
            for channel in channels:
                where.append(where_template.format(
                    channel, snr, channel, snr_2))
        else:
            for channel in channels:
                where.append("{}>={}".format(channel, snr))

        where_list.append("+AND+".join(where))

    return where_list


def init_queries(where_list, catalog):
    '''
    Initializes the queries from IRSA so they can be processed
    simultaneously.
    Inputs:
        bin_list: list of snr partitions
        catalog: catalog ID to be pulled from
            ALLWISE ID: allwise_p3as_psd
            SEIP ID: slphotdr4
    Returns list of tuples containing url's of query status pages and
        their most recent status update.
    '''
    status_list = []

    for snr in where_list:
        query = BASE.format("*", catalog, snr)
        print(query)
        info_xml_url = get(query, stream=True).url  # It redirects to info XML
        info_xml = ElementTree.fromstring(get(info_xml_url).content)
        status = info_xml[2].text
        status_list.append([info_xml_url, status])

    return status_list
# ",".join(columns)

############## OBSOLETE BUT KEPT AROUND JUST IN CASE ################


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
