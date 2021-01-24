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



# function that start dstat
def threadFunc():
    os.system(dstat)
    #proc = subprocess.Popen(["/usr/bin/dstat","--epoch","--cpu-adv","--output /home/noooberino/control.csv"],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT,shell=True)
    #log = open('/home/noooberino/control.csv','a')
    #proc = subprocess.Popen(["/usr/bin/dstat","--epoch","--cpu-adv"],stdout=log,shell=True)

th = threading.Thread(target=threadFunc)

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
wd = os.getcwd()

# forge logfolder, timestamps & dstat logs based on wd
logfolder = wd+"/logs"
if not os.path.exists(logfolder): os.mkdir(logfolder)
dstatcsv = logfolder+"/dstat.csv"
timecsv = logfolder+"/time.csv"
# dstat command including arguments to pipe output do null and execute in background
# logs epochtime, cpu-usage, disk-usage, memory-usage and top ps
#dstat = 'dstat --epoch --cpu-adv --disk --mem-adv --top-io-adv --output '+dstatcsv+' > /dev/null 2>&1 &'
dstat = 'dstat --epoch --cpu-adv --disk --mem-adv --output '+dstatcsv+' > /dev/null 2>&1 &'
#dstat = 'dstat --epoch --cpu-adv --disk --mem-adv --top-io-adv --output /home/noooberino/control.csv &'
#dstatarg = '--epoch --cpu-adv --disk --mem-adv --top-io-adv --output /home/noooberino/control.csv > /dev/null 2>&1 &'

# ARGUMENT PARSING
import argparse
parser = argparse.ArgumentParser(description='Script to execute sampling, labeling, preprocessing and classification scripts on given capture file.')
# positional arguments
parser.add_argument('file', metavar='file', type=int,nargs=1,choices=filenames, help='select file to process: {}'.format(filenames))
parser.add_argument('n', metavar='n', type=int,nargs=1,help='non-zero integer, used to determine sampling-steps')
parser.add_argument('j', metavar='j', type=int,nargs=1,help='select feature-vector: {}'.format(featurevectors))
# optional arguments
parser.add_argument('-v','--verbose', action='store_true', help='output verbose information')
parser.add_argument('--superverbose', action='store_true', help='output additional verbose informations, including loop-iteration output')
parser.add_argument('-t','--time', action='store_true', help='measure runtimes, save timestamps')
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

    time = args.time
    if time: 
        # kill literally any running dstat process
        os.system('killall dstat')
        # start timer
        start = timer()
        # save epochtime
        t = epochtime.time()
        # start dstat logging
        th.start()
        print('\nControl.py\n[EPOCH, start]: {}\n'.format(t))
        # write timestamp to csv
        with open('/home/noooberino/timestamps.csv','w') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=",")
            csvwriter.writerow([t,'Control.py','start'])

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


    # positional arguments
    # file selection (can be passed 1:1 to scripts called in main)
    findex = args.file[0]
    # sampling steps
    n = abs(args.n[0])
    if n == 0:
        print('>>> please enter non-zero integer value for n!')
        exit()
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

    # check passed optional arguments and commands
    print('\n\n'+40*' '+' FILE: {}'.format(filenames[findex]))
    print(40*'~'+' SCRIPT: Control.py '+40*'~')
    print('\n'+20*'~'+' optional arguments '+20*'~')
    print("\n{}\t--verbose\n{}\t--superverbose\n{}\t--time\n{}\t--osx\n{}\t--windows\n{}\t--flowsampling\n{}\t--packetsampling".format(verbose,superverbose,time,osx,windows,flowsampling,packetsampling))
    print('\n{}, n = {}'.format(samplingmode,n))
    print('\n'+20*'~'+' paths & files '+20*'~')
    print('\nlogs:\t{}'.format(logfolder))
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
        # write timestamp to csv
        with open(timecsv,'a') as csvfile:
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

