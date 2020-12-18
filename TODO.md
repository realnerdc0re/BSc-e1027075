


## INPROGRESS:
- add paths for rpi/repository folders containing already fitted data & model

- improve filename generation, including working-directory instead of hardcoded /home/<user>/<project-folder>, maybe read folder-content, based on that create dictionary with filenames without extensions, use that and wd as base to forge filepaths and filenames 



## TODO:
#### NEXT:
- tweak Classification.py to read CSV line-by-line on rpi
- add AGM feature vectors for packet-sampling, make selection automatic depending on the --flowsampling/packetsampling argument alltogether
#### LATER:
- implement automatic folder generation on script execution (os.path.exists(folder) and os.makedirs(folder)), do this with a separate python script for the base-folder structure. expand this structure if necessary for multiple test-runs?
- write script to evaluate data logged with dstat in combination with ML scores and timestamps saved
- change rpi distro from dietPi to piCore (http://www.tinycorelinux.net/ports.html, check http://forum.tinycorelinux.net/index.php/topic,24392.0.html to import integrated wifi firmware)
- think about the substitutions for NaNs & Infs in preprocessing
#### IMPROVEMENTS:
- better handling for time.csv creation (writing or appending, based on fresh script start or execution within Control.py)
- create config file to import, containing all necessary file- and folderpaths, paths to executable tools... and import this file instead of making definitions inside every script
- choose another method to load/save data, model & results
- improve FlowSampling method (function convertToList), now using actual lists instead of np array for iteration, etc..
- improve Classification (function scalingDataframe) with using the actual data and not the copy 'scaleinput'



## DONE:
- expand save to add "_Xtest, _Ytest, _model" to the filenames when saving model & test-portions, to have all the files available in one folder
- add functionality to save ML algorithm score with other relevant informations into file
- save dstat logs, timestamps, results... in new folder BSc-e1027075/logs/...
- implement save/load model & data
- split preprocessing of the data from the actual Classification.py script
- write small script to merge CSVs on Raspberry Pi due to 100MB Github filesize limit
- implement mode-selection in sampling scripts for usage of AGM feature vector (labeling.py needs different mode then)
- how to handle low flash-drive storage on Raspberry Pi (8GB) for large capture files? (additional storage via USB, larger SD card...)
- prepare already sampled & labeled CSV files to use with rpi in the first step
- evaluate all necessary tools/packages for Raspberry Pi setup


## DISCARDED:
- tweak dstat delay for average values over a given time: its not possible to set delays below the default 1 second. does not affect the 
