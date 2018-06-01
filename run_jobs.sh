# set up environment vars
#export MRJOB_CONF=.mrjob.conf


# Not the actual name of the variable - make sure you check
#export GOOGLE_CLOUD_DATAPROC=permission json


# create a cluster
#gcloud dataproc clusters create star-finder --num-workers 25  --worker-machine-type n1-standard-4 --master-machine-type n1-standard-4


# submit spark job - doesn't really work well, need to capture output better
#gcloud dataproc jobs submit pyspark --cluster=finding-stars src/outliers.py -- gs://astro-data/merged_seip.csv 2 gs://astro-data/clustered_points


# run algorithm 1
time python3 edgesanddistance.py -r dataproc outlier_points.csv > algo1results.csv

# run algorithm 2

#time python3  src/group_objects.py -r dataproc test.csv  > algo2results.csv
#--setup 'sudo apt-get install python3-pip -y' --setup 'pip3 install numpy'\
# --setup 'pip3 install scipy'\
# --num-core-instances 25  --core-instance-type n1-standard-4 --instance-type n1-standard-4


# delete the cluster

#gcloud dataproc clusters delete star-finder -Y
