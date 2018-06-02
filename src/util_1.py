from mrjob.job import MRJob
from mrjob.step import MRStep
from astro_object import AstroObject
from numpy.random import randint
from math import inf, sqrt
from numpy import array, histogram
from heapq import heapify
from scipy.interpolate import UnivariateSpline
from time import sleep
from matplotlib import pyplot as plt


def map_kmeans(line, centroids):
    astr = AstroObject()
    if isinstance(line, str):
        # Parses fresh input from file
        astr.fill_small(line)

    else:
        astr.from_dict(line)

    # Calc closest centroid, yield that centroid and obj colors
    if astr.ra:
        center_idx = None
        closest = inf
        for i, center in enumerate(centroids):
            dist = astr.sq_euc_2d(
                astr.color1, astr.color2, center[0], center[1])
            if dist < closest:
                closest = dist
                center_idx = i

        astr.dist_from_center = closest
        # Package relevant info as a hashable type to yield
        astr_to_pass = astr.package_small()
        # Yield centroid id, astro object, and distance to center
        return center_idx, astr_to_pass

    return None, None


def cut_list(l, max_len, mult):
    new_list = []

    for i in range(int(round(max_len * mult))):
        idx = randint(low=0, high=len(l))
        new_list.append(l[idx])

    return new_list


def heapsort(input):
    heap = []
    for item in input:
        heappush(heap, item)
    return heap


def map_clust(val, mod_std, max_len, len_mult, node_list):
    '''
    NOTE. THIS CURRENTLY GETS US OUTLIERS IN CLUSTERS. NOT CLUSTERS OF OUTLIERS.
    TO CHANGE THIS, ONLY ADD TO LIST IF IS AN OUTLIER.
    '''

    astr = AstroObject(data_row=val, small=True, dic=True)
    new_node_list = node_list
    ###### PUT THE LINES MENTIONED ABOVE HERE TO CHANGE FUNCTIONALITY #####
    if mod_std < astr.dist_from_center:
        ############ THIS LINE IS THE ONE TO CHANGE AS MENTIONED ABOVE ####
        new_node_list.append(astr)
        ############ THE LINES ABOVE ###################

        # If our node list is too large, we randomly toss values
        if len(new_node_list) > max_len:
            new_node_list = new_node_list[:round(max_len * len_mult)]

        # Validate that our list is still the right size
        if len(new_node_list) > max_len * len_mult:
            # Now iterate over the nodes and find distances
            for astr2 in new_node_list:
                dist = astr.euc_dist_4d(astr2)
                yield astr, dist

        node_list[:] = new_node_list


def comb_clust(astr, vals, top_k, num_bins):
    heap = [i for i in vals]
    heapify(heap)
    cutoff = min(top_k, len(heap))  # ensure we don't have indexerrors
    heap = heap[:cutoff]

    counts, edges = histogram([dist for dist in heap], num_bins)
    y = list(counts)
    x = list(edges)  # get distances
    # we need to give some approximate knots
    # calculate the derivates

    astr['dist_from_center'] = x[y.index(max(y))]
    yield 1, astr
