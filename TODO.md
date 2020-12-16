# TODO:

	## NEXT:
	- prepare already sampled CSV files to use with rpi in the first step
	- implement save/load model and export test-data for usage on rpi
	- tweak Classification.py to read CSV line-by-line on rpi
	- change dstat count/interval


	## LATER:
	- add functionality to save ML algorithm score with other relevant informations into file
	- write script to evaluate data logged with dstat in combination with ML scores and timestamps saved
	- change rpi distro from dietPi to piCore (http://www.tinycorelinux.net/ports.html, check http://forum.tinycorelinux.net/index.php/topic,24392.0.html to import integrated wifi firmware)


# INPROGRESS:

- evaluate all necessary tools/packages for Raspberry Pi setup


# DONE:

- implement mode-selection in sampling scripts for usage of AGM feature vector (labeling.py needs different mode then)
- how to handle low flash-drive storage on Raspberry Pi (8GB) for large capture files? (additional storage via USB, larger SD card...)