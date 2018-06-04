#### USAGE: bash run_jobs.sh [name of your permissions file]


# set up environment vars
export MRJOB_CONF=configs.conf


# your permissions json should be here
export GOOGLE_APPLICATION_CREDENTIALS=$1 # 


# create a cluster
gcloud dataproc clusters create star-finder #--num-workers 25  --worker-machine-type n1-standard-4 --master-machine-type n1-standard-4


# submit spark job - used for an earlier iteration of algorithm 1
#gcloud dataproc jobs submit pyspark --cluster=finding-stars src/outliers.py -- gs://astro-data/merged_seip.csv 2 gs://astro-data/clustered_points


# run algorithm 1
time python3 src/obsolete/edgesanddistance.py -r dataproc --cluster-id=star-finder test.csv > algo1results.csv 
--num-core-instances 25  --core-instance-type n1-standard-4 --instance-type n1-standard-4
--file src/astro_object.py  --file src/kmeans.py \
--file src/alg_2.py --file src/stdev.py --file src/alg_2_util.py --file src/alg_1_util.py \
--file src/astro_object.py \
 --bootstrap-python --bootstrap-script=scripts/bootstrap.sh

# run algorithm 2

time python3  src/group_objects.py -r dataproc \
 --cluster-id=star-finder test.csv  > algo2results.csv \
--file src/astro_object.py  --file src/kmeans.py \
--file src/alg_2.py --file src/stdev.py --file src/alg_2_util.py --file src/alg_1_util.py \
--file src/astro_object.py \
 --bootstrap-python --bootstrap-script=bootstrap.sh

# delete the cluster

gcloud dataproc clusters delete star-finder 
