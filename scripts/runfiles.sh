# this is an example of the script we used to divide our data
# and run each portion locally across all our machines

sed -n '1,100000p;200001q' sasha.csv > test.csv

python3 src/alg_2.py test.csv > sasha_alg2.csv

sed -n '100001,200000p;200001q' sasha.csv > test.csv

python3 src/alg_2.py test.csv >> sasha_alg2.csv

sed -n '200001,300000p;300001q' sasha.csv > test.csv

python3 src/alg_2.py test.csv >> sasha_alg2.csv

sed -n '300001,400000p;400001q' sasha.csv > test.csv

python3 src/alg_2.py test.csv >> sasha_alg2.csv

sed -n '400001,500000p;500001q' sasha.csv > test.csv

python3 src/alg_2.py test.csv >> sasha_alg2.csv


sed -n '500001,600000p;600001q' sasha.csv > test.csv

python3 src/alg_2.py test.csv >> sasha_alg2.csv


sed -n '600001,700000p;700001q' sasha.csv > test.csv

python3 src/alg_2.py test.csv >> sasha_alg2.csv


sed -n '700001,800000p;800001q' sasha.csv > test.csv

python3 src/alg_2.py test.csv >> sasha_alg2.csv



sed -n '800001,900000p;900001q' sasha.csv > test.csv
python3 src/alg_2.py test.csv >> sasha_alg2.csv



sed -n '900001,1000000p;1000001q' sasha.csv > test.csv
python3 src/alg_2.py test.csv >> sasha_alg2.csv


