## TODO:

### NEXT:

- implement save/load model and export test-data for usage on rpi
- implement export of just the test-data to run minimal storage for classification on rpi
- tweak Classification.py to read CSV line-by-line on rpi


### LATER:

- add functionality to save ML algorithm score with other relevant informations into file
- write script to evaluate data logged with dstat in combination with ML scores and timestamps saved
- change rpi distro from dietPi to piCore (http://www.tinycorelinux.net/ports.html, check http://forum.tinycorelinux.net/index.php/topic,24392.0.html to import integrated wifi firmware)
- think about the substitutions for NaNs & Infs in preprocessing


## INPROGRESS:

- write small script to merge CSVs on Raspberry Pi due to 100MB Github filesize limit
- use actual working/home directory path-prefixes to forge filepaths when reasonable to do so
- split preprocessing of the data from the actual Classification.py script, at the end I just want to load an already preprocessed, test-portion of the dataset for pure classification (maybe make this an optional and let Classification.py still do the split in training/test-portion and the model-calculation)




## DONE:

- implement mode-selection in sampling scripts for usage of AGM feature vector (labeling.py needs different mode then)
- how to handle low flash-drive storage on Raspberry Pi (8GB) for large capture files? (additional storage via USB, larger SD card...)
- prepare already sampled & labeled CSV files to use with rpi in the first step (just one Workdays - those are not split at the moment, adding this with save/load model, exporting test-CSVs into BSc-e1027075/rpi/... together with the saved model-file)
	- packet-sampled:
		- every n-th package
	- flow-sampled:
		- n = 5
		- CAIA_flowSampling.json
		- every n-th package
- evaluate all necessary tools/packages for Raspberry Pi setup

## DISCARDED:

- tweak dstat delay for average values over a given time: its not possible to set delays below the default 1 second. does not affect the 
