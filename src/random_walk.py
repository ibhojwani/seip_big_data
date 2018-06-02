from astro_object import AstroObject
import numpy as np
#from group_objects import MrBoxAstroObjects
import copy


def recast_astro_objects(astro_list):
    """
    Take a list of dictionaries with astro objects info and convert to
    a list of astro objects
    :param astro_list: list of dictionaries
    :return l: list of astro objects, with attributes filled in.
    """
    l = []
    for astro_dict in astro_list:
        astro_object = AstroObject()  # instantiate astro object
        astro_object.from_dict(astro_dict)  # cast back into astro object
        l.append(astro_object)

    return l


def build_adjacency_matrix(astro_list):
    """
    Build a matrix of probabilities for random walk. Each value at location
    i, j is a probability of moving from i'th object to j'th object and
    vice-versa
    :param astro_list: list of astro objects
    :return norm_trans_matrix: numpy array, probability matrix, with rows adding
    to 1
    """
    # If the list has 0 or 1 object, no travel between objects is possible:
    if len(astro_list) <= 1:
        return None

    # create empty adjacency matrix
    dimension = len(astro_list)
    adjacency_matrix = np.zeros((dimension, dimension))

    for one_ind in range(len(astro_list)):
        astro_1 = astro_list[one_ind]
        for two_ind in range(one_ind + 1, len(astro_list)):
            astro_2 = astro_list[two_ind]
            dist = astro_1.euc_dist_4d(astro_2)

            # fill adjacency matrix
            adjacency_matrix[one_ind][two_ind] = dist
            adjacency_matrix[two_ind][one_ind] = dist

    # transform distances in adjacency matrix
    trans_matrix = transform_dist_matrix(adjacency_matrix)

    # fill the diagonal with zeroes
    np.fill_diagonal(trans_matrix, val=0)

    # normalize the transformed matrix across rows
    norm_trans_matrix = row_normalize_matrix(trans_matrix)

    return norm_trans_matrix


def transform_dist_matrix(dist_adj_mat):
    """
    Helper function, transforms a matrix of distances to a matrix of trans-
    formed distances. Each distance is transformed with function transform_distance
    :param dist_adj_mat: numpy array, matrix of distances between objects
    :return func(dist_adj_mat): numpy array, matrix of transformed distances
    """
    func = np.vectorize(transform_distance)
    return func(dist_adj_mat)


def transform_distance(distance):
    """
    Transform a distance into a measure that recallibrates the distance to
    give higher values to closer objects
    :param distance: float
    :return transformed_dist: float
    """
    transformed_dist = 1 / (1 + distance)

    return transformed_dist


def row_normalize_matrix(transformed_matrix):
    """
    Normalize values in a matrix across rows; i.e. rows add to one
    :param transformed_matrix: numpy array, matrix of values to normalize
    :return normalized_matrix: numpy array, normalized matrix
    """
    row_sums = transformed_matrix.sum(axis=1)  # Across rows normalization
    normalized_matrix = transformed_matrix / row_sums[:, np.newaxis]

    return normalized_matrix


def random_walk(prob_mat, start_row, iterations, astro_objects_list):
    """
    Reference for function:
    https://medium.com/@sddkal/random-walks-on-adjacency-matrices-a127446a6777

    :param prob_mat: numpy array, probabilities of visting other points
    :param start_row: int, which row/point to start at
    :param iterations: int, number of iterations to do random walk
    :param astro_objects_list: list of astro objects
    :return astro_objects_list_copy or None: list of astro objects, with
    visitation counts updated (None if bad probability matrix input)
    """
    # Check that probability matrix is a numpy array. It shouldn't be if
    # there were no objects between which to compare distances:
    if type(prob_mat).__module__ == 'numpy':

        # create array of possible outcomes
        possible_outcomes = np.arange(prob_mat.shape[0])

        # begin at pre-defined row
        curr_index = start_row

        # Deepcopy astro object list:
        astro_objects_list_copy = copy.deepcopy(astro_objects_list)

        # create empty matrix to store random walk results
        dimension = len(prob_mat)
        random_walk_matrix = np.zeros((dimension, dimension))

        # begin random walk
        for k in range(iterations):
            probs = prob_mat[curr_index]  # probability of transitions

            # sample from probs
            new_spot_index = np.random.choice(possible_outcomes, p=probs)

            # increment counts in the astro object attribute
            astro_objects_list_copy[new_spot_index].rand_walk_visits += 1

            random_walk_matrix[curr_index][new_spot_index] += 1
            random_walk_matrix[new_spot_index][curr_index] += 1

            # make the new spot index the current index
            curr_index = new_spot_index
        #print(random_walk_matrix)
        return astro_objects_list_copy
    return None


#Test code
if __name__ == "__main__":
    # initialize MRJob
    mr_job = MrBoxAstroObjects(args=['-r', 'local', '5218597.csv'])
    with mr_job.make_runner() as runner:
        runner.run()
        for line in runner.stream_output():
            key, value = mr_job.parse_output_line(line)
            print(key, value)
            # # l = recast_astro_objects(value)
            # matrix = build_adjacency_matrix(value)
            # #print("+++++++++++++++++")
            # #print(matrix)
            # rw_astro_list = random_walk(matrix, start_row=0,
            #                             iterations=1000, astro_objects_list=value)
            # print(rw_astro_list)
            # print("??????????????????")
            # for i in range(len(value)):
            #     print("original object", value[i])
            #     print("original object visits", value[i].rand_walk_visits)
            #     if rw_astro_list:
            #         print("modified object", rw_astro_list[i])
            #         print("modified object visits", rw_astro_list[i].rand_walk_visits)





