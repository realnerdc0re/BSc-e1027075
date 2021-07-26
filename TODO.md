## INPROGRESS
- implement probabilistic sampling for packet-based sampling and maybe also flow-based sampling: https://towardsdatascience.com/probability-sampling-with-python-8c977ad78664
    - random sampling
    - n out of N sampling (similar to how Cisco routers do it)
        - right now I do n, N = n²
        - maybe do n = 1 +sqrt(N)?
        - https://sflow.org/packetSamplingBasics/
        - https://sflow.org/
        - https://openlab-mu-internal.web.cern.ch/03_documents/3_technical_documents/technical_reports/2007/rj-mm_samplingreport.pdf
        - https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/netflow/configuration/12-2sr/nf-12-2sr-book/nf-detct-analy-thrts.html
    - will deliver worse performance but results are still interesting


### CODE
- check makefile syntax for private usage
- CHANGE samplingmode choice: not use limits set in config.py but use acutal feature-vector names instead
- NaN replacement AGM still questionable
    - implemented NaN row detection within searchNaN function, all occuring NaN flows should be kind of neglible...

#### SAMPLING, PREPROCESSING, CLASSIFICATION
- rename scripts and feature-vectors properly and change everything connected accordingly (shittask)
    - rpi-Preprocessing.py  ==> Classification.py
    - rpi-FlowSampling.py   ==> FlowbasedSampling.py
    - rpi-PacketSampling.py ==> PacketbasedSampling.py
    - rpi-Sampling.py       ==> SamplingControl.py
    - rpi-Evaluation.py     ==> Evaluation.py
- config.py: get limits directy from dictionary-entries same way I implemented the sampling-modes

#### EVALUATION
- change model size to instances on comparison and ranking spiderchart plots
- develop meaningful parameter, involving accuracy, resourece-usage and maybe runtime to express tradeoff between accuracy and resources for different sampling methods
    - instead of using f11 and recall1 use degradiation compared to best score for same... (should even out base-differences on various feature-vectors for the same dataset)
        - https://www.wikiwand.com/en/Feature_scaling, use best result on same feature-vector and all modes, steps (0,3,5,7) as maximum, min-max scaled all scores based on maximum and minimum values instead of base scores
- for comparison charts:
    - add legend on top of plot show visual differentiation of flow-based and packet-based plots
    - add legend for actual plots below spider chart
- group experiment classobjects based on following comparisons (files always Merged?):
    - same featurevector, same samplingmethod
        - different steps
    - same steps, same samplingmethods
        - different featurevector
    - same steps, same featurevectors
        - different samplingmethods


### THESIS

- prediction time per instance based on sampling? refer to Asadi et al figure 2 (the more complex the tree the more time per instance)
    - also chapter 6 discussion points out that the necessary feature vector preprocessing is very difficult to to study cuz based on implementation extraction algorithm.

- change all figures from PNG to PDF (Cropped)
    - also increase line width by +1 for everything to improve printing results?

- mention in detail the fails tied to model export/import on the Raspberry Pi Zero
    - maybe redo the experiments to gather the exact error message:
        - with a fitted model created on:
            - Ubuntu 20.10 (64bit)
            - Debian 32bit
- describe why steps done like splitting files and downgrading datatypes were necessary to get the classification going on the Raspberry Pi Zero

- upload thesis to SVN when following topics are written:
    - experiment description: 
        - list,legend or table that describes all used experiment configurations e.g. with roman letters
        - use those letter-shortcuts for the flow-charts
    - metric descriptions

- mention implemented, but not used sampling methods like sample n, skip n-1, sample n-2...
- adjust codelines in chapter 05 methodology after final code-changes and extend description when necessary
- chapter 01 introduction
- chapter 02 background
    - search for basic machine learning ressource requirements/usage and don't focus on anomaly detection
        - processing
        - classification tasks
        - flow export
- result & discussion

### DEFENSIO
- simplify the framework diagrams, these can also be placed in the thesis introduction:
    - group functions
    - simplify
- keep detailed diagrams in chapter methodology


## TODO

### NEXT
- rpi-FlowSampling.py: samplingmode 2 & 4 - improvements?
- use basefolderpaths from config.py also in rpi-Preprocessing, rpi-Sampling, rpi-FlowSampling, rpi-Packetsampling for more convenient customization of paths and way better maintenance possibilities

