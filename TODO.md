


## INPROGRESS:

- change datatypes from int64/float64 to int32/float32 to save memory directly after sampling? (df.astype('int32') e.g.) - astype maybe has issues with features containing NaNs or Infs, check on specific dataset!
- read CSV line-by-line: process data per chunk on rpi (https://www.codementor.io/@guidotournois/4-strategies-to-deal-with-large-datasets-using-pandas-qdw3an95k?utm_campaign=Data_Elixir&utm_medium=social) - create new script for RPI usage
- change replacement in cleanInf similar to cleanNaN via: dataset[column] = dataset[column].replace(np.inf, replacement)



## TODO:

#### NEXT:

- use numpy.vectorize to speed up cell replacements (https://numpy.org/doc/stable/reference/generated/numpy.vectorize.html)
- flowStartMilliseconds: remove feature direct after labeling
- pyplot import only on non-rpi devices?
- add AGM feature vectors for packet-sampling, make selection automatic depending on the --flowsampling/packetsampling argument alltogether

#### LATER:

- when going full in on rpi, avoid useless write/reads of dataset-files to speed up the whole process (e.g. merge Preprocessing.py and Classification.py when doing the preprocessing on rpi), pack as many functions into a single script as possible to avoid time-sconsuming write/reads!
- write script to evaluate data logged with dstat in combination with ML scores and timestamps saved
- think about the substitutions for NaNs & Infs in preprocessing
- implement automatic folder generation on script execution (os.path.exists(folder) and os.makedirs(folder)), do this with a separate python script for the base-folder structure. expand this structure if necessary for multiple test-runs? (important for wd/logs, and first time creation of time.csv if no file exists or if a file already exists on scriptstart outside of Control.py create new file (due to appending time within any other scripts than Control.py...))
- improve filename generation, including working-directory instead of hardcoded /home/<user>/<project-folder>, maybe read folder-content, based on that create dictionary with filenames without extensions, use that and wd as base to forge filepaths and filenames 
  
#### IMPROVEMENTS:

- create config file to import, containing all necessary file- and folderpaths, paths to executable tools... and import this file instead of making definitions inside every script
- choose another method to load/save data, model & results
- improve FlowSampling method (function convertToList), now using actual lists instead of np array for iteration, etc..






## DONE:

- improve speed for NaN replacement
- better handling for time.csv creation (writing or appending, based on fresh script start or execution within Control.py)
- tweak importCSV in Preprocessing.py to support chunksize on rpi
- restructure Classification.py main depending on argument choices...
	- saving results to file not implemented on -l loading right now
- Classification.py: take care when using --time to check if /logs/time.csv is already existing to open with 'a' append, or with 'w' write
- add command to only import model, but preprocess data on rpi via -m --model & to import test data only -d, --data
- tweak Classification.py to read CSV line-by-line into pandas dataframe on rpi (chunksize)
- switch to saving/loading model via joblib
- skip scaleinput = copyDfList in Classification.py
- dump dietPi installation because fucked up python module installations, not able to upgrade scikit-learn to 0.23 necessary for importing models
- add paths for rpi/repository folders containing already fitted data & model
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
- change rpi distro from dietPi to piCore (http://www.tinycorelinux.net/ports.html, check http://forum.tinycorelinux.net/index.php/topic,24392.0.html to import integrated wifi firmware), reason: available piCore packages not suitable for this application
- tweak dstat delay for average values over a given time: its not possible to set delays below the default 1 second
