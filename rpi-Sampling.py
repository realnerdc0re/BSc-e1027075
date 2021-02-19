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


# DICTIONARIES
# available sampling-modes, used for informational outputs
flowsmode = {1:'every n-th packet',2:'sample & skip n packets',3:'sample first n packets of a flow',4:'sample n, skip n-1, sample n-2 ...'}
packetsmode = {5:'every n-th packet',6:'time-based'}
# capture files, https://www.unb.ca/cic/datasets/ids-2017.html
filenames = {0:'Merged',1:'Monday-WorkingHours',2:'Tuesday-WorkingHours',3:'Wednesday-WorkingHours',4:'Thursday-WorkingHours',5:'Friday-WorkingHours'}
# feature vectors, https://pkg.go.dev/github.com/CN-TU/go-flows
featurevectors = {1:'AGM_10s.json', 2:'AGM_60s.json',3:'AGM_3600s.json',4:'CAIA_flowSampling.json',5:'CAIA_packetSampling.json'}


# PATHS
wd = Path.cwd()
rootd = PurePath(wd).root
mntd = Path('/mnt')
flowfolder =  mntd / 'data' / 'CIC-IDS2017' / 'PCAP' / 'flow-sampledCSV' # folder containing per-flow sampled csv
packetfolder = mntd / 'data' / 'CIC-IDS2017' / 'PCAP' / 'packet-sampledCSV' # folder containing packet-sampled csv
logd = wd / 'logs'
logfolder = 'logs_Sampling'
reportcsv = logd / 'report.csv'
resultcsv = logd / 'result.csv'
timecsv = logd / 'time.csv'
dstatcsv = logd / 'dstat.csv'


# COMMANDS
# start dstat resource logging
dstat = 'dstat --epoch --cpu-adv --disk --mem-adv --swap --output {} > /dev/null 2>&1 &'.format(dstatcsv)


if not os.path.exists(logd): os.mkdir(logd)


# ARGUMENT PARSING
import argparse
parser = argparse.ArgumentParser(description='script to sample pcap files, saving labled csv into folders')
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
# force sampling method & mode
samplegroup = parser.add_mutually_exclusive_group(required=True)
samplegroup.add_argument('-f','--flowsampling', metavar='m', type=int, nargs=1, choices=flowsmode, help='select sampling-mode: {}'.format(flowsmode))
samplegroup.add_argument('-p','--packetsampling', metavar='m', type=int, nargs=1, choices=packetsmode, help='select sampling-mode: {}'.format(packetsmode))
args = parser.parse_args()


# function that start dstat
def threadFunc():
    os.system(dstat)
    return
