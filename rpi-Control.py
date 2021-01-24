#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 14 13:53:04 2020

@author: pjr

datasets taken from:
    https://www.unb.ca/cic/datasets/ids-2017.html
    http://205.174.165.80/CICDataset/CIC-IDS-2017/

    only reliable way to download the complete set of PCAP-files is using -c to reconnect on read-errors:
    wget -c --timeout=20 --tries=0 <PCAP-URL>
"""

import glob
import csv
import os
import sys
import subprocess
import pandas as pd
import time as epochtime
import threading
from timeit import default_timer as timer
from pathlib import Path, PureWindowsPath



# choices for argument-parsing
# flowsampling-modes
flowsmode = {1:'every n-th packet',2:'sample & skip n packets',3:'sample first n packets of a flow',4:'sample n, skip n-1, sample n-2 ...'}
# packetsampling-modes
packetsmode = {1:'every n-th packet'}
# capture files, https://www.unb.ca/cic/datasets/ids-2017.html
filenames = {0:'All',1:'Monday-WorkingHours',2:'Tuesday-WorkingHours',3:'Wednesday-WorkingHours',4:'Thursday-WorkingHours',5:'Friday-WorkingHours'}
# feature vectors
featurevectors = {1:'AGM_10s.json', 2:'AGM_60s.json',3:'AGM_3600s.json',4:'CAIA_flowSampling.json',5:'CAIA_packetSampling.json'}

# directories
flowfolder = '/mnt/data/CIC-IDS2017/PCAP/flow-sampledCSV'
packetfolder = '/mnt/data/CIC-IDS2017/PCAP/packet-sampledCSV'


# get working directory
wd = Path.cwd()

# forge logfolder, timestamps & dstat logs based on wd
logd = wd / 'logs'
#if not os.path.exists(logd): os.mkdir(logd)
reportcsv = logd / 'report.csv'
resultcsv = logd / 'result.csv'
timecsv = logd / 'time.csv'
dstatcsv = logd / 'dstat.csv'
# sampled CSVs
fpath = wd / 'csv' / 'flow-sampled'
ppath = wd / 'csv' / 'packet-sampled'
# models
fmodeld = fpath / 'fitted'
pmodeld = ppath / 'fitted'
#modelpkl = '{}_model_{}.pkl' # placeholder for file and 32/64bit
#modelpkl = '{}_model_32bit.pkl'
modelpkl = '{}_model_64bit.pkl'

# directories for large PCAP files
flowfolder = '/mnt/data/CIC-IDS2017/PCAP/flow-sampledCSV'
packetfolder = '/mnt/data/CIC-IDS2017/PCAP/packet-sampledCSV'

# COMMANDS
# start dstat resource logging
#dstat = 'dstat --epoch --cpu-adv --disk --mem-adv --output '+dstatcsv+' > /dev/null 2>&1 &'
dstat = 'dstat --epoch --cpu-adv --disk --mem-adv --output {} > /dev/null 2>&1 &'



# ARGUMENT PARSING
import argparse
parser = argparse.ArgumentParser(description='script to execute sampling, labeling, preprocessing and classification scripts on given capture file.')
# positional arguments
parser.add_argument('file', metavar='file', type=int,nargs=1,choices=filenames, help='select file to process: {}'.format(filenames))
parser.add_argument('n', metavar='n', type=int,nargs=1,help='non-zero integer, used to determine sampling-steps')
parser.add_argument('j', metavar='j', type=int,nargs=1,help='select feature-vector: {}'.format(featurevectors))
# optional arguments
parser.add_argument('-v','--verbose', action='store_true', help='output verbose information')
parser.add_argument('--superverbose', action='store_true', help='output additional verbose informations, including loop-iteration output')
parser.add_argument('-t','--time', action='store_true', help='measure runtimes, save timestamps')
parser.add_argument('-e','--export', action='store_true', help='export timestamps & resource logs')
# force OS choice, https://docs.python.org/3/library/argparse.html#mutual-exclusion
osgroup = parser.add_mutually_exclusive_group(required=True)
osgroup.add_argument('--linux', action='store_true', help = 'use Linux paths & commands' )
osgroup.add_argument('--osx', action='store_true', help='use MacOS paths & commands')
osgroup.add_argument('--windows', action='store_true', help='use Windows paths & commands')

# force sampling method & mode
samplegroup = parser.add_mutually_exclusive_group(required=True)
samplegroup.add_argument('-f','--flowsampling', metavar='m', type=int, nargs=1, choices=flowsmode, help='select sampling-mode: {}'.format(flowsmode))
samplegroup.add_argument('-p','--packetsampling', metavar='m', type=int, nargs=1, choices=packetsmode, help='select sampling-mode: {}'.format(packetsmode))
args = parser.parse_args()


# function that start dstat
def threadFunc():
    os.system(dstat.format(dstatcsv))
    return
th = threading.Thread(target=threadFunc)


# CONTROL SCRIPT
# executes Sampling, Labeling & Classification scripts and shoule also run the performance monitoring
if __name__ == '__main__':
    
    global verbose 
    global time
    global check

    time = args.time
    # set split to 5000 packets per split-file (editcaps)
    split = 5000
    # positional arguments
    j = args.j[0]
    # optional arguments
    verbose = args.verbose
    superverbose = args.superverbose
    if superverbose: verbose = True
    linux = args.linux
    osx = args.osx
    windows = args.windows
    flowsampling = args.flowsampling
    packetsampling = args.packetsampling
    export = args.export


    if export: # remove any exisiting CSV
        for file in os.listdir(logd):
            Path.unlink(logd / file)

    if time:
        os.system('killall dstat') # kill literally any running dstat process
        start = timer()
        t = epochtime.time()
        #print('\nControl.py\n[EPOCH, start]: {}\n'.format(t))
        if export: # write timestamp to csv
            th.start() # start dstat logging
            with open(timecsv,'w') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Control.py','start'])


    # positional arguments
    # file selection (can be passed 1:1 to scripts called in main)
    findex = args.file[0]
    # sampling steps
    n = abs(args.n[0])
    if n == 0:
        print('>>> please enter non-zero integer value for n!')
        exit()

    # set arguments for chosen sampling
    if flowsampling:
        flowsampling = True
        packetsampling = False
        m = args.flowsampling[0]
        samplingmode =flowsmode[m]
    elif packetsampling:
        packetsampling = True
        flowsampling = False
        m = args.packetsampling[0]
        samplingmode = packetsmode[m]

    # COMMANDS arguments to execute Flowsampling.py or Packetsampling.py within this script
    # set argument for OS choice
    if linux: osarg = ' --linux'
    elif osx: osarg = ' --osx'
    elif windows: osarg = ' --windows'
    # set command for verbose output
    if superverbose: verbosearg = " --superverbose"
    elif verbose: verbosearg = " --verbose"
    else: verbosearg = ""
    # set command for time
    if time: timearg = " --time"
    else: timearg = ""


    # check passed optional arguments and commands
    print('\n\n'+40*' '+' FILE: {}'.format(filenames[findex]))
    print(40*'~'+' SCRIPT: Control.py '+40*'~')
    print('\n'+20*'~'+' optional arguments '+20*'~')
    print("\n{}\t--verbose\n{}\t--superverbose\n{}\t--time\n{}\t--osx\n{}\t--windows\n{}\t--flowsampling\n{}\t--packetsampling".format(verbose,superverbose,time,osx,windows,flowsampling,packetsampling))
    print('\n{}, n = {}'.format(samplingmode,n))
    print('\n'+20*'~'+' paths & files '+20*'~')
    print('\nlogs:\t{}'.format(logd))
    print('dstat:\t{}'.format(dstatcsv))
    print('times:\t{}\n'.format(timecsv))
    print('flowfolder:\t{}'.format(flowfolder))
    print('packetfolder:\t{}'.format(packetfolder))
    print('go-flows:\t{}'.format(featurevectors[j]))
    print('\n'+20*'~'+' commands '+20*'~')
    print('\ndstat:\t{}'.format(dstat))


    # SAMPLING ALL CAPTURE FILES & MERGE TO SINGLE CSV
    if findex == 0:
        # iterate over all PCAP files
        for fcount in range(1,len(filenames)):
            if flowsampling: 
                sarg = " --flowsampling "
                #m = args.flowsampling[0]
                samplearg = " "+str(m)+" "+str(fcount)+" "+str(n)
                featurearg =" "+str(j)
                samplingcmd = "python FlowSampling.py"+str(verbosearg)+str(timearg)+str(osarg)+str(samplearg)+str(featurearg)
            elif packetsampling: 
                sarg = " --packetsampling "
                #m = args.packetsampling[0]
                samplearg = " "+str(split)+" "+str(m)+" "+str(fcount)+" "+str(n)
                featurearg =" "+str(j)
                samplingcmd = "python PacketSampling.py"+str(verbosearg)+str(timearg)+str(osarg)+str(samplearg)+str(featurearg)
            
            print('\n>>> execute sampling: {}\n>>> input-file: {}'.format(samplingcmd,filenames[fcount]))
            # start sampling
            os.system(samplingcmd)

        # merge all CSVs into one single file
        # change current working directory to CSV folder to get relevant files
        if flowsampling:
            os.chdir(flowfolder)
            mergefolder = flowfolder
            info = {'file':[filenames[findex]],'flowsampling':[flowsampling],'samplingmode':[flowsmode[m]],'samplingsteps':[n],'featurevector':[featurevectors[j]]}
            info = pd.DataFrame.from_dict(info,orient='index')

        elif packetsampling:
            os.chdir(packetfolder)
            mergefolder = packetfolder
            info = {'file':[filenames[findex]],'packetsampling':[packetsampling],'samplingmode':[packetsmode[m]],'samplingsteps':[n],'featurevector':[featurevectors[j]]}
            info = pd.DataFrame.from_dict(info,orient='index')

        extension = 'csv'
        print('\n\n>>> merging sampled data into CSV...')
        # save all files matching *Hours.csv into list, these are the already labeled CSV files
        matchedfiles = [i for i in glob.glob('*Hours.{}'.format(extension))]
        # concat all labeled csv-files into single csv
        singlecsv = pd.concat([pd.read_csv(f) for f in matchedfiles])
        print('>>> saving sampled data')
        singlecsv.to_csv(str(mergefolder)+"/Merged.csv", index = False,encoding='utf-8-sig') # save merged, sampled CSV
        print('>>> saving sampling information')
        info.to_csv(str(mergefolder)+"/information.csv") # save sampling-information to CSV (to original PCAP directory)
        info.to_csv(str(logd)+"/information.csv")
        # set working directory back to actual wd for further script executions
        os.chdir(wd)


    # SAMPLING SINGLE SPECIFIC CAPTURE FILE
    else:
        # forge script execution-command out of given arguments
        if flowsampling: 
            sarg = " --flowsampling "
            #m = args.flowsampling[0]
            samplearg = " "+str(m)+" "+str(findex)+" "+str(n)
            featurearg =" "+str(j)
            samplingcmd = "python FlowSampling.py"+str(verbosearg)+str(timearg)+str(osarg)+str(samplearg)+str(featurearg)
        elif packetsampling: 
            sarg = " --packetsampling "
            #m = args.packetsampling[0]
            samplearg = " "+str(split)+" "+str(m)+" "+str(findex)+" "+str(n)
            featurearg =" "+str(j)
            samplingcmd = "python PacketSampling.py"+str(verbosearg)+str(timearg)+str(osarg)+str(samplearg)+str(featurearg)
        print('>>> execute sampling: {}'.format(samplingcmd))
        os.system(samplingcmd)



    if time:
        end = timer()
        t = epochtime.time()
        print('\nControl.py\n[EPOCH, end]: {}'.format(t))
        print('[RUNTIME]: %.3f' % (end-start),'seconds')
        if export: # write timestamp to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Control.py','end'])


    # MONITORING
    pid = os.system('pidof /usr/bin/python3 /usr/bin/dstat -sq') # get running dstat pid (-q doesn't output pid to console, -s single-shot)
    epochtime.sleep(50) # wait 50 seconds for dstat before terminating the process, seems like dstat writes its output to the target-file around every 45 seconds
    os.kill(pid,9) # kill running dstat process

    exit() # temporary exit, just to create merged sampled files











    # PRE-PROCESSING
    #preparg = " "+str(findex)
    prepcmd = "python Preprocessing.py"+str(verbosearg)+str(timearg)+str(osarg)+str(sarg)+str(findex)
    print('>>> pre-processing:\n\t{}'.format(prepcmd))
    os.system(prepcmd)


    # CLASSIFICATION
    # forge executable command + arguments
    #classificationarg = " "+str(findex)
    classificationcmd = "python Classification.py"+str(verbosearg)+str(timearg)+str(osarg)+str(sarg)+str(findex)
    print('>>> classification:\n\t{}'.format(classificationcmd))
    os.system(classificationcmd)

    if time:
        end = timer()
        t = epochtime.time()
        print('\nControl.py\n[EPOCH, end]: {}'.format(t))
        print('[RUNTIME]: %.3f' % (end-start),'seconds')
        if export: # write timestamp to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Control.py','end'])


    # MONITORING
    # get running dstat pid
    # -q ...doesn't output pid to console, -s ...single-shot, only displays 
    pid = os.system('pidof /usr/bin/python3 /usr/bin/dstat -sq')
    #pid = os.system('pidof /usr/bin/python3 /usr/bin/dstat -s')
    
    # wait 50 seconds for dstat before terminating the process, seems like dstat writes its output to the target-file around every 45 seconds
    epochtime.sleep(50)

    # kill running dstat process
    os.kill(pid,9)
    sys.exit()

