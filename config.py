#!/usr/bin/env python
from pathlib import Path, PureWindowsPath, PurePath, PurePosixPath




#######################################################################################
# BASIC CONFIGURATION
#######################################################################################
# BASE directories
# used for proper path generation
mntd = PurePosixPath('/mnt')
wd = Path.cwd()
hd = Path.home()
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
#######################################################################################
# FOLDERS
# sampled CSVs & result logs, temporary logs in working directory
flowfolder =  mntd / 'data' / 'CIC-IDS2017' / 'PCAP' / 'flow-sampledCSV'
packetfolder = mntd / 'data' / 'CIC-IDS2017' / 'PCAP' / 'packet-sampledCSV'
logd = wd / 'logs'
time = logd / 'time.csv'
#######################################################################################
# TOOLS
# path to executable for go-flows and labeling-script
goflowspath = hd / 'Git' / 'go-flows' / 'go-flows'
labelingpath = mntd / 'data' / 'BSc-e1027075' / 'Labeling.py'
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
#######################################################################################
# TRESHOLD, change details here
# numbers marks specific limits used for plausibility on specific
# argument combinations to guarantee automated execution
vectorlimit = 5
samplinglimit = 5

flowlimit = 4 # used to set mode to 'AGM' or '5tuple' for Labeling.py
packetlimit = 4
#######################################################################################




#######################################################################################
# EXPERIMENT CONFIGURATION
#######################################################################################
# REMOTE MACHINE
# username, IP and working directory for the remote machine
remotewd = 'BSc-e1027075'
remoteuser = 'dietpi'
remoteip = '10.10.45.55'
remote = '{}@{}'.format(remoteuser,remoteip)
#######################################################################################
# EXPERIMENTS
# batchsize for preprocessing
# files, feature-vectors, sampling-modes & sampling-steps to process
batchsize = 100000
file = [3,4,5]
vector = [4]
mode = [1]
steps = [5,7]
#######################################################################################