import csv
import os
import sys
import pandas as pd
from time import sleep
from requests import get
from xml.etree import ElementTree
# TODO change name of .csv so restarts can work
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


def get_data(num_bins, min_snr, out_dir, restart=False, catalog="allwise_p3as_psd", debug=0):
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

    if not restart:
        # Build and init queries. If debug, use a subset.
        query_list = build_queries(num_bins, min_snr, catalog)
        if debug:
            lower = (len(query_list) // 2) - (debug // 2)
            upper = (len(query_list) // 2) + (debug // 2)
            query_list = query_list[lower:upper]
        status_list = init_queries(query_list, out_dir)

    # If being used to restart failed queries, do as above but from csv
    else:
        with open(out_dir + "/" + "restart.csv", "r") as f:
            dict_list = [{k: v for k, v in row.items()}
                         for row in csv.DictReader(f, skipinitialspace=True)]
        query_list = []
        for status_dict in dict_list:
            query_list.append(status_dict['query'])
        status_list = init_queries(query_list, out_dir)

    # Periodically check if query is done
    num_done = 0
    num_queries = len(status_list)
    waiting = "|/-\\"
    idx = 0
    restart_list = []

    while num_done < num_queries:
        for i, query in enumerate(status_list):
            idx = processing(idx, num_done, num_queries, waiting)

            # Otherwise, get update on progress
            try:
                status = ElementTree.fromstring(
                    get(query['info']).content)[2].text
            except:
                print("Warning... cannot connect. Added to restart list.")
                query["status"] = status
                restart_list.append(query)
                continue

            # If completed, write to file.
            if status == "COMPLETED":
                with get(query['info'] + "/results/result", stream=True) as result:
                    with open("{}/{}.csv".format(out_dir, str(i)), "wb") as f:
                        for block in result.iter_content(1024):
                            f.write(block)
                num_done += 1
                query["status"] = status
                continue

            # Deal with error conditions
            elif status == "ERROR":
                print("ERROR. Adding to restarts: {}".format(query['info']))
                num_done += 1
                query["status"] = status
                restart_list.append(query)
                continue

            elif status == "ABORTED":
                print("ABORTED. Added to restarts: {}".format(query['info']))
                num_done += 1
                query["status"] = status
                restart_list.append(query)
                continue
        # for i in range(10):
        #     idx = processing(idx, num_done, num_queries, waiting)
        #     sleep(1)
        sleep(1)

    create_log(out_dir, "restart.csv", restart_list)

    return restart_list


def processing(idx, num_done, num_queries, waiting):
    monit = "Monitoring queries {}/{}".format(num_done, num_queries)
    print(monit, waiting[idx % len(waiting)], end="\r")
    return idx + 1


def init_queries(query_list, out_dir):
    '''
    Initializes the queries from IRSA so they can be processed
    simultaneously.
    Inputs:
        bin_list: list of snr partitions
        catalog: str, catalog ID to be pulled from
            ALLWISE ID: allwise_p3as_psd
            SEIP ID: slphotdr4
        out_dir: str, directory for log file to go in
    Returns list of tuples containing url's of query status pages and
        their most recent status update.
    '''

    status_list = []
    for query in query_list:
        info_xml_url = get(query).url  # It redirects to info XML
        info_xml = ElementTree.fromstring(get(info_xml_url).content)
        status = info_xml[2].text
        # Store info page, current status, and query
        temp_dict = {"info": info_xml_url, "status": status, "query": query}
        status_list.append(temp_dict)

    create_log(out_dir, "query_log.csv", status_list)

    return status_list


def build_queries(num_bins, min_snr, catalog):
    '''
    Builds a list of boxes which cover the whole sky to run queries on.
    Inputs:
        ra_num: int, num boxes to divide right ascension into
        dec_num: int, num boxes to divide declination into
    Returns: list of tuples -- ("J2000", center ra, center dec, width, height).
        Width and height are in decimal degrees, "J2000" is coord system.

    Ex. ra_div = 10, dec_div = 10 would return 100 boxes, each 36x36 degrees.
    '''
    # Create ra slices
    RA_BDS = (0, 360)
    slice_list = [RA_BDS[0]]
    ra_size = (RA_BDS[1] - RA_BDS[0]) / num_bins
    for r in range(num_bins):
        slice_list.append(round(slice_list[-1] + ra_size, 3))

    # Create snr portion of query
    channels = ["w1", "w2", "w3", "w4"]
    snr_template = "{}snr>={}"
    snr_list = []
    for channel in channels:
        snr_list.append(snr_template.format(channel, min_snr))
    snr_query = "+AND+".join(snr_list)

    # Create ra portion of query from slices, and combine with snr
    ra_list = []
    ra_template = "ra>={}+AND+ra<{}"
    for i, ra in enumerate(slice_list):
        if i < len(slice_list) - 1:
            ra_list.append(ra_template.format(ra, slice_list[i + 1]))

    other_constr = "+AND+cc_flags='0000'+AND+"
    where_list = [snr_query + other_constr + ra_query for ra_query in ra_list]

    # Put together final queries
    col_query = ",".join(columns)
    query_list = []
    for where in where_list:
        query_list.append(BASE.format(col_query, catalog, where))

    return query_list


def create_log(out_dir, filename, data):
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    df = pd.DataFrame.from_records(data)  # TODO
    df.to_csv(out_dir + "/" + filename, index=False)
    return None


def main(num_bins, min_snr, out_dir, cat="allwise_p3as_psd", debug=0, restarts=0):
    restart = get_data(num_bins, min_snr, out_dir, catalog=cat, debug=debug)
    if not restart:
        return True
    for i in range(restarts):
        restart = get_data(num_bins, min_snr, out_dir,
                           catalog=cat, debug=debug, restart=True)
        if not restart:
            return True
    return not bool(restart)
