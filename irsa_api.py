import csv
import os
from time import sleep
from requests import get
from astroquery.irsa import Irsa
from xml.etree import ElementTree

# Base query
BASE = "https://irsa.ipac.caltech.edu/TAP/async?QUERY=SELECT+{}+FROM+{}+WHERE+{}&FORMAT=CSV&PHASE=RUN"

# Columns to pull
columns = ["designation",
           "ra",
           "dec",
           "w1mpro",
           "w2mpro",
           "w3mpro",
           "w4mpro",
           "w1snr",
           "w2snr",
           "w3snr",
           "w4snr"]


def get_data(num_bins, min_snr, out_dir, catalog="allwise_p3as_psd", debug=0):
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
    assert (num_bins > 0) and (
        min_snr > 0), "Error: Partition count must be > 0"
    where_list = build_slices(num_bins, min_snr)
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
            try:
                status = ElementTree.fromstring(get(query[0]).content)[2].text
            except:
                print("Warning... connection dropped")
                continue
            if status == "COMPLETED":
                with get(query[0] + "/results/result", stream=True) as result:
                    with open("{}/{}.csv".format(out_dir, str(i)), "wb") as f:
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
        sleep(10)


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
    col_query = ",".join(columns)

    for where in where_list:
        query = BASE.format(col_query, catalog, where)
        print(query)
        info_xml_url = get(query).url  # It redirects to info XML
        print("hahahaha", info_xml_url)
        info_xml = ElementTree.fromstring(get(info_xml_url).content)
        status = info_xml[2].text
        status_list.append([info_xml_url, status])
    return status_list


def build_slices(num_bins, min_snr):
    '''
    Builds a list of boxes which cover the whole sky to run queries on.
    Inputs:
        ra_num: int, num boxes to divide right ascension into
        dec_num: int, num boxes to divide declination into
    Returns: list of tuples -- ("J2000", center ra, center dec, width, height).
        Width and height are in decimal degrees, "J2000" is coord system.

    Ex. ra_div = 10, dec_div = 10 would return 100 boxes, each 36x36 degrees.
    '''
    RA_BDS = (0, 360)
    slice_list = [RA_BDS[0]]
    ra_size = (RA_BDS[1] - RA_BDS[0]) / num_bins

    for r in range(num_bins):
        slice_list.append(round(slice_list[-1] + ra_size, 3))
    channels = ["w1", "w2", "w3", "w4"]
    snr_template = "{}snr>={}"
    snr_list = []
    for channel in channels:
        snr_list.append(snr_template.format(channel, min_snr))
    snr_query = "+AND+".join(snr_list)

    ra_list = []
    ra_template = "ra>={}+AND+ra<{}"
    for i, ra in enumerate(slice_list):
        if i < len(slice_list) - 1:
            ra_list.append(ra_template.format(ra, slice_list[i + 1]))

    other_constr = "+AND+cc_flags='0000'+AND+"
    where_list = [snr_query + other_constr + ra_query for ra_query in ra_list]

    return where_list
