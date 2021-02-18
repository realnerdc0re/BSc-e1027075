#!/usr/bin/env python
from pathlib import Path, PureWindowsPath, PurePath, PurePosixPath

filenames = {0:'Merged',1:'Monday-WorkingHours',2:'Tuesday-WorkingHours',3:'Wednesday-WorkingHours',4:'Thursday-WorkingHours',5:'Friday-WorkingHours'}


# ATTENTION: DONT FORGET TO COMMENT IN WAITING FOR DSTAT EXECUTION ON REAL EXPERIMENTS
# rpi-Preprocessing.py: lines 1012, 1013
# rpi-Sampling.py: lines 294, 295


'''
modes = {1:'every n-th packet',2:'sample & skip n packets',3:'sample first n packets of a flow',4:'sample n, skip n-1, sample n-2 ...',5:'every n-th packet',6:'time-based'}
filenames = {0:'Merged',1:'Monday-WorkingHours',2:'Tuesday-WorkingHours',3:'Wednesday-WorkingHours',4:'Thursday-WorkingHours',5:'Friday-WorkingHours'}
vectors = {1:'AGM_10s.json', 2:'AGM_60s.json',3:'AGM_3600s.json',4:'CAIA_flowSampling.json',5:'CAIA_packetSampling.json'}

flowsampling (in scripts)
samplingmode = {1:'every n-th packet',2:'sample & skip n packets',3:'sample first n packets of a flow',4:'sample n, skip n-1, sample n-2 ...'}

packetsampling (in scripts)
samplingmode = {5:'every n-th packet',6:'time-based'}

'''


####################################
# TRESHOLD, change details here
vectorlimit = 5
samplinglimit = 5
####################################



####################################
#BASE-FOLDERS, change details here
mntd = PurePosixPath('/mnt')
flowfolder =  mntd / 'data' / 'CIC-IDS2017' / 'PCAP' / 'flow-sampledCSV' # folder containing per-flow sampled csv
packetfolder = mntd / 'data' / 'CIC-IDS2017' / 'PCAP' / 'packet-sampledCSV' # folder containing packet-sampled csv
####################################



####################################
#REMOTE MACHINE, change details here
remotewd = 'BSc-e1027075'
remoteuser = 'dietpi'
remoteip = '10.10.45.55'
remote = '{}@{}'.format(remoteuser,remoteip)
####################################



####################################
#EXPERIMENTS, change details here
batchsize = 100000
file = [3,4,5]
vector = [4]
mode = [1]
steps = [5,7]
####################################