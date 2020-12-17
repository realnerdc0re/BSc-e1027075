## TODO:

#### NEXT:

- implement save/load model and export test-data for usage on rpi
- implement export of just the test-data to run minimal storage for classification on rpi
- tweak Classification.py to read CSV line-by-line on rpi


#### LATER:

- add functionality to save ML algorithm score with other relevant informations into file
- write script to evaluate data logged with dstat in combination with ML scores and timestamps saved
- change rpi distro from dietPi to piCore (http://www.tinycorelinux.net/ports.html, check http://forum.tinycorelinux.net/index.php/topic,24392.0.html to import integrated wifi firmware)
- think about the substitutions for NaNs & Infs in preprocessing


## INPROGRESS:

- add paths for rpi
- expand save to add "_Xtest, _Ytest, _model" to the filenames when saving model & test-portions, to have all the files available in one folder
- improve filename generation, including working-directory instead of hardcoded /home/<user>/<project-folder>, maybe read folder-content, based on that create dictionary with filenames without extensions, use that and wd as base to forge filepaths and filenames 


## DONE:

- implement save/load model & data
- split preprocessing of the data from the actual Classification.py script
- write small script to merge CSVs on Raspberry Pi due to 100MB Github filesize limit
- implement mode-selection in sampling scripts for usage of AGM feature vector (labeling.py needs different mode then)
- how to handle low flash-drive storage on Raspberry Pi (8GB) for large capture files? (additional storage via USB, larger SD card...)
- prepare already sampled & labeled CSV files to use with rpi in the first step
- evaluate all necessary tools/packages for Raspberry Pi setup

## DISCARDED:

- tweak dstat delay for average values over a given time: its not possible to set delays below the default 1 second. does not affect the 
