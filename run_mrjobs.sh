# bash to run mrjobs

# get mean

python3 get_recommendation.py --jobconf mapreduce.job.reduces=1 data/experimental/400k.csv > centres.csv

# get standard deviation and add to same file as means

python3 get_sd.py --jobconf mapreduce.job.reduces=1 data/experimental/400k.csv >> centres.csv

# get outliers

python3 get_outliers.py --jobconf mapreduce.job.reduces=1 data/experimental/400k.csv > outliers.csv

