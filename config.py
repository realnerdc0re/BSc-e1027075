#!/usr/bin/env python
from pathlib import Path, PureWindowsPath, PurePath, PurePosixPath


#######################################################################################
# BASIC CONFIGURATION
#######################################################################################
# BASE directories
# used for proper path generation
mntd    = PurePosixPath('/mnt')
wd      = Path.cwd()
hd      = Path.home()
#######################################################################################
# PCAP filepath & filenames (without extension)
fpath = mntd / 'data' / 'CIC-IDS2017' / 'PCAP'

filenames = {
0:'Merged',
1:'Monday-WorkingHours',
2:'Tuesday-WorkingHours',
3:'Wednesday-WorkingHours',
4:'Thursday-WorkingHours',
5:'Friday-WorkingHours'
}

pattern = '*Hours.csv' # pattern used to merge files
#######################################################################################
# FOLDERS, FILES & LOGS
# sampled CSVs & result logs, temporary logs in working directory
flowfolder      = mntd / 'data' / 'CIC-IDS2017' / 'PCAP' / 'flow-sampledCSV'
packetfolder    = mntd / 'data' / 'CIC-IDS2017' / 'PCAP' / 'packet-sampledCSV'


# filenames used for logs
csv_dstat   = 'dstat.csv'
csv_time    = 'time.csv'
csv_result  = 'result.csv'
csv_report  = 'report.csv'
csv_info    = 'information.csv'

# working directory folders
tmp     = wd / 'tmp'
logs    = wd / 'logs'
figures = wd / 'figures'

# full path to wd logs
time    = logs / csv_time
dstat   = logs / csv_dstat
result  = logs / csv_result
report  = logs / csv_report

# pickle-model files
model_remote    = '{}_model_remote.pkl'
model_local     = '{}_model_local.pkl'
#######################################################################################
# TOOLS
# path to executable for go-flows and labeling-script
goflowspath     = hd / 'Git' / 'go-flows' / 'go-flows'
labelingpath    = mntd / 'data' / 'BSc-e1027075' / 'Labeling.py'
#######################################################################################


#######################################################################################
# SAMPLING CONFIGURATION
#######################################################################################
# FEATURE-VECTORS
# directory within working directory and filenames of available feature-vectors

vectorfolder = 'go-flows-configurations'

vectors = {
1:'AGM_10s.json',
2:'AGM_60s.json',
3:'AGM_3600s.json',
4:'CAIA_flowSampling.json',
5:'CAIA_packetSampling.json'
}
#######################################################################################
# SAMPLING-MODES
# modes available for perflow- and packetsampling
fsamplingmode = {
1:'every n-th packet',
2:'sample & skip n packets',
3:'sample first n packets of a flow',
4:'sample n, skip n-1, sample n-2 ...'
}
psamplingmode = {
5:'every n-th packet',
6:'time-based'
}
# merge dictionaries for easier addressing later on
samplingmode = fsamplingmode.copy()
samplingmode.update(psamplingmode)
#######################################################################################
# TRESHOLD, change details here
# numbers marks specific limits used for plausibility on specific
# argument combinations to guarantee automated execution
vectorlimit     = 5
samplinglimit   = 5

modelimit   = 4 # used to determine choice for samplingmodes in evaluation

flowlimit   = 4 # used to set mode to 'AGM' or '5tuple' for Labeling.py
packetlimit = 4
#######################################################################################


#######################################################################################
# EXPERIMENT CONFIGURATION
#######################################################################################
# REMOTE MACHINE
# username, IP and working directory for the remote machine
remotewd    = 'BSc-e1027075'
remoteuser  = 'dietpi'
remoteip    = '10.10.45.55'
remote      = '{}@{}'.format(remoteuser,remoteip)
#######################################################################################
# EXPERIMENTS
# batchsize for preprocessing
# files, feature-vectors, sampling-modes & sampling-steps to process
batchsize   = 100000
file        = [0]
vector      = [4,5]
mode        = [1,3,5]
steps       = [3,5,7,10]
n_PCA       = 4 # number of components for PCA
chunksize   = 1 # read CSV line-by-line
split       = 5000 # used for packetsampling, determines number of packets in editcap splits
splitsize   = 25*10**4 # to not exceed rpi RAM size, split files into 250k rows per file
#######################################################################################


#######################################################################################
# EVALUATION



#######################################################################################