### LATER
- RF: random state for creating splits fixed for comparison? Setting parameters to control tree sizes to eventually reduce memory consumption, see scikit-learn documentation.
- use pathlib to generate filepaths instead of manual forging (https://docs.python.org/3/library/pathlib.html) for all filepaths (FlowSampling.py, PacketSampling.py)
- maybe limit nodes/leaves depth/size for RandomForest classification to reduce model size
    - output nodes/leaves depth/sizes in results.csv
- try QEMU on Linux to virtualize dietpi ARM 32bit (https://raspberrytips.com/run-raspberry-in-virtual-machine/)
    - https://wiki.ubuntu.com/Kernel/Dev/QemuARMVexpress
    - https://gist.github.com/luk6xff/9f8d2520530a823944355e59343eadc1
    - if above fails, just virtualize Linux with hardware similar to rpi (500MB RAM, one core CPU...)
- create function for saving timestamps
- get rid of unnecessary imports to save memory
- use numpy.vectorize to speed up cell replacements (https://numpy.org/doc/stable/reference/generated/numpy.vectorize.html)?
- minor: verbose output makes no sense in Classification.py Xtrain,Xtest original and transformed is the same because its the same data
- check sampling on rpi (flowsampling, packetsampling on original data)
- write script to evaluate data logged with dstat in combination with ML scores and timestamps saved
- think about the substitutions for NaNs & Infs in preprocessing other than mean average
- implement automatic folder generation on script execution (os.path.exists(folder) and os.makedirs(folder)), do this with a separate python script for the base-folder structure. expand this structure if necessary for multiple test-runs? (important for wd/logs, and first time creation of time.csv if no file exists or if a file already exists on scriptstart outside of Control.py create new file (due to appending time within any other scripts than Control.py...))

### IMPROVEMENTS
- implement scapy to do the packet-sampling, using editcap is like a very poor bandaid in comparison and creatues issues for timebased sampling technique implementation
- user inner classes for class Experiment
- change replacement in cleanInf similar to cleanNaN via: dataset[column] = dataset[column].replace(np.inf, replacement) (useless, no infs in dataset anyway)
- create config file to import, containing all necessary file- and folderpaths, paths to executable tools... and import this file instead of making definitions inside every script
- choose another method to load/save data, model & results
- improve FlowSampling method (function convertToList), now using actual lists instead of np array for iteration, etc..




## DONE
- chapter 05 methodology:
    - Preprocessing.py diagram: dstat logging missing
- change comparison.csv column order:
    - parameter
    - vector
    - sampling
    - experiment
    - pattern
    - accuracy-score ... F1 1 unchanged
    - runtime
    - instances
    - classification time
    - classification speed
    - maxRAM
    - modelsize
    - trees
    - maxdepth
    - maxleaves
    - PCA components
    - PCA explained variance
- inlude loss of instances to classify in the parameter
- rp-Evaluation.py: limit polar plot y-axis to 100% to create similar plot scales
- rp-Evaluation.py: set titles to 'unsampled' when sampling steps are zero
- rp-Evaluation.py: add values to single experiment plots for every metric
    - scale RAM and Runtime to maximum occuring RAM and Runtime values
- rp-Evaluation.py: include following stats in comparison.csv:
    - modelsize (MB)
    - max depth
    - max leaves
- REVERSE keeping flowStartMilliseconds in Labeling.py for debugging (remove this feature from preordered (list) in flowSampling.py and packetSampling.py for AGM and CAIA or just keep it and remove it in preprocessing)
- CAIA: sort and rename features on packet-based and flow-based sampling for easier comparison
- CAIA: compare unsampeld flow-based and packet-based configuration output for possible mistakes in implementation
    - check all empty cells and replace with 0 for features:
        + 'count(tcpSynTotalCount,forward)'
        + 'count(tcpAckTotalCount,forward)'
        + 'count(tcpFinTotalCount,forward)',
        + 'count(_tcpCwrTotalCount,forward)'
        + 'count(octetTotalCount,backward)',
        + 'count(tcpSynTotalCount,backward)',
        + 'count(tcpAckTotalCount,backward)',
        + 'count(tcpFinTotalCount,backward)',
        + 'count(_tcpCwrTotalCount,backward)',
    - check 'count(packetTotalCount,backward)', different numbers for flow- and packet-based config?
- AGM10s: change feature to calculate packetTotalCount from destinationPort to 'apply(accumulate(protocolIdentifier),forward)' to get correct total packet counts.
- AGM10s: accumulate with goflows returns list with whitespace separation, but it also uses whitespaces for non-occuring e.g. flags. Correct non-TCP flows for correct list generation
- evaluation: add classification speed and F1-scores for 0 and 1 (maybe even replace Precision or Recall parameter with F1-scores), remove CPU usage and cached RAM from Spiderchart
- use one feature-per-flag encoding instead of textual-binary-decimal encoding for AGM (flow-based and packet-based sampling)
- change NaN replacement, separate mean calculation & replacement for Xtrain and Xtest (rpi-Preprocessing.py, starting at line 818)
- implement n_component determination when executing pre-processing on the local machine
    - save this number in as parameter in information.csv in every experiment folder (better I guess)
    - load component number on remote to for incremental PCA
- implement AGM feature handling in packetSampling.py and flowSampling.py
- implement no sampling experiment execution in Master.py when steps == 0!!!!
    - directly pass merged PCAPs to labeling script and execute Preprocessing for results
- remove CPU usage and RAM cached from graphs and charts, its a useless stat
- rpi-Preprocessing.py: implement replacing NaN with feature mean instead of 0!!!!
- implement timestamp after predictions
- save model uncompressed to gather file-size that has to be loaded into memory directly from file
- create tmp directory in working-directory if necessary when executing rpi-Preprocessing.py, otherwise error because folder is ignored in git and therefore not created
- implement AGM feature handling in flowSampling.py
    - maybe convert textual features to numerical values (encoding) before calculation distinct and modeCount, mode only gets saved for _tcpFlags....
    - encoding features right at the beginning could be helpful so conversion to numpy arrays can be applied directly
- implement AGM feature handling in packetSampling.py
    - change condition to first three letters of feature vector instead of number
    - drop destination IP feature before labeling
- implemented PCA batchsize in configuration
- add maximum RAM usage value and file that got processed to the comparison.csv!
- also sync config.py to remote to get immediately all configuration changes on parameters like batchsize, splitsize and so on...
- implement foldername in config.py and use that in Preprocessing, Master and Sampling scripts
- add --nosampling to skip sampling if possible (check if sampled file already exists and use the sampled & labeled csv instead of sampling)
- describe softlink usage on remote machine in config.py to get user aware of this for documentation
- mention authorization via SSH keys for Master.py execution in thesis
- create more detailed charts for modules once they are finished (preprocessing, classification, sampling...)
- check LaTeX basics
- setup environment for LaTeX usage and check basics to add text-blocks to template on OSX
- create detailed flow-charts for the scripts in addition to the overview flow-chart
- implement draft chapter-structure

- adjust CAIA_perflowSampling.json feature vector to have correct per-flow sampling features
- create df for comparison table of different techniques, containing at least:
    - accuracy
    - recall 0,1
    - precision
    - F1
- include sampling mode in informational output in rpi-Preprocessing.py
- reading double digit sampling steps need to be improved in rpi-Evaluation.py. Either read from foldername or just use the actual information.csv instead (probably cleaner way to do it, check script line 121)
- config.py: append psamplingmode at the end of fsamplingmode dictionary so I don't have anything to change afterwards when tweaking samplingmodes?
- change evaluation script to read data from new folder-structure, containing logs-rpi* subfolders for fit/import model...
- dstat swap- & memory-usage will have similar labels ("used", "free"): take care of duplicates in rpi-Evaluation.py
- evaluation: implement a class experiment, containing info about file, vector, steps, samplingmethod and find experiments that can be used for comparisons based on that class
- implement csv_... filenames in rpi-Sampling.py and rpi-Evaluation.py
- clean complete folders before progressing on rpi-Evaluation.py to have all sampled data
    - add logfolder-names to config.py and implement in rpi-Preprocessing & rpi-Evaluation
- add properties for pandas df to import into class Experiments for
    - dstat.csv
    - time.csv
    - result.csv
    - report.csv
- set variables for PCAP path and all other useful base-folders in config.py, implement those in all scripts:
    - rpi-PacketSampling.py
    - rpi-FlowSampling.py
    - rpi-Preprocessing.py
    - rpi-Sampling.py
- create logfolder names to distinguish betweenn local and remote machine (convention now: logs_<whatever>_remote/local)
    - rpi-Preprocessing.py: logs_model-import/fit_local/remote
    - rpi-Sampling.py: logs_Sampling
- improve creation of samplearg, featurearg and samplingcmd in rpi-Sampling.py
- change forged commands into single lines using placeholders (e.g. samplingcmd in Control.py) directly in os.system(samplingcmd.format(verbosearg,timearg,osarg,samplearg,featurearg...))
- write script for automated experiment execution (Master.py):
    - implement configuration file (config.py) containing all necessary information to execute all experiments
    - does following steps subsequently:
        - check online status of remote machine (VM/rpi)
        - rpi-Sampling.py on local machine to create sampled CSV
        - rpi-Preprocessing.py on local machine to create model
        - create directory for necessary data on remote machine (VM/rpi), containing:
            - sampled CSV
            - fitted pickle-model
        - sync above mentioned files to remote machine via rsync
        - execute rpi-Preprocessing.py on remote machine, importing the synced model, saving results on remote machine
        - sync back results to the local machine for further evaluation
- improved saving log-files at the end of rpi-Preprocessing.py
- implement --rpi on rpi-Preprocessing.py to properly kill dstat, since this has to be done in different ways on Linux and dietpi
- set softlink on rpi so no script paths have to be changed in rpi-Preprocessing.py:
    - save data to process on rpi/vm into a folder 'data' in the homefolder (e.g. /home/dietpi/data), retaining original folderstructure from desktop machine (e.g. ) when syncing sampled data from desktop to rpi
    - set softlink via: sudo ln -s /home/dietpi/data/ /mnt/
- remove unnecessary if time executions in rpi-Preprocessing.py (all the stop timestamps)
- change paths in rpi-Preprocessing.py to use /mnt/... whatever for desktop machine, copy accordingly on rpi as mentioned in task below
    - needs all informations about sampling methods in arguments to choose correct data
- rpi-Preprocessing.py: use folders that determine sampling-mode, -steps & feature-vector (e.g. /mnt/data/CIC-IDS2017/PCAP/flow-sampledCSV/Merged_mode1_vector2_steps5/) instead of old folder /mnt/data/CIC-IDS2017/PCAP/flow-sampledCSV/
- rpi-Control.py: move logs into proper folder after sampling is done or after whole process is done
- add perflow/packetsampled at the end of foldername for easier differentiation later on
- rp-Control.py, rpi-Preprocessing.py: fix dstat process stop, right now getting return code instead of pid when using os.system, which is just the behaviour to expect.
- rpi-Control.py: change script for packetsampling mode to use pathlib file/folderpaths, get rid of osarg for execution-command
- change rpi-PacketSampling.py to use pathlib paths and commands, get rid of OS choice
- rpi-PacketSampling.py: sort list of splitfiles created via os.listdir() - not necessary sorted alphabetically, depending on OS
- changed cell conversion using lambda functions, changed sampling and cell replacements using lambda functions in rpi-FlowSampling.py (massive runtime improvements!)
- improve output rpi-FlowSampling.py
- change rpi-FlowSampling.py to use pathlib paths and commands, get rid of OS choice, change rpi-Control.py accordingly
- rpi-Control.py: change script for flowsampling mode to use pathlib file/folderpaths
- flowStartMilliseconds: remove feature directly at the end of Labeling.py
- install svn on ubuntu
- setup environment for LaTeX usage and check basics to add text-blocks to template on ubuntu
- Zotera: add IEEE papers and send account information to Fares once that is done
- include swap usage in dstat (--swap)
- change labels in time.csv: improve segment-names to be more precise to distinguish between fit and import model
- create timestamps for segements automatically from time.csv
    - use those timestamps for xticks in graphs, and label those for better graph readability
- when saving model also include PCA component number in result.csv
- improve names for flow-/packetsampling in results to be better distinguishable (e.g. per-flow sampling, packet sampling), has to be changed in rpi-Evaluation (merged spiderchart), rpi-Control (info used to generate informations.csv), rpi-Preprocessing (logged informations) and in the overview flowchart
- take care of different dataframe splits on rpi due to chunked processing when saving model on Desktop and use same chunked processing when saving the RandomForest() model -> create models on Desktop with rpi-Preprocessing.py to use same training portion
- create PGP key and send Mail to Dr. Fabini to get access to SVN
- check TUWEL group for LateX
- create Zotera account
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

- get rid of superverbose?
- implement rpi-Evaluation.py execution at the end of Master.py? Or process manually (probably better and makes sense)
- Virtualization: try to train RandomForest model in 32bit ARM dietpi VM (https://github.com/scikit-learn/scikit-learn/issues/2972)
- re-install Proxmox VE latest version on my home-server to try ARM virtualization (added ARM support? https://forum.proxmox.com/threads/arm-support.72766/). FAILED, no ARM support
- change filepath & filenames generated in Control.py (FlowSampling.py and PacketSampling.py) to include actual sampling mode and sampling steps (either as additional info-file or within the filenames) -> now done in Control.py/rpi-Control.py with creation of information.csv
- implement RandomForest classifier using RandomForest(warm_start=True) for fit on chunks
- try different approach for the merged CSV on rpi: instead of merging all sampled CSVs into one large single CSV, read_csv workdays, preprocess those (including reducing memory size float16/32, int8/16/32, cleaning,...) and merge the preprocessed data right before doing the RandomForest classification
- change rpi distro from dietPi to piCore (http://www.tinycorelinux.net/ports.html, check http://forum.tinycorelinux.net/index.php/topic,24392.0.html to import integrated wifi firmware), reason: available piCore packages not suitable for this application
- tweak dstat delay for average values over a given time: its not possible to set delays below the default 1 second