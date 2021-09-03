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
flowfolder    = mntd / 'data' / 'CIC-IDS2017' / 'PCAP' / 'flow-sampledCSV'
packetfolder  = mntd / 'data' / 'CIC-IDS2017' / 'PCAP' / 'packet-sampledCSV'
# folder containing results, logs, temporary logs and sampled CSV for later evaluation
eflowfolder   = mntd / 'data' / 'CIC-IDS2017' / 'Experiments' / 'flow-sampledCSV'
epacketfolder = mntd / 'data' / 'CIC-IDS2017' / 'Experiments' / 'packet-sampledCSV'
# experiment configuration foldername
foldername    = '{}_mode{}_vector{}_steps{}_{}'
# logfiles
csv_dstat   = 'dstat.csv'
csv_time    = 'time.csv'
csv_result  = 'result.csv'
csv_report  = 'report.csv'
csv_info    = 'information.csv'
# working directory folders
tmp         = wd / 'tmp'
logs        = wd / 'logs'
figures     = wd / 'figures'
# full path to wd logfiles
time        = logs / csv_time
dstat       = logs / csv_dstat
result      = logs / csv_result
report      = logs / csv_report
# pickle-model
model_remote    = '{}_model_remote.pkl'
model_local     = '{}_model_local.pkl'
# framework configuration
configuration   = 'config.py'
#######################################################################################
# TOOLS
# path to executables
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
2:'AGM_60s.json',                       # unused
3:'AGM_3600s.json',                     # unused
4:'CAIA_flowSampling.json',
5:'CAIA_packetSampling.json',
6:'AGM_10s.json',
7:'AGM_60s.json',                       # unused
8:'AGM_3600s.json'                      # unused
}
#######################################################################################
# SAMPLING-MODES
# modes available for perflow- and packetsampling
fsamplingmode = {
1:'every n-th packet',
2:'sample & skip n packets',            # unused
3:'first n packets',
4:'sample n, skip n-1, sample n-2 ...'  # unused
}
psamplingmode = {
5:'every n-th packet',
6:'n out of N',                         # unused
7:'probability',
8: 'timebased'                          # unused
}
# dictionary used for automated execution
samplingmode = fsamplingmode.copy()
samplingmode.update(psamplingmode)
#######################################################################################
# TRESHOLD, change details here
# numbers marks specific limits used for plausibility on specific
# argument combinations to guarantee correct automated execution
vectorlimit     = 5 # used to make experiment plausibility check in Master.py
samplinglimit   = 5 # used to make experiment plausibility check in Master.py
modelimit       = 4 # unused
flowlimit       = 4 # used to set labeling mode in FlowSampling.py
packetlimit     = 4 # used to set labeling mode in PacketSampling.py
#######################################################################################

#######################################################################################
# EXPERIMENT CONFIGURATION
#######################################################################################
# REMOTE MACHINE
# username, IP and working directory for the remote machine
# LXC container
remotewd    = 'BSc-e1027075'
remoteuser  = 'thesis'
remoteip    = '10.10.40.209'
remote      = '{}@{}'.format(remoteuser,remoteip)
remoteconf  = '/home/{}/{}/{}'.format(remoteuser,remotewd,configuration)
#######################################################################################
# EXPERIMENTS
# files, feature-vectors, sampling-modes & sampling-steps to process
file        = [5]  # 0 to process all all workday files, 1 to 5 for workdays
vector      = [4,6]  # determines used go-flows specification file specified above
mode        = [3]  # determines applied sampling mode specified above
steps       = [9]  # value for n, 0 to process unsampled PCAP
seed        = 1000 # seed number used for random sampling
#######################################################################################
# SCRIPTS
# Principal Component Analysis
n_PCA       = 12       # unused
PCA_var     = 0.90     # explained variance to achieve with PCA components
PCA_batch   = 10**5    # batchsize used for incremental PCA
# StandardScaler
batchsize   = 10**5    # batchsize used for partial fit (default 10**5)
# CSV import
chunksize   = 10**5    # lines per chunks (default 10**5)
# Sampling
split       = 5000     # number of packets per splitfile created with editcap
# Classification
splitsize   = 25*10**4 # number of lines (flows) per file (default 25*10**4)
#######################################################################################
# RANDOM FORST CLASSIFIER
# estimators
maxtrees    = 100      # maximum number of trees
maxdepth    = None     # maximum tree-depth
maxleaves   = None     # maximum number of leafes per tree
#######################################################################################

#######################################################################################
# OUTPUTS
#######################################################################################
# EVALUATION
types = ['*.png','*.csv','*.pdf'] # used to clean figures folder when before processing data
#######################################################################################
# COLORS
# uses terminal color palette, options are:
# BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE
vcolor = Fore.GREEN
#######################################################################################


#######################################################################################
# REMOTE MACHINE
# raspberry pi zero
#remoteuser  = 'dietpi'
#remoteip    = '10.10.45.55'
#remoteip    = '192.168.178.29'
#######################################################################################