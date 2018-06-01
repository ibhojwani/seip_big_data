# set up environment vars
export MRJOB_CONF=.mrjob.conf


# your permissions json should be here
export GOOGLE_APPLICATION_CREDENTIALS=$1 # 


# create a cluster
#gcloud dataproc clusters create star-finder --num-workers 25  --worker-machine-type n1-standard-4 --master-machine-type n1-standard-4


# submit spark job - doesn't really work well, need to capture output better
#gcloud dataproc jobs submit pyspark --cluster=finding-stars src/outliers.py -- gs://astro-data/merged_seip.csv 2 gs://astro-data/clustered_points


# run algorithm 1
#time python3 src/edgesanddistance.py -r dataproc --cluster-id=star-finder outlier_points.csv > algo1results.csv \
#--num-core-instances 25  --core-instance-type n1-standard-4 --instance-type n1-standard-4

# run algorithm 2

# zip python class files 

#zip astro.zip src/astro_object.py src/random_walk.py

time python3  src/group_objects.py -r dataproc \
 --cluster-id=star-finder test.csv  > algo2results.csv \
#--num-core-instances 25  --core-instance-type n1-standard-4 --instance-type n1-standard-4 
--py-file src/astro.zip 

# delete the cluster

#gcloud dataproc clusters delete star-finder 
