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
from pathlib import Path, PureWindowsPath, PurePath, PurePosixPath
from pandas import read_csv


# choices for argument-parsing
# flowsampling-modes
flowsmode = {1:'every n-th packet',2:'sample & skip n packets',3:'sample first n packets of a flow',4:'sample n, skip n-1, sample n-2 ...'}
# packetsampling-modes
packetsmode = {1:'every n-th packet'}
# capture files, https://www.unb.ca/cic/datasets/ids-2017.html
filenames = {0:'Merged',1:'Monday-WorkingHours',2:'Tuesday-WorkingHours',3:'Wednesday-WorkingHours',4:'Thursday-WorkingHours',5:'Friday-WorkingHours'}
# feature vectors
featurevectors = {1:'AGM_10s.json', 2:'AGM_60s.json',3:'AGM_3600s.json',4:'CAIA_flowSampling.json',5:'CAIA_packetSampling.json'}


# get working directory
wd = Path.cwd()
rootd = PurePath(wd).root

# mounted disk paths for large PCAP and sampled CSVs files
mntd = Path('/mnt')
flowfolder =  mntd / 'data' / 'CIC-IDS2017' / 'PCAP' / 'flow-sampledCSV'
packetfolder = mntd / 'data' / 'CIC-IDS2017' / 'PCAP' / 'packet-sampledCSV'

