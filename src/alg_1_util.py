from numpy.random import randint
from numpy import histogram, array
from scipy.interpolate import UnivariateSpline
from heapq import heapify


def cut_list(l, max_len, mult):
    new_list = []

    for i in range(int(round(max_len * mult))):
        idx = randint(low=0, high=len(l))
        new_list.append(l[idx])

    return new_list


def map_clust(astr, max_len, len_mult, node_list):
    '''
    For a given AstroObject, yield the object and distances to a random
    collection of color outliers in the sky.
    Inputs:
        astr: AstroObject to compare
        max_len: int, max number of other outliers to store in memory
        len_mult: float in (0,1), multiplier to reduce max_len by
        node_list: list of other objects in sky to compare to, 
            persistent for each mapper
    Yields: Astro object and distance to another outlier in the sky
    '''
    new_node_list = node_list
    new_node_list.append(astr)

    # If our node list is too large, toss oldest (first) values
    if len(new_node_list) > max_len:
        new_start = len(new_node_list) - round(max_len * len_mult)
        new_node_list = new_node_list[new_start:]

    # Validate that our list is still the right size
    if len(new_node_list) > max_len * len_mult:
        # Now iterate over the nodes and find distances
        for astr2 in new_node_list:
            dist = astr.euc_dist_4d(astr2)
            yield astr, dist

    node_list[:] = new_node_list


def comb_clust(astr, dist_gen, top_k, num_bins):
    '''
    Takes an AstroObject and a generator of distances from the object
    to other outliers in the sky. Returns a radius within which a
    cluster may lie, if any exist.
    Inputs:
        astr: AstroObject to analyze. Radius is put in dist_from_center
            attribute.
        dist_gen: generator of distances to a set of nearby outliers
        top_k: how many outliers to examine
        num_bins: how finely to calculate counts
    Yields: 1 (junk value), AstroObject w/ dist_from_center attribute
    '''

    heap = [val for val in dist_gen]
    if not heap:
        return None
    heapify(heap)
    cutoff = min(top_k, len(heap))  # ensure we don't have indexerrors
    heap = heap[:cutoff]
    counts, edges = histogram([i for i in heap], num_bins, density=True)
    y = array([0] + list(counts))
    x = array(list(edges))  # get distances
    # we need to give some approximate knots
    # calculate the derivates
    d1 = UnivariateSpline(x=x, y=y, k=4).derivative().roots()
    try:
        astr.dist_from_center = min(d1)
        yield 1, astr
    except:
        pass

    # # Pick num clusters / allocate memory so this next line isnt an
    # # issue at a given node. Sort by distance from astr.
    # heap = [i for i in dist_gen]
    # heapify(heap)
    # # Truncate to desired value.
    # cutoff = min(top_k, len(heap))
    # heap = heap[:cutoff]

    # # Bin distances.
    # counts, edges = histogram([dist for dist in heap], num_bins)
    # x = list(edges)
    # y = list(counts)

    # # Store potential cluster radius in astr.dist_from_cente
    # # NOTE: need a better way to calcualte radius
    # astr.dist_from_center = x[y.index(max(y))]
    # yield 1, astr
