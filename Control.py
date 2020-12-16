#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 14 13:53:04 2020

@author: Patrick Resch

dataset taken from:
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

# dstat command including arguments to pipe output do null and execute in background
# logs epochtime, cpu-usage, disk-usage, memory-usage and top ps
dstat = 'dstat --epoch --cpu-adv --disk --mem-adv --top-io-adv --output /home/noooberino/dstat-log.csv > /dev/null 2>&1 &'
#dstat = 'dstat --epoch --cpu-adv --disk --mem-adv --top-io-adv --output /home/noooberino/control.csv &'
#dstatarg = '--epoch --cpu-adv --disk --mem-adv --top-io-adv --output /home/noooberino/control.csv > /dev/null 2>&1 &'

# function that start dstat
def threadFunc():
    os.system(dstat)
    #proc = subprocess.Popen(["/usr/bin/dstat","--epoch","--cpu-adv","--output /home/noooberino/control.csv"],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT,shell=True)
    #log = open('/home/noooberino/control.csv','a')
    #proc = subprocess.Popen(["/usr/bin/dstat","--epoch","--cpu-adv"],stdout=log,shell=True)

th = threading.Thread(target=threadFunc)

# TODO: implement hardware/performance monitoring (maybe multi-threaded?)

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

# ARGUMENT PARSING
import argparse
parser = argparse.ArgumentParser(description='Script to execute sampling, labeling, preprocessing and classification scripts on given capture file.')

# positional arguments
parser.add_argument('file', metavar='file', type=int,nargs=1,choices=filenames, help='select file to process: {}'.format(filenames))
parser.add_argument('n', metavar='n', type=int,nargs=1,help='non-zero integer, used to determine sampling-steps')
parser.add_argument('j', metavar='j', type=int,nargs=1,help='select feature-vector: {}'.format(featurevectors))
# optional arguments
parser.add_argument('-v','--verbose', action='store_true', help='output verbose information')
parser.add_argument('--superverbose', action='store_true', help='output additional verbose informations, including loop-iterations output')
parser.add_argument('-t','--time', action='store_true', help='measure runtimes')
# force OS choice, https://docs.python.org/3/library/argparse.html#mutual-exclusion
osgroup = parser.add_mutually_exclusive_group(required=True)
osgroup.add_argument('--linux', action='store_true', help = 'use Linux paths & commands' )
osgroup.add_argument('--osx', action='store_true', help='use MacOS paths & commands')
osgroup.add_argument('--windows', action='store_true', help='use Windows paths & commands')
# force sampling method & mode
samplegroup = parser.add_mutually_exclusive_group(required=True)
samplegroup.add_argument('--flowsampling', metavar='m', type=int, nargs=1, choices=flowsmode, help='select sampling-mode: {}'.format(flowsmode))
samplegroup.add_argument('--packetsampling', metavar='m', type=int, nargs=1, choices=packetsmode, help='select sampling-mode: {}'.format(packetsmode))

args = parser.parse_args()


# CONTROL SCRIPT
# executes Sampling, Labeling & Classification scripts and shoule also run the performance monitoring
if __name__ == '__main__':
    
    global verbose 
    global time
    global check

    # positional arguments
    j = args.j[0]
    # optional arguments
    verbose = args.verbose
    superverbose = args.superverbose
    if superverbose:
        verbose = True
    time = args.time
    
    linux = args.linux
    osx = args.osx
    windows = args.windows
    
    flowsampling = args.flowsampling
    packetsampling = args.packetsampling


    # kill literally any running dstat process before starting monitoring
    os.system('killall dstat')
    # starting dstat threaded
    th.start()

    if time: 
        start = timer()
        # save epochtime
        t = epochtime.time()
        print('\nControl.py\n[EPOCH, start]: {}'.format(t))

        # write timestamp to csv
        with open('/home/noooberino/timestamps.csv','w') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=",")
            csvwriter.writerow([t,'Control.py','start'])
    
    # set split to 5000 packets per split-file (editcaps)
    split = 5000
    
    # positional arguments
    # file selection (can be passed 1:1 to scripts called in main)
    findex = args.file[0]
    # sampling steps
    n = abs(args.n[0])
    if n == 0:
        print('>>> please enter non-zero integer value for n!')
        exit()
    
    # get working directory
    wd = os.getcwd()

    
    # COMMANDS
    # set optional argument for OS choice
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


    # SAMPLING ALL CAPTURE FILES & MERGE
    if findex == 0:
        # iterate over all PCAP files
        for fcount in range(1,len(filenames)):
            if flowsampling: 
                sarg = " --flowsampling "
                m = args.flowsampling[0]
                samplearg = " "+str(m)+" "+str(fcount)+" "+str(n)
                featurearg =" "+str(j)
                samplingcmd = "python FlowSampling.py"+str(verbosearg)+str(timearg)+str(osarg)+str(samplearg)+str(featurearg)
            elif packetsampling: 
                sarg = " --packetsampling "
                m = args.packetsampling[0]
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
        elif packetsampling:
            os.chdir(packetfolder)
            mergefolder = packetfolder
        extension = 'csv'
        print('\n\n>>> merging sampled data into CSV...')
        # save all files matching *Hours.csv into list, these are the already labeled CSV files
        matchedfiles = [i for i in glob.glob('*Hours.{}'.format(extension))]
        # concat all labeled csv-files into single csv
        singlecsv = pd.concat([pd.read_csv(f) for f in matchedfiles])
        singlecsv.to_csv(str(mergefolder)+"/Merged.csv", index = False,encoding='utf-8-sig')
        # set working directory back to actual wd for further script executions
        os.chdir(wd)


    # SAMPLING SPECIFIC CAPTURE FILE
    else:
        # forge script execution-command out of given arguments
        if flowsampling: 
            sarg = " --flowsampling "
            m = args.flowsampling[0]
            samplearg = " "+str(m)+" "+str(findex)+" "+str(n)
            featurearg =" "+str(j)
            samplingcmd = "python FlowSampling.py"+str(verbosearg)+str(timearg)+str(osarg)+str(samplearg)+str(featurearg)
        elif packetsampling: 
            sarg = " --packetsampling "
            m = args.packetsampling[0]
            samplearg = " "+str(split)+" "+str(m)+" "+str(findex)+" "+str(n)
            featurearg =" "+str(j)
            samplingcmd = "python PacketSampling.py"+str(verbosearg)+str(timearg)+str(osarg)+str(samplearg)+str(featurearg)
        print('>>> execute sampling: {}'.format(samplingcmd))
        os.system(samplingcmd)


    # PREPROCESSING


    # CLASSIFICATION
    # forge executable command + arguments
    classificationarg = " "+str(findex)
    classificationcmd = "python Classification.py"+str(verbosearg)+str(timearg)+str(osarg)+str(sarg)+str(findex)
    print('>>> execute classification: {}'.format(classificationcmd))
    os.system(classificationcmd)

    if time:
        end = timer()
        t = epochtime.time()
        print('\nControl.py\n[EPOCH, end]: {}'.format(t))
        print('[RUNTIME]: %.3f' % (end-start),'seconds')
        # write timestamp to csv
        with open('/home/noooberino/timestamps.csv','a') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=",")
            csvwriter.writerow([t,'Control.py','end'])


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

