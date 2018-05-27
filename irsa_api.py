'''
CMSC 12300 Spr 2018
TBD

This file provides tools to pull from the IRSA databse. While it is
currently only compatible with the ALLWISE source catalog, the only 
barrier to this is the 'columns' variable being fixed, rather
than a parameter. It splits the sky into 'vertical strips,' downloading
data in chunks between 2 right ascension values, while filtering for
image confidence, signal to noise (snr), and ALLWISE movement
estimations.

It is advisable to download in 2 steps, using get_data() and
monitor_queries() in succession, rather than using the main() function.
This generally results in fewer errors due to the IRSA API's limits.
'''

import csv
import os
import sys
import pandas as pd
from time import sleep
from requests import get
from xml.etree import ElementTree

# Base query
BASE = "https://irsa.ipac.caltech.edu/TAP/async?QUERY=SELECT+{}+FROM+{}+WHERE+{}&FORMAT=CSV&PHASE=RUN"

# Columns to pull
columns = ["designation",
           "ra_pm",
           "dec_pm",
           "sigra_pm",
           "sigdec_pm",
           "pmra",
           "pmdec",
           "sigpmra",
           "sigpmdec",
           "w1mpro",
           "w2mpro",
           "w3mpro",
           "w4mpro",
           "w1snr",
           "w2snr",
           "w3snr",
           "w4snr"]


def get_data(num_bins, min_snr, out_dir, restart=False, catalog="allwise_p3as_psd", debug=0, init=0):
    '''
    Queries IRSA database with requested params. By default, actively 
    monitors for results and writes results to out_dir, however this can
    be used to only initialize queries, which is useful for testing as
    queries can last hours.
    Inputs:
        num_bins: int, num slices to create (36 recommended, 360 fails)
        min_snr: int, minimum snr in all 4 channels
        out_dir: str, directory to store data in
        restart: bool, True if restarting queries in out_dir/restart.csv
        catalog: str, ident of catalog to search
        debug: int, debug > 0 means only request subset, len(sub)~debug
        init: bool, True if only being used to initialize queries. Lets
            user init queries and then manually start monitoring later.
    Returns status_list, a list of dicts w/ query text, status page, and
        current status
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
        query_list = read_log(out_dir, "restart.csv", True)
        status_list = init_queries(query_list, out_dir)

    if init:
        return status_list

    restart_list = monitor_queries(out_dir)

    create_log(out_dir, "restart.csv", restart_list)
    return restart_list


def processing(idx, num_done, num_queries, waiting):
    '''
    Simple loading animation.
    '''
    monit = "Monitoring queries {}/{}".format(num_done, num_queries)
    print(monit, waiting[idx % len(waiting)], end="\r")
    return idx + 1


def init_queries(query_list, out_dir):
    '''
    Initializes queries. Writes results to log file.
    Inputs:
        query_list: list of queries to send
        out_dir: str, directory for log file to go in
    Returns list of dicts w/ info on queries (also writes this to log).
        Dict contains status, url of status page, and query text
    '''
    status_list = []
    for query in query_list:
        info_xml_url = get(query).url  # It redirects to info XML
        info_xml = ElementTree.fromstring(get(info_xml_url).content)
        # Store info page, current status, and query
        temp_dict = {"info": info_xml_url, "status": "QUEUED", "query": query}
        status_list.append(temp_dict)

    create_log(out_dir, "query_log.csv", status_list)

    return status_list


def build_queries(num_bins, min_snr, catalog):
    '''
    Builds queries to get data from IRSA. Breaks the sky into a set of
    vertical strips and searches for objects within the strip with
    signal to noise ratio above min_snr in all 4 channels.
    Inputs:
        num_bins: int, num strips to cut sky into
        min_snr: float, minumum signal to noise ratio in all 4 channels
        catalog: str, catalog to query
    Returns list of query strings.
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

    other_constr = "+AND+cc_flags='0000'+AND+ra_pm+IS+NOT+NULL+AND+dec_pm+IS+"\
        + "NOT+NULL+AND+pmra+IS+NOT+NULL+AND+pmdec+IS+NOT+NULL+AND+"
    where_list = [snr_query + other_constr + ra_query for ra_query in ra_list]

    # Put together final queries
    col_query = ",".join(columns)
    query_list = []
    for where in where_list:
        query_list.append(BASE.format(col_query, catalog, where))

    return query_list


def monitor_queries(out_dir):
    '''
    Monitors queries already being processed, downloading them to file
    when detected. Allows user to initialize queries and monitor them
    in separate steps.
    Inputs:
        out_dir: str, directory to download to and read query info from
    Returns list of dicts of failed queries to be restarted, w/ each
        dict containing status page url, current status, and query text.
    '''
    status_list = read_log(out_dir, "query_log.csv", False)
    done_flags = ["COMPLETED", "ERROR", "ABORTED"]
    num_done = 0
    num_queries = len(status_list)
    waiting = "|/-\\"
    idx = 0
    restart_list = []

    while num_done < num_queries:
        for i, query in enumerate(status_list):
            idx = processing(idx, num_done, num_queries, waiting)

            # If already done, continue to next
            if query['status'] in done_flags:
                continue

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
                    with open("{}/{}.csv".format(out_dir, query['info'][-7:]), "wb") as f:
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

        idx = processing(idx, num_done, num_queries, waiting)
        sleep(1)

    return restart_list


def create_log(out_dir, filename, data):
    '''
    Helper function to write csv log files.
    Inputs:
        out_dir: str, name of output directory
        filename: str, name of log file to create
        data: list of dicts with info to write
    Returns None, but writes to out_dir/filename.csv
    '''
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    df = pd.DataFrame.from_records(data)  # TODO
    df.to_csv(out_dir + "/" + filename, index=False)
    return None


def read_log(out_dir, logfile, queries):
    '''
    Helper function to read log files generated by create_log().
    Inputs:
        out_dir: str, name of directory containing log file
        filename: str, name of log file to read
        queries: bool, True if output should be processed only return
            query text.
    Returns list of dicts, or list of strings if queries
    '''
    with open(out_dir + "/" + logfile, "r") as f:
        dict_list = [{k: v for k, v in row.items()}
                     for row in csv.DictReader(f, skipinitialspace=True)]
    if not queries:
        return dict_list

    query_list = []
    for status_dict in dict_list:
        query_list.append(status_dict['query'])
    return query_list


def main(num_bins, min_snr, out_dir, cat="allwise_p3as_psd", debug=0, restarts=0):
    '''
    Queries and downloads data from IRSA database with given params.
    Inputs:
        num_bins: int, num slices to create (36 recommended, 360 fails)
        min_snr: int, minimum snr in all 4 channels
        out_dir: str, directory to store data in
        cat: str, ident of catalog to search
        debug: int, debug > 0 means only request subset, len(sub)~debug
        restarts: int, num times to retry failed queries
    Returns bool, True if no failed queries by end.

    '''
    restart = get_data(num_bins, min_snr, out_dir,
                       catalog=cat, debug=debug)
    if not restart:
        return True
    for i in range(restarts):
        restart = get_data(num_bins, min_snr, out_dir,
                           catalog=cat, debug=debug, restart=True)
        if not restart:
            return True
    return not bool(restart)
