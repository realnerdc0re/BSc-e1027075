## TODO:

### NEXT:
- split preprocessing of the data from the actual Classification.py script
- prepare already sampled & labeled CSV files to use with rpi in the first step (just one Workday)
	- packet-sampled:
		- every n-th package
	- flow-sampled:
		- n = 5
		- CAIA_flowSampling.json
		- every n-th package
- implement save/load model and export test-data for usage on rpi
- tweak Classification.py to read CSV line-by-line on rpi


### LATER:
- add functionality to save ML algorithm score with other relevant informations into file
- write script to evaluate data logged with dstat in combination with ML scores and timestamps saved
- change rpi distro from dietPi to piCore (http://www.tinycorelinux.net/ports.html, check http://forum.tinycorelinux.net/index.php/topic,24392.0.html to import integrated wifi firmware)


## INPROGRESS:

- write small script to merge CSVs on Raspberry Pi due to 100MB Github filesize limit
- evaluate all necessary tools/packages for Raspberry Pi setup


## DONE:

- implement mode-selection in sampling scripts for usage of AGM feature vector (labeling.py needs different mode then)
- how to handle low flash-drive storage on Raspberry Pi (8GB) for large capture files? (additional storage via USB, larger SD card...)

## DISCARDED:

- tweak dstat delay for average values over a given time: its not possible to set delays below the default 1 second. does not affect the 
