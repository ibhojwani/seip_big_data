
# create a cluster
gcloud dataproc clusters create finding-stars --num-workers 25  --worker-machine-type n1-standard-4 --master-machine-type n1-standard-4


# submit spark job - doesn't really work well, need to capture output better
#gcloud dataproc jobs submit pyspark --cluster=finding-stars src/outliers.py -- gs://astro-data/merged_seip.csv 2 gs://astro-data/clustered_points


# run algorithm 1
time python3 src/edgesanddistance.py --cluster-id=finding-stars -r dataproc outlier_points.csv > algo1results.csv


# run algorithm 2

#python3  src/group_objects.py --cluster-id=finding-stars -r gs://astro-data/merged_seip.csv  > algo2results.csv


# delete the cluster

gcloud dataproc clusters delete finding-stars
