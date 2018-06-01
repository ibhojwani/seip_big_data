# set up script for running on dataproc
export MRJOB_CONF=.mrjob_conf

# Not the actual name of the variable - make sure you check
export GOOGLE_CLOUD_DATAPROC= location of the permission json

python3 edgesandistance.py -r dataproc test_csv.csv


time python3 edgesanddistance.py  -r dataproc test_csv.csv  > output.txt
  --num-core-instances 7  --core-instance-type n1-highcpu-8 --instance-type n1-highcpu-8


  --output-dir=gs://foundstartsalgo1 --no-output