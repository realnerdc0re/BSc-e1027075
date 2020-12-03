#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 14 13:53:04 2020

@author: Patrick Resch
"""

import os
import sys

# TODO: implement hardware/performance monitoring (maybe multi-threaded?)

# choices for argument-parsing
# flowsampling-modes
flowsmode = {1:'every n-th packet',2:'sample & skip n packets',3:'sample first n packets of a flow',4:'sample n, skip n-1, sample n-2 ...'}
# packetsampling-modes
packetsmode = {1:'every n-th packet'}
# capture files, https://www.unb.ca/cic/datasets/ids-2017.html
filenames = {1:'Monday-WorkingHours',2:'Tuesday-WorkingHours',3:'Wednesday-WorkingHours',4:'Thursday-WorkingHours',5:'Friday-WorkingHours'}


# ARGUMENT PARSING
import argparse
parser = argparse.ArgumentParser(description='Script to execute sampling, labeling, preprocessing and classification scripts on given capture file.')

# positional arguments
parser.add_argument('file', metavar='file', type=int,nargs=1,choices=filenames, help='select file to process: {}'.format(filenames))
parser.add_argument('n', metavar='n', type=int,nargs=1,help='non-zero integer, used to determine sampling-steps')
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
    
    # get working directory
    wd = os.getcwd()

    
    # COMMANDS
    # set command argument for OS
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
    
    
    # SAMPLING
    # forge script execution-command out of given arguments
    if flowsampling: 
        sarg = " --flowsampling "
        m = args.flowsampling[0]
        samplearg = " "+str(m)+" "+str(findex)+" "+str(n)
        samplingcmd = "python3 FlowSampling.py"+str(verbosearg)+str(timearg)+str(osarg)+str(samplearg)
    elif packetsampling: 
        sarg = " --packetsampling "
        m = m = args.packetsampling[0]
        samplearg = " "+str(split)+" "+str(m)+" "+str(findex)+" "+str(n)
        samplingcmd = "python3 PacketSampling.py"+str(verbosearg)+str(timearg)+str(osarg)+str(samplearg)
        
    print('>>> execute sampling: {}'.format(samplingcmd))
    os.system(samplingcmd)
    
    
    # PREPROCESSING

    
    # CLASSIFICATION
    classificationarg = " "+str(findex)
    classificationcmd = "python3 Classification.py"+str(verbosearg)+str(timearg)+str(sarg)+str(findex)
    
    print('>>> execute classification: {}'.format(classificationcmd))
    os.system(classificationcmd)
        