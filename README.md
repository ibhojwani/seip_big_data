# TBD ALLWISE YSO Search
Created by Ishaan Bhojwani, Tyler Amos, Kevin Sun, and Alexander Tyan.

This project provides two algorithms for finding Young Stellar Object (YSO) candidates in the ALLWISE all sky catalog. Both algorithms heavily utilize MRJob for distribution of computation. Used in both are custom made k-means and standard deviation MRJob implementations.

The first algorithm less effectively and less efficiently finds YSO candidates by searching for color outliers and drawing edges between a selection of them. It then fits a spline to the distances between these edges and draws conclusions on clusters from there. 

The second algorithm finds clusters by binning stars according to ra and dec, and performing a random walk within bins to find dense regions. It then filters for the densest regions with a thresholding algorithm. It then filters for color outliers within these clusters. The second algorithm should be treated as the most effective and has most potential to be applied to other datasets and fine tuned to provide the best results.

#
University of Chicago

CMSC 12300 Spring 2018

Dr. Matthew Wachs

Submitted as the result of a quarter long project in fulfillment of the
class requirements.