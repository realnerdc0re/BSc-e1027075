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


import config as cfg # necessary configurations from config.py

# create base-folders if necessary
if not os.path.exists(cfg.logs):            os.mkdir(cfg.logs)
if not os.path.exists(cfg.fpath):           os.mkdir(cfg.fpath)
if not os.path.exists(cfg.packetfolder):    os.mkdir(cfg.packetfolder)
if not os.path.exists(cfg.flowfolder):      os.mkdir(cfg.flowfolder)



# ARGUMENT PARSING
import argparse
parser = argparse.ArgumentParser(description='script to sample pcap files, saving labled csv into folders')
# positional arguments
parser.add_argument('file', metavar='file', type=int,nargs=1,choices=cfg.filenames, help='select file to process: {}'.format(cfg.filenames))
parser.add_argument('n', metavar='n', type=int,nargs=1,help='non-zero integer, used to determine sampling-steps')
parser.add_argument('j', metavar='j', type=int,nargs=1,help='select feature-vector: {}'.format(cfg.vectors))
# optional arguments
parser.add_argument('-v','--verbose', action='store_true', help='output verbose information')
parser.add_argument('--superverbose', action='store_true', help='output additional verbose informations, including loop-iteration output')
# measure runtimes or measure & export timestamps and dstat-logs
timegroup = parser.add_mutually_exclusive_group(required=False)
timegroup.add_argument('-t','--time', action='store_true', help='measure runtimes')
timegroup.add_argument('-e','--export', action='store_true', help='export timestamps & resource logs')
# force sampling method & mode
samplegroup = parser.add_mutually_exclusive_group(required=True)
samplegroup.add_argument('-f','--flowsampling', metavar='m', type=int, nargs=1, choices=cfg.fsamplingmode, help='select sampling-mode: {}'.format(cfg.fsamplingmode))
samplegroup.add_argument('-p','--packetsampling', metavar='m', type=int, nargs=1, choices=cfg.psamplingmode, help='select sampling-mode: {}'.format(cfg.psamplingmode))
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

    # set variables given in config.py
    split = cfg.split

    # set boolean variables based on argument passing
    time            = args.time
    export          = args.export
    verbose         = args.verbose
    superverbose    = args.superverbose
    flowsampling    = args.flowsampling
    packetsampling  = args.packetsampling
    if superverbose: verbose = True

    findex  = args.file[0]
    n       = args.n[0]
    j       = args.j[0]

    if export:
        time = True
        print('>>> clear log-directory')
        for file in Path(cfg.logs).glob('*.csv'): # remove csv-files from sampling directory
            Path.unlink(file)

    # set samplingmode and flags for further processing, create info
    if flowsampling:
        flowsampling    = True
        packetsampling  = False
        m               = args.flowsampling[0]
        samplingmode    = cfg.fsamplingmode[m]
        samplingfolder  = cfg.flowfolder

        info            = {
        'file':             [cfg.filenames[findex]],
        'per-flow sampling':[flowsampling],
        'samplingmode':     [cfg.fsamplingmode[m]],
        'samplingsteps':    [n],
        'featurevector':    [cfg.vectors[j]]
        }
    elif packetsampling:
        packetsampling  = True
        flowsampling    = False
        m               = args.packetsampling[0]
        samplingmode    = cfg.psamplingmode[m]
        samplingfolder  = cfg.packetfolder

        info = {
        'file':             [cfg.filenames[findex]],
        'packet sampling':  [packetsampling],
        'samplingmode':     [cfg.psamplingmode[m]],
        'samplingsteps':    [n],
        'featurevector':    [cfg.vectors[j]]
        }

    # df for saving sampling-informations to csv
    info = pd.DataFrame.from_dict(info,orient='index')

    # forge specific foldername
    folder = '{}_mode{}_vector{}_steps{}'.format(cfg.filenames[findex],m,j,n)
    if flowsampling: folder = '{}_perflowsampled'.format(folder)
    elif packetsampling: folder = '{}_packetsampled'.format(folder)

    # FILES, PATHS & COMMANDS
    wd = Path.cwd() # working directory

    # directories & files
    csv_name = '{}.csv'.format(cfg.filenames[findex])
    csv_folder  = samplingfolder / folder
    csv_tmp     = samplingfolder / csv_name # temporary location of sampled CSV returned from called scripts
    csv_save    = csv_folder / csv_name # correct location of sampled CSV.
    csv_info    = csv_folder / 'information.csv' # CSV containing informations about chosen sampling
    logs        = csv_folder / 'logs_Sampling' # directory to save all logs

    # commands
    goflowsconf = wd / cfg.vectorfolder / cfg.vectors[j] # full path to selected feature-vector
    dstat       = 'dstat --epoch --cpu-adv --disk --mem-adv --swap --output {} > /dev/null 2>&1 &'.format(cfg.dstat)
    movecmd     = 'mv {} {}'.format(csv_tmp,csv_save) # moves returned sampled CSV into correct folder
    cplogs      = 'cp -r {} {}/' # command to copy logs at the end of the script, using placeholders based on arguments

    if not os.path.exists(csv_folder): os.mkdir(csv_folder) # create csv-directory if it doesn't exist

    # set arguments for sampling-script execution
    if superverbose:    verbosearg = '--superverbose'
    elif verbose:       verbosearg = '--verbose'
    else:               verbosearg = ''

    if time:            timearg = '--time'
    else:               timearg = ''


    if time: # start timers
        start = timer()
        t = epochtime.time()
        if export: # save timestamps & logs
            os.system('killall dstat') # kill literally any already running dstat process
            th.start() # start dstat logging
            with open(cfg.time,'w') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow(['epochtime','scriptname','segment','status']) # set labels
                csvwriter.writerow([t,'rpi-Control.py','','start'])


    # check passed optional arguments and commands
    print('\n'+40*' '+' FILE: {}'.format(cfg.filenames[findex]))
    print(40*'~'+' SCRIPT: rpi-Sampling.py '+40*'~')
    print('\n'+20*'~'+' optional arguments '+20*'~')
    print("\n{}\t--verbose\n{}\t--superverbose\n{}\t--time\n{}\t--export\n{}\t--flowsampling\n{}\t--packetsampling".format(verbose,superverbose,time,export,flowsampling,packetsampling))
    print('\n{}, n = {}'.format(samplingmode,n))
    print('\n'+20*'~'+' paths & files '+20*'~')
    print('\nJSON:\t{}'.format(goflowsconf))
    print('CSV:\t{}\n\t{}'.format(csv_save,csv_info))
    print('\nlogs:\t{}'.format(cfg.logs))
    print('dstat:\t{}'.format(cfg.dstat))
    print('times:\t{}'.format(cfg.time))
    print('\n'+20*'~'+' commands '+20*'~')
    print('\ndstat:\t{}'.format(dstat))


    # SAMPLE ALL CAPTURE FILES & MERGE
    if findex == 0:
        for fcount in range(1,len(cfg.filenames)): # iterate over all PCAP files
            if flowsampling:
                samplearg   = '{} {} {} {}'.format(m,fcount,n,j)
                samplingcmd = 'python3 rpi-FlowSampling.py {} {} {}'.format(verbosearg,timearg,samplearg)

            elif packetsampling:
                samplearg   = '{} {} {} {} {}'.format(split,m,fcount,n,j)
                samplingcmd = 'python3 rpi-PacketSampling.py {} {} {}'.format(verbosearg,timearg,samplearg)


            print('\n>>> Execute sampling: {}\n\t> {}\n\t> {}\n\t> {}\n\t> n={}'.format(samplingcmd,cfg.filenames[fcount],cfg.vectors[j],samplingmode,n))
            os.system(samplingcmd) # start sampling

        print('\n>>> Merging sampled data')
        os.chdir(samplingfolder) # change directory for glob usage
        matchedfiles = [i for i in glob.glob(cfg.pattern)] # save labeled files matching pattern into list
        singlecsv = pd.concat([pd.read_csv(f) for f in matchedfiles]) # concat all labeled files into single CSV

        print('>>> Saving file {}'.format(csv_save))
        singlecsv.to_csv(csv_save, index = False,encoding='utf-8-sig')

        print('>>> Saving information {}'.format(csv_info))
        info.to_csv(csv_info)


    # SAMPLE SINGLE CAPTURE FILE
    else:
        # forge script execution-command out of given arguments
        if flowsampling: 
            samplearg   = '{} {} {} {}'.format(m,findex,n,j)
            samplingcmd = 'python3 rpi-FlowSampling.py {} {} {}'.format(verbosearg,timearg,samplearg)

        elif packetsampling: 
            samplearg   = '{} {} {} {} {}'.format(split,m,findex,n,j)
            samplingcmd = 'python3 rpi-PacketSampling.py {} {} {}'.format(verbosearg,timearg,samplearg)


        print('\n>>> Execute sampling: {}\n\t> {}\n\t> {}\n\t> {}\n\t> n={}'.format(samplingcmd,cfg.filenames[findex],cfg.vectors[j],samplingmode,n))
        os.system(samplingcmd)

        print('>>> Saving file {}'.format(csv_save))
        os.system(movecmd)

        print('>>> Saving information {}'.format(csv_info))
        info.to_csv(csv_info)


    # CLEANUP
    print('>>> cleanup')
    for file in Path(samplingfolder).glob('*.csv'): # remove csv-files from sampling directory
        Path.unlink(file)


    if time:
        end = timer()
        t = epochtime.time()
        if export: # write timestamp to csv
            with open(cfg.time,'a') as csvfile:
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

        print('>>> Saving logs to folder {}'.format(logs))

        if not os.path.exists(logs): os.mkdir(logs) # create logfolder if necessary

        for root, dirs, files in os.walk(cfg.logs):
            for filename in files: # iterate over filenames found within the wd logfolder
                log = cfg.logs / filename # full path for current logfile

                print('\t> Saving {}'.format(filename))
                os.system(cplogs.format(log,logs))
        print(20*'#')

    exit()