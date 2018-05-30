# Argument 1: data directory, Argument 2: output file
# e.g. bash merge_seip.sh data merged_seip.csv
# assigns the header in the outfile and concatenates
# all the other files without their headers

echo 'designation,ra_pm,dec_pm,sigra_pm,sigdec_pm,pmra,pmdec,sigpmra,sigpmdec,w1mpro,w2mpro,w3mpro,w4mpro,w1snr,w2snr,w3snr,w4snr' > $2

# from https://unix.stackexchange.com/questions/96226/delete-first-line-of-a-file#96284
# https://www.quora.com/How-do-you-combine-multiple-csv-files-into-a-single-file-using-the-command-line?share=1
for filename in $(ls $1/*.csv)
	do sed 1d $filename >> $2
done