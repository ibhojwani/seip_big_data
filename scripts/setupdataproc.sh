# set up script for running on dataproc
export MRJOB_CONF=.mrjob_conf
export GOOGLE_CLOUD_DATAPROC= location of the permission json

python3 edgesandistance.py -r dataproc test_csv.csv
