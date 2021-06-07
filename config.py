#!/usr/bin/env python
from pathlib import Path, PureWindowsPath, PurePath, PurePosixPath
from colorama import Fore, Style

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
pattern = '*Hours.csv' # pattern used to merge files in Sampling.py
#######################################################################################
# FOLDERS, FILES & LOGS
# sampled CSVs & result logs, temporary logs in working directory
flowfolder      = mntd / 'data' / 'CIC-IDS2017' / 'PCAP' / 'flow-sampledCSV'
packetfolder    = mntd / 'data' / 'CIC-IDS2017' / 'PCAP' / 'packet-sampledCSV'
# folder to store all result logs, temporary logs and sampled CSV for later evaluation
eflowfolder     = mntd / 'data' / 'CIC-IDS2017' / 'Experiments' / 'flow-sampledCSV'
epacketfolder   = mntd / 'data' / 'CIC-IDS2017' / 'Experiments' / 'packet-sampledCSV'
# experiment configuration foldername
foldername      = '{}_mode{}_vector{}_steps{}_{}'
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
# framework configuration file
configuration = 'config.py'
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
1:'AGM_10s_flowbased.json',
2:'AGM_60s.json', # unused
3:'AGM_3600s.json', # unused
4:'CAIA_flowSampling.json',
5:'CAIA_packetSampling.json',
6:'AGM_10s.json'
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
6:'time-based' # unused
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
modelimit       = 4 # used to determine choice for samplingmodes in evaluation
flowlimit       = 4 # used to set mode to 'AGM' or '5tuple' for Labeling.py
packetlimit     = 4
#######################################################################################
tcpflags = {
        'A':100000000, # ACK
        'P': 10000000, # PSH
        'F':  1000000, # FIN
        'R':   100000, # RST
        'S':    10000, # SYN
        'U':     1000, # URG
        'E':      100, # ECE
        'C':       10, # CWR
        'N':        1  # NS
    }
#######################################################################################

#######################################################################################
# EXPERIMENT CONFIGURATION
#######################################################################################
# REMOTE MACHINE
# username, IP and working directory for the remote machine
remotewd    = 'BSc-e1027075'
#remoteuser  = 'dietpi'
#remoteip    = '10.10.45.55'
#remoteip    = '192.168.178.29'
remoteuser  = 'thesis'
remoteip    = '10.10.40.209'
remote      = '{}@{}'.format(remoteuser,remoteip)
remoteconf  = '/home/{}/{}/{}'.format(remoteuser,remotewd,configuration)
#######################################################################################
# EXPERIMENTS
# batchsize for preprocessing
# files, feature-vectors, sampling-modes & sampling-steps to process
#file        = [0]
#vector      = [1,4,5,6]
#mode        = [1,3,5]
#steps       = [7]

file        = [0]
vector      = [1,4,5,6]
mode        = [1,3,5]
steps       = [3]

n_PCA       = 4 # number of components for PCA
PCA_batch   = 10**5 # batchsize used for incremental PCA
batchsize   = 10**5 # batchsize used for Standard Scaler partial fit (default 10**5)
chunksize   = 10**5 # read CSV in chunks (reading line-by-line not allowed! default 10**5)
split       = 5000 # used for packetsampling, determines number of packets in editcap splits
splitsize   = 25*10**4 # to not exceed rpi RAM size, split files into 250k rows per file (default 25*10**4)
#######################################################################################
# MODEL ESTIMATORS
maxtrees    = 100 # maximum number of trees
maxdepth    = None # maximum tree-depth
maxleaves   = None # maximum number of leafes per tree
#######################################################################################

#######################################################################################
# OUTPUTS
#######################################################################################
# EVALUATION
types = ['*.png','*.csv'] # used to clean figures folder when before processing data
#######################################################################################
# INFORMATIONAL OUTPUT
# color used for verbose output
vcolor = Fore.WHITE
#######################################################################################