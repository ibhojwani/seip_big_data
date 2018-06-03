from alg_2 import MrBoxAstroObjects


# Test code:
if __name__ == "__main__":
    # initialize MRJob:
    csv_input = 'data/5218562_short.csv'
    mr_job = MrBoxAstroObjects(args=['-r', 'local', csv_input])
    with mr_job.make_runner() as runner:
        runner.run()
        # For every output tuple from the MRJob:
        for line in runner.stream_output():
            # list_of_astroobjs here will contain items within a single box:
            bounds, list_of_astroobjs = mr_job.parse_output_line(line)
            # Some lists will be empty (when only one or zero objects in a box):
            if list_of_astroobjs:
                for astro_obj in list_of_astroobjs:
                    # This just prints number of visits of this astro object:
                    print("OBJECT ID:", astro_obj.objid,
                          "| NUM VISITS:", astro_obj.rand_walk_visits)
            print("===================BOX SEPARATOR===================")
