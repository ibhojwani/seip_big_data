# bash to run mrjobs

# get mean

echo Finding mean...

python3 get_recommendation.py --jobconf mapreduce.job.reduces=1 data/experimental/400k.csv > centres.csv

# get standard deviation and add to same file as means

echo Finding standard deviation...

python3 get_sd.py --jobconf mapreduce.job.reduces=1 data/experimental/400k.csv >> centres.csv

# get outliers

echo Finding outliers...

python3 get_outliers.py --jobconf mapreduce.job.reduces=1 data/experimental/400k.csv > outliers.csv

echo NUMBER OF OUTLIERS FOUND: 

wc  -l outliers.csv