# forge logfolder, timestamps & dstat logs based on wd
logd = wd / 'logs'
#if not os.path.exists(logd): os.mkdir(logd)
reportcsv = logd / 'report.csv'
resultcsv = logd / 'result.csv'
timecsv = logd / 'time.csv'
dstatcsv = logd / 'dstat.csv'


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
# measure runtimes or measure & export timestamps and dstat-logs
timegroup = parser.add_mutually_exclusive_group(required=False)
timegroup.add_argument('-t','--time', action='store_true', help='measure runtimes')
timegroup.add_argument('-e','--export', action='store_true', help='export timestamps & resource logs')
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


    split = 5000 # set split to 5000 packets per split-file (editcaps)

    j = args.j[0]

    time = args.time
    verbose = args.verbose
    superverbose = args.superverbose
    if superverbose: verbose = True
    flowsampling = args.flowsampling
    packetsampling = args.packetsampling

    linux = args.linux
    osx = args.osx
    windows = args.windows

    export = args.export
    if export:
        time = True
        print('>>> clear log-directory')
        for file in os.listdir(logd): # remove any exisiting logs in log-directory
            Path.unlink(logd / file)

    if time: # start timers
        start = timer()
        t = epochtime.time()
        if export: # save timestamps & logs
            os.system('killall dstat') # kill literally any already running dstat process
            th.start() # start dstat logging
            with open(timecsv,'w') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow(['epochtime','scriptname','segment','status']) # set labels
                csvwriter.writerow([t,'rpi-Control.py','','start'])

    # positional arguments
    findex = args.file[0]
    n = abs(args.n[0])
    if n == 0:
        print('>>> please enter non-zero integer value for n!')
        exit()

    # set arguments for chosen samplingmethod, set directory, forge info for information.csv
    if flowsampling:
        flowsampling = True
        packetsampling = False
        m = args.flowsampling[0]
        samplingmode =flowsmode[m]
        samplingd = flowfolder
        info = {'file':[filenames[findex]],'per-flow sampling':[flowsampling],'samplingmode':[flowsmode[m]],'samplingsteps':[n],'featurevector':[featurevectors[j]]}
        info = pd.DataFrame.from_dict(info,orient='index')
    elif packetsampling:
        packetsampling = True
        flowsampling = False
        m = args.packetsampling[0]
        samplingmode = packetsmode[m]
        samplingd = packetfolder
        info = {'file':[filenames[findex]],'packet sampling':[packetsampling],'samplingmode':[packetsmode[m]],'samplingsteps':[n],'featurevector':[featurevectors[j]]}
        info = pd.DataFrame.from_dict(info,orient='index')

    # forge filename & directories
    foldername =  str(filenames[findex])+str('_mode')+str(m)+str('_vector')+str(j)+str('_steps')+str(n)
    csvd = samplingd / foldername
    csvname = filenames[findex]+str('.csv')
    csvsave = csvd / csvname
    csvinfo = csvd / 'information.csv'
    goflowsconf = wd / 'go-flows-configurations' / featurevectors[j]

    scsv = samplingd / csvname
    movecmd = str('mv ')+str(scsv) +str(' ')+str(csvsave)

    if not os.path.exists(csvd): os.mkdir(csvd) # create csv-directory if it doesn't exist

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
    print('\n'+40*' '+' FILE: {}'.format(filenames[findex]))
    print(40*'~'+' SCRIPT: rpi-Control.py '+40*'~')
    print('\n'+20*'~'+' optional arguments '+20*'~')
    #print("\n{}\t--verbose\n{}\t--superverbose\n{}\t--time\n{}\t--osx\n{}\t--windows\n{}\t--flowsampling\n{}\t--packetsampling".format(verbose,superverbose,time,osx,windows,flowsampling,packetsampling))
    print("\n{}\t--verbose\n{}\t--superverbose\n{}\t--time\n{}\t--export\n{}\t--flowsampling\n{}\t--packetsampling".format(verbose,superverbose,time,export,flowsampling,packetsampling))
    print('\n{}, n = {}'.format(samplingmode,n))
    print('\n'+20*'~'+' paths & files '+20*'~')
    print('\nJSON:\t{}'.format(goflowsconf))
    print('CSV:\t{}\n\t{}'.format(csvsave,csvinfo))
    print('\nlogs:\t{}'.format(logd))
    print('dstat:\t{}'.format(dstatcsv))
    print('times:\t{}'.format(timecsv))
    print('\n'+20*'~'+' commands '+20*'~')
    print('\ndstat:\t{}'.format(dstat))


    # SAMPLE ALL CAPTURE FILES & MERGE
    if findex == 0:
        # iterate over all PCAP files
        for fcount in range(1,len(filenames)):
        #for fcount in range(1,1):
            if flowsampling: 
                sarg = " --flowsampling "
                samplearg = " "+str(m)+" "+str(fcount)+" "+str(n)
                featurearg =" "+str(j)
                #samplingcmd = "python3 rpi-FlowSampling.py"+str(verbosearg)+str(timearg)+str(osarg)+str(samplearg)+str(featurearg)
                samplingcmd = "python3 rpi-FlowSampling.py"+str(verbosearg)+str(timearg)+str(samplearg)+str(featurearg)

            elif packetsampling: 
                sarg = " --packetsampling "
                samplearg = " "+str(split)+" "+str(m)+" "+str(fcount)+" "+str(n)
                featurearg =" "+str(j)
                samplingcmd = "python3 rpi-PacketSampling.py"+str(verbosearg)+str(timearg)+str(osarg)+str(samplearg)+str(featurearg)

            print('\n>>> execute sampling: {}\n>>> input-file: {}'.format(samplingcmd,filenames[fcount]))
            os.system(samplingcmd) # start sampling

        print('\n>>> merging sampled data')
        os.chdir(samplingd) # change directory for glob usage
        extension = 'csv'
        matchedfiles = [i for i in glob.glob('*Hours.{}'.format(extension))] # save all files matching *Hours.csv into list (labeled files)
        singlecsv = pd.concat([pd.read_csv(f) for f in matchedfiles]) # concat all labeled csv-files into single csv

        print('>>> saving merged data')
        singlecsv.to_csv(csvsave, index = False,encoding='utf-8-sig')

        print('>>> saving information')
        info.to_csv(csvinfo)


    # SAMPLE SINGLE CAPTURE FILE
    else:
        # forge script execution-command out of given arguments
        if flowsampling: 
            sarg = " --flowsampling "
            samplearg = " "+str(m)+" "+str(findex)+" "+str(n)
            featurearg =" "+str(j)
            #samplingcmd = "python3 rpi-FlowSampling.py"+str(verbosearg)+str(timearg)+str(osarg)+str(samplearg)+str(featurearg)

            samplingcmd = "python3 rpi-FlowSampling.py"+str(verbosearg)+str(timearg)+str(samplearg)+str(featurearg)
        elif packetsampling: 
            sarg = " --packetsampling "
            samplearg = " "+str(split)+" "+str(m)+" "+str(findex)+" "+str(n)
            featurearg =" "+str(j)
            samplingcmd = "python3 rpi-PacketSampling.py"+str(verbosearg)+str(timearg)+str(osarg)+str(samplearg)+str(featurearg)

        print('>>> execute sampling: {}'.format(samplingcmd))
        os.system(samplingcmd)

        print('>>> saving information')
        info.to_csv(csvinfo)

        print('>>> move to folder')
        os.system(movecmd)


    # CLEANUP
    print('>>> cleanup')
    for file in Path(samplingd).glob('*.csv'): # remove csv-files from sampling directory
        #print('delete: {}'.format(file))
        Path.unlink(samplingd / file)


    if time:
        end = timer()
        t = epochtime.time()
        print('\n(rpi-Control.py, runtime: %.3f' % (end-start),'seconds)')
        if export: # write timestamp to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Control.py','','end'])

    # STOP MONITORING
    if export:
        pid = os.system('pidof /usr/bin/python3 /usr/bin/dstat -sq') # get running dstat pid (-q doesn't output pid to console, -s single-shot)
        epochtime.sleep(50) # wait 50 seconds for dstat before terminating the process, seems like dstat writes its output to the target-file around every 45 seconds
        os.kill(pid,9) # kill running dstat process (kills running script, has to be done that way since dstat is running in background)

    exit() # temporary exit, just to create merged sampled files








    ### SCRIPTS BELOW HAVE TO BE TWEAKED TO ACCESS DATA FROM FORGED PATH csvsave

    # PRE-PROCESSING
    #preparg = " "+str(findex)
    prepcmd = "python3 Preprocessing.py"+str(verbosearg)+str(timearg)+str(osarg)+str(sarg)+str(findex)
    print('>>> pre-processing:\n\t{}'.format(prepcmd))
    os.system(prepcmd)


    # CLASSIFICATION
    # forge executable command + arguments
    #classificationarg = " "+str(findex)
    classificationcmd = "python3 Classification.py"+str(verbosearg)+str(timearg)+str(osarg)+str(sarg)+str(findex)
    print('>>> classification:\n\t{}'.format(classificationcmd))
    os.system(classificationcmd)

    if time:
        end = timer()
        t = epochtime.time()
        print('\nrpi-Control.py\n\t<<< runtime: %.3f' % (end-start),'seconds')
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

