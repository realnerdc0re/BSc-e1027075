


## INPROGRESS:

- improve names for flow-/packetsampling in results to be better distinguishable (e.g. per-flow sampling, per-packet sampling?)

- change labels in time.csv: dump logging stop-timestamps, improve segment-names to be ore precise

- maybe limit nodes/leaves depth/size for RandomForest classification to reduce model size
	- output nodes/leaves depth/sizes in results.csv

- try QEMU on Linux to virtualize dietpi ARM 32bit (https://raspberrytips.com/run-raspberry-in-virtual-machine/)
	- https://wiki.ubuntu.com/Kernel/Dev/QemuARMVexpress
	- https://gist.github.com/luk6xff/9f8d2520530a823944355e59343eadc1

- Virtualization: try to train RandomForest model in 32bit ARM dietpi VM (https://github.com/scikit-learn/scikit-learn/issues/2972)

- when saving Model also include PCA component number in filename??
- include swap usage in dstat

- change polar plot to get separate axis for every parameter with separate values? or keep polar as is and use highest usage as 100% comparison?

- create vertical bars automatically from time.csv

- change forged commands into single lines using placeholders (e.g. samplingcmd in Control.py) directly in os.system(samplingcmd.format(verbosearg,timearg,osarg,samplearg,featurearg...))

- rsync Merged.csv directly after creation in Control.py (including info-file containing sampling info) to rpi if pingable (or make error-fallback)

- take care of different dataframe splits on rpi due to chunked processing when saving model on Desktop and use same chunked processing when saving the RandomForest() model -> create models on Desktop with rpi-Preprocessing.py to use same training portion

- 





## TODO:

#### NEXT:

- create more detailed charts for modules once they are finished (preprocessing, classification, sampling...)

- use pathlib to generate filepaths instead of manual forging (https://docs.python.org/3/library/pathlib.html)

- flowStartMilliseconds: remove feature direct after labeling

- add AGM feature vectors for packet-sampling, make selection automatic depending on the --flowsampling/packetsampling argument alltogether


#### LATER:

- create function for saving timestamps
- get rid of unnecessary imports to save memory
- use numpy.vectorize to speed up cell replacements (https://numpy.org/doc/stable/reference/generated/numpy.vectorize.html)?
- pyplot import only on non-rpi devices?
- minor: verbose output makes no sense in Classification.py Xtrain,Xtest original and transformed is the same because its the same data
- check sampling on rpi (flowsampling, packetsampling on original data)
- when going full in on rpi, avoid useless write/reads of dataset-files to speed up the whole process (e.g. merge Preprocessing.py and Classification.py when doing the preprocessing on rpi), pack as many functions into a single script as possible to avoid time-sconsuming write/reads!
- write script to evaluate data logged with dstat in combination with ML scores and timestamps saved
- think about the substitutions for NaNs & Infs in preprocessing
- implement automatic folder generation on script execution (os.path.exists(folder) and os.makedirs(folder)), do this with a separate python script for the base-folder structure. expand this structure if necessary for multiple test-runs? (important for wd/logs, and first time creation of time.csv if no file exists or if a file already exists on scriptstart outside of Control.py create new file (due to appending time within any other scripts than Control.py...))
- improve filename generation, including working-directory instead of hardcoded /home/<user>/<project-folder>, maybe read folder-content, based on that create dictionary with filenames without extensions, use that and wd as base to forge filepaths and filenames 


#### IMPROVEMENTS:

- change replacement in cleanInf similar to cleanNaN via: dataset[column] = dataset[column].replace(np.inf, replacement) (useless, no infs in dataset anyway)
- create config file to import, containing all necessary file- and folderpaths, paths to executable tools... and import this file instead of making definitions inside every script
- choose another method to load/save data, model & results
- improve FlowSampling method (function convertToList), now using actual lists instead of np array for iteration, etc..






## DONE:

- write script for evaluation of stored results: use results from different sampling methods to compare e.g. runtimes (used highest one as 100%)
- save sampled CSVs in folders that contain important sampling-infos within the foldername (do this in rpi-Control.py with variable mergefolder, that is used to actually save Merged.csv and information.csv, around line 270)
- compress model dump (http://gael-varoquaux.info/programming/new_low-overhead_persistence_in_joblib_for_big_data.html)
- if importing model, don't PCA transform Xtrain at all
- add information about sampling-modes, sampling-steps and used feature-vector somewhere for further evaluation of results- and logging-output (done in rpi-Control.py)
- split dstat informations according to timestamps in time.csv
- create simple graphs for different parts of the script 
- transform epochtimestamps to start with 0 (time - timestampstart)
- transform units to readable ones (bytes to megabytes...)
- create spider-diagram for key values (mem, cpu, time, accuracy)
- add timestamps for making predictions
- implement load/save model (-m/-s) in rpi-Preprocessing.py (already done in Classification.py)
- add timestamp saves and dstat to rpi-Preprocessing.py
- rpi-Preprocessing.py: use pathlib to forge filepaths to get rid of OS choice
- create basic chart using draw.io (including blocks for sampling, preprocessing, classification...)and send to Fares
- implement partial_fit for the StandardScaler to process chunks to save memory usage, without this rpi will run into SWAP when applying scaling to the dataset
- read CSV line-by-line: process data per chunk on rpi
- change datatypes from int64/float64 to int32/16/8 or float32/float16 to save memory directly after sampling, include check to not convert features that require int64 (nonetheless, every imported CSV is imported with 64bit, so try to avoid unnecessary save/loads on rpi)
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

- re-install Proxmox VE latest version on my home-server to try ARM virtualization (added ARM support? https://forum.proxmox.com/threads/arm-support.72766/). FAILED, no ARM support
- change filepath & filenames generated in Control.py (FlowSampling.py and PacketSampling.py) to include actual sampling mode and sampling steps (either as additional info-file or within the filenames) -> now done in Control.py/rpi-Control.py with creation of information.csv
- implement RandomForest classifier using RandomForest(warm_start=True) for fit on chunks
- try different approach for the merged CSV on rpi: instead of merging all sampled CSVs into one large single CSV, read_csv workdays, preprocess those (including reducing memory size float16/32, int8/16/32, cleaning,...) and merge the preprocessed data right before doing the RandomForest classification
- change rpi distro from dietPi to piCore (http://www.tinycorelinux.net/ports.html, check http://forum.tinycorelinux.net/index.php/topic,24392.0.html to import integrated wifi firmware), reason: available piCore packages not suitable for this application
- tweak dstat delay for average values over a given time: its not possible to set delays below the default 1 second
