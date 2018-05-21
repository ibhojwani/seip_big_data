from requests import get
import csv
from astroquery.irsa import Irsa

DATA_URL = "https://irsa.ipac.caltech.edu/TAP/sync?QUERY=SELECT+{0}+FROM+slphotdr4+WHERE+CONTAINS(POINT('J2000',ra,dec),CIRCLE('J2000',66.76957,26.10453,{1}))=1&FORMAT=CSV"
WGET = "https://irsa.ipac.caltech.edu/TAP/sync?QUERY=SELECT+*+FROM+slphotdr4+WHERE+CONTAINS(POINT('J2000',ra,dec),CIRCLE('J2000',66.76957,26.10453,1))=1&FORMAT=CSV"

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
    col_query = ",".join(columns)
    query = DATA_URL.format(col_query, size)
    print(query)
    download = get(query, stream=True)

    with open(target, "wb") as f:
        for block in download.iter_content(1024):
            f.write(block)