th = threading.Thread(target=threadFunc)
# used in waiting periode before killing dstat at the end of the script
def progressBar(it, prefix="", size=60, file=sys.stdout):
    count = len(it)
    def show(j):
        x = int(size*j/count)
        file.write("%s[%s%s] %i/%i\r" % (prefix, "·"*x, " "*(size-x), j, count))
        file.flush()

    show(0)

    for i, item in enumerate(it):
        yield item
        show(i+1)

    file.write("\n")
    file.flush()
    return


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
    n = args.n[0]


    # set arguments for chosen samplingmethod, set directory, forge info for information.csv
    if flowsampling:
        flowsampling = True
        packetsampling = False
        m = args.flowsampling[0]
        samplingmode =flowsmode[m]
        samplingd = flowfolder
        info = {'file':[filenames[findex]],'per-flow sampling':[flowsampling],'samplingmode':[flowsmode[m]],'samplingsteps':[n],'featurevector':[featurevectors[j]]}
    elif packetsampling:
        packetsampling = True
        flowsampling = False
        m = args.packetsampling[0]
        samplingmode = packetsmode[m]
        samplingd = packetfolder
        info = {'file':[filenames[findex]],'packet sampling':[packetsampling],'samplingmode':[packetsmode[m]],'samplingsteps':[n],'featurevector':[featurevectors[j]]}

    info = pd.DataFrame.from_dict(info,orient='index') # df for saving sampling-informations to csv

    # forge filename & directories
    foldername = '{}_mode{}_vector{}_steps{}'.format(filenames[findex],m,j,n)
    if flowsampling: foldername = '{}_perflowsampled'.format(foldername)
    elif packetsampling: foldername = '{}_packetsampled'.format(foldername)

    csvd = samplingd / foldername
    csvname = '{}.{}'.format(filenames[findex],'csv')
    csvsave = csvd / csvname # directory where sampled CSV and logs are stored when script is finished
    csvinfo = csvd / 'information.csv' # CSV containing informations about chosen sampling
    goflowsconf = wd / 'go-flows-configurations' / featurevectors[j] # full path to selected feature-vector
    rpilogs = csvd / logfolder # directory to save all logs
    scsv = samplingd / csvname # temporary directory to store sampled CSV

    movecmd = 'mv {} {}'.format(scsv,csvsave)
    cplogs = 'cp -r {} {}/' # command to copy logs at the end of the script, using placeholders based on arguments

    if not os.path.exists(csvd): os.mkdir(csvd) # create csv-directory if it doesn't exist


    # set arguments for sampling-script execution
    if superverbose: verbosearg = '--superverbose'
    elif verbose: verbosearg = '--verbose'
    else: verbosearg = ''
    if time: timearg = '--time'
    else: timearg = ''


    # check passed optional arguments and commands
    print('\n'+40*' '+' FILE: {}'.format(filenames[findex]))
    print(40*'~'+' SCRIPT: rpi-Sampling.py '+40*'~')
    print('\n'+20*'~'+' optional arguments '+20*'~')
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
        for fcount in range(1,len(filenames)): # iterate over all PCAP files
            if flowsampling:
                #sarg = " --flowsampling "
                #samplearg = " "+str(m)+" "+str(fcount)+" "+str(n)
                samplearg = '{} {} {} {}'.format(m,fcount,n,j)
                #featurearg =" "+str(j)
                #samplingcmd = "python3 rpi-FlowSampling.py"+str(verbosearg)+str(timearg)+str(samplearg)+str(featurearg)
                samplingcmd = 'python3 rpi-FlowSampling.py {} {} {}'.format(verbosearg,timearg,samplearg)

            elif packetsampling:
                #sarg = " --packetsampling "
                #samplearg = " "+str(split)+" "+str(m)+" "+str(fcount)+" "+str(n)
                samplearg = '{} {} {} {} {}'.format(split,m,fcount,n,j)
                #featurearg =" "+str(j)
                #samplingcmd = "python3 rpi-PacketSampling.py"+str(verbosearg)+str(timearg)+str(samplearg)+str(featurearg)
                samplingcmd = 'python3 rpi-PacketSampling.py {} {} {}'.format(verbosearg,timearg,samplearg)


            print('\n>>> Execute sampling: {}\n\t> {}\n\t> {}\n\t> {}\n\t> n={}'.format(samplingcmd,filenames[fcount],featurevectors[j],samplingmode,n))
            os.system(samplingcmd) # start sampling

        print('\n>>> Merging sampled data')
        os.chdir(samplingd) # change directory for glob usage
        extension = 'csv'
        matchedfiles = [i for i in glob.glob('*Hours.{}'.format(extension))] # save all files matching *Hours.csv into list (labeled files)
        singlecsv = pd.concat([pd.read_csv(f) for f in matchedfiles]) # concat all labeled csv-files into single csv

        print('>>> Saving file {}'.format(csvsave))
        singlecsv.to_csv(csvsave, index = False,encoding='utf-8-sig')

        print('>>> Saving information {}'.format(csvinfo))
        info.to_csv(csvinfo)


    # SAMPLE SINGLE CAPTURE FILE
    else:
        # forge script execution-command out of given arguments
        if flowsampling: 
            #sarg = " --flowsampling "
            #samplearg = " "+str(m)+" "+str(findex)+" "+str(n)
            samplearg = '{} {} {} {}'.format(m,findex,n,j)
            #featurearg =" "+str(j)
            #samplingcmd = "python3 rpi-FlowSampling.py"+str(verbosearg)+str(timearg)+str(samplearg)+str(featurearg)
            samplingcmd = 'python3 rpi-FlowSampling.py {} {} {}'.format(verbosearg,timearg,samplearg)

        elif packetsampling: 
            #sarg = " --packetsampling "
            #samplearg = " "+str(split)+" "+str(m)+" "+str(findex)+" "+str(n)
            samplearg = '{} {} {} {} {}'.format(split,m,findex,n,j)
            #featurearg =" "+str(j)
            #samplingcmd = "python3 rpi-PacketSampling.py"+str(verbosearg)+str(timearg)+str(samplearg)+str(featurearg)
            samplingcmd = 'python3 rpi-PacketSampling.py {} {} {}'.format(verbosearg,timearg,samplearg)


        print('\n>>> Execute sampling: {}\n\t> {}\n\t> {}\n\t> {}\n\t> n={}'.format(samplingcmd,filenames[findex],featurevectors[j],samplingmode,n))
        os.system(samplingcmd)

        print('>>> Saving file {}'.format(csvsave))
        os.system(movecmd)

        print('>>> Saving information {}'.format(csvinfo))
        info.to_csv(csvinfo)


    # CLEANUP
    print('>>> cleanup')
    for file in Path(samplingd).glob('*.csv'): # remove csv-files from sampling directory
        Path.unlink(samplingd / file)


    if time:
        end = timer()
        t = epochtime.time()
        if export: # write timestamp to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Control.py','','end'])
        else: print('\n(rpi-Control.py, runtime: %.3f' % (end-start),'seconds)\n')


    # STOP MONITORING
    if export:
        wait = 50 # seconds to wait before killing dstat
        pids = os.popen('pidof /usr/bin/python3 /usr/bin/dstat').read() # get pids as string, containing pid from dstat process and the pid of the running script
        pids = [int(s) for s in pids.split(' ')] # convert strings to list
        mypid = os.getpid() # pid of running script
        pids.remove(mypid)

        #for i in progressBar(range(wait),'>>> Waiting for dstat (pid={}): '.format(pids[0]), wait):
        #    epochtime.sleep(1)

        print('>>> Killing dstat')
        os.kill(pids[0],9) # kill running dstat process (kills running script, has to be done that way since dstat is running in background)

        print('>>> Saving logs to folder {}'.format(rpilogs))

        if not os.path.exists(rpilogs): os.mkdir(rpilogs) # create logfolder if necessary

        for root, dirs, files in os.walk(logd):
            for filename in files: # iterate over filenames found within the wd logfolder
                log = logd / filename # full path for current logfile

                print('\t> Saving {}'.format(filename))
                os.system(cplogs.format(log,rpilogs))
        print(20*'#')

    exit()