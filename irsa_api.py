import csv
from time import sleep
from requests import get
from astroquery.irsa import Irsa
from xml.etree import ElementTree

DATA_URL = "https://irsa.ipac.caltech.edu/TAP/async?QUERY=SELECT+{0}+FROM+slphotdr4+WHERE+CONTAINS(POINT('J2000',ra,dec),CIRCLE('J2000',66.76957,26.10453,{1}))=1&FORMAT=CSV&PHASE=RUN"
WGET = "https://irsa.ipac.caltech.edu/TAP/sync?QUERY=SELECT+*+FROM+slphotdr4+WHERE+CONTAINS(POINT('J2000',ra,dec),CIRCLE('J2000',66.76957,26.10453,1))=1&FORMAT=CSV"
ALL_SKY = "https://irsa.ipac.caltech.edu/TAP/sync?QUERY=SELECT+{0}+FROM+slphotdr4FORMAT=CSV&PHASE=RUN"
columns = [
    "ra",
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


def get_data(size, target):
    '''
    25 = 1.06 mil
    10 = 400k
    '''
    assert (size >= 0), "Error: Size must be greater than 0"
    col_query = ",".join(columns)
    query = DATA_URL.format(col_query, size)
    print(query)

    # Wait until API finishes the query
    redirect = get(query, stream=True).url  # It redirects to info XML
    info_tree = ElementTree.fromstring(get(redirect).content)
    result_url = redirect + "/results/result"
    status = info_tree[2].text

    # Periodically check if query is done
    while (status == "EXECUTING") or (status == "QUEUED"):
        print("Working...")
        sleep(10)
        status = ElementTree.fromstring(get(redirect).content)[2].text

    # Catch errors in query
    if status == "ERROR":
        result_tree = ElementTree.fromstring(get(result_url).content)
        raise Exception(
            "Query returned error: {}".format(result_tree[-1].text))
    assert status != "ABORT", "Query was aborted"

    # Write to file
    print('Writing...')
    result = get(result_url, stream=True)
    with open(target, "wb") as f:
        for block in result.iter_content(1024):
            f.write(block)

    size = result.headers["Content-length"]
    print("Successfully downloaded {} MB".format(int(size)/1000000))
