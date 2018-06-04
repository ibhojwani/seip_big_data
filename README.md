# TBD ALLWISE YSO Search
Created by Ishaan Bhojwani, Tyler Amos, Kevin Sun, and Alexander Tyan.

## Summary
This project provides two algorithms for finding Young Stellar Object (YSO) candidates in the ALLWISE all sky catalog. Both algorithms heavily utilize MRJob for distribution of computation. Used in both are custom made k-means and standard deviation MRJob implementations.

The first algorithm less effectively and less efficiently finds YSO candidates by searching for color outliers and drawing edges between a selection of them. It then fits a spline to the distances between these edges and draws conclusions on clusters from there. 

The second algorithm finds clusters by binning stars according to ra and dec, and performing a random walk within bins to find dense regions. It then filters for the densest regions with a thresholding algorithm. It then filters for color outliers within these clusters. The second algorithm should be treated as the most effective and has most potential to be applied to other datasets and fine tuned to provide the best results.


## How To Run
### Algorithm 1
    >>> python3 alg_1.py input_file > outfile

### Algorithm 2
    >>> python3 alg_2.py input_file > outfile


## Directory Structure
- src/ 
  - alg_1.py
    - Main file for algorithm 1. 
  - alg_1_util.py
    - Helper functions for algorithm 1
  - alg_2.py
    - Main file for algorithm 2
  - alg_2_util.py
    - Helper functions for algorithm 2
  - astro_object.py
    - AstroObject class, used to store information for astronomical objects and provide methods which are useful for analysing and processing them
  - irsa_api.py
    - Code for downloading data from the IRSA database. Queries generally take several hours, so provides framework to init query on database, go offline, and download completed results later.
  - kmeans.py
    - MRJob implementation of k-means algorithm.
  - stdev.py
    - MRJob implementation of standard deviation calculation
- data
    - contains a few small sample data files
- scripts/
  - useful scripts we used
- presentation/
  - contains files used to build final presentation.
- .configs.conf
  - dataproc config file
- requirements.txt
  - python package requirements.
- .gitignore

#
University of Chicago

CMSC 12300 Spring 2018

Dr. Matthew Wachs

Submitted as the result of a quarter long project in fulfillment of the
class requirements.