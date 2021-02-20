#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 11 09:25:55 2020

@author: pjr
"""

from timeit import default_timer as timer
from pathlib import Path, PureWindowsPath, PurePath, PurePosixPath
from colorama import Fore, Style

import time as epochtime
import numpy as np
import pandas as pd
import csv
import subprocess
import os
import sys


import config as cfg # necessary configurations from config.py

# create base-folders if necessary
if not os.path.exists(cfg.logs):            os.mkdir(cfg.logs)
if not os.path.exists(cfg.fpath):           os.mkdir(cfg.fpath)
if not os.path.exists(cfg.packetfolder):    os.mkdir(cfg.packetfolder)


# ARGUMENT PARSING
# command line argument passthrough for better usability
import argparse
parser = argparse.ArgumentParser(description='script for sampling PCAP files via editcaps (packetsampling), output is CSV')
# positional arguments
parser.add_argument('split', metavar='split', type=int,nargs=1,help='integer used to determine the split-size for PCAP files')
parser.add_argument('mode', metavar='mode', type=int, nargs=1, help='choose samplign mode: {}'.format(cfg.psamplingmode))
parser.add_argument('file', metavar='file', type=int,nargs=1,help='select file to process: {}'.format(cfg.filenames))
parser.add_argument('n', metavar='n', type=int,nargs=1,help='integer used to determine sampling steps')
parser.add_argument('j', metavar='j', type=int,nargs=1,help='choose feature-vector: {}'.format(cfg.vectors))
# optional arguments
parser.add_argument('-v','--verbose', action='store_true', help='output additional informations')
parser.add_argument('--superverbose', action='store_true', help='output additional informations, including loop iteration output')
parser.add_argument('-t','--time', action='store_true', help='measure function-runtimes')
parser.add_argument('-c','--check', action='store_true', help='check if number of sampled packets is correct')
args = parser.parse_args()


# FUNCTIONS
# returns list of features that contains multiple packet-values based on feature-keyword
def perpacketFeatures(dataset,keyword,verbose=False,time=False):
    
    # get all features from given dataset
    features = dataset.columns
    tmp = []
    
    if verbose:
        print('\n'+40*'~'+' FUNCTION: perpacketFeatures, all features '+40*'~')
        print('\n',features)
    
    print('\n'+40*'~'+' FUNCTION: perpacketFeatures, comparison '+40*'~')
    for feature in features:
        print(feature)
        if feature[0:len(keyword)] == keyword:
            print('...added\n')
            tmp.append(feature)
        else:
            print('...discarded\n')
    
    if verbose:
        print('\n'+40*'~'+' FUNCTION: perpacketFeatures, summary '+40*'~')
        print('\nper-packet features:\n', tmp)
        if (not time): input('\n...')
            
    return tmp
# returns formatted list for increased visibility in verbose output
def packetOutput(plist,n,verbose):
    
    tmp = []
    
    # creates list containing two elements (first and last n packets of given list) 
    tmp = [plist[0:n],plist[-n:]]
    
    for i in range(0,2):
        tmp[i] = [str(int) for int in tmp[i]]
        tmp[i] = " ".join(tmp[i])
    
    if verbose:
        print('\n\n\n'+40*'~'+' FUNCTION: packetOutput '+40*'~')
        print('\npacket-list, length:\n{}'.format(len(plist)))
        print('\npacket-list, content:\n{}'.format(plist))
        print('\npacket-list, formatted:\n{}'.format(tmp))
        if (not time): input('\n...')
    
    return tmp


if __name__ == '__main__':

    global verbose
    global time
    global check

    # set boolean variables based on argument passing
    verbose         = args.verbose
    superverbose    = args.superverbose
    time            = args.time
    check           = args.check
    if superverbose: verbose = True

    split   = args.split[0] # split size for editcap splits
    findex  = args.file[0] # file-index
    mode    = args.mode[0] # sampling-mode
    n       = args.n[0] # sampling steps
    j       = args.j[0] # feature-vector

    if time:
        start = timer()
        t = epochtime.time()
        with open(cfg.time,'a') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=",")
            csvwriter.writerow([t,'rpi-PacketSampling.py',cfg.filenames[findex],'start'])

    # set mode for later labeling.py
    if j<cfg.packetlimit: labelmode = 'AGM'
    elif j >= cfg.packetlimit: labelmode = '5tuple'


    # FILES, PATHS & COMMANDS
    wd = Path.cwd() # working directory

    # filenames
    pcap            = '{}.pcap'.format(cfg.filenames[findex]) # PCAP file to process
    pcap_snap       = '{}.pcap'.format(cfg.filenames[findex])
    pcap_split      = '{}_split.pcap'.format(cfg.filenames[findex])
    pcap_sampled    = '{}_sampled.pcap'.format(cfg.filenames[findex]) # sampled PCAP
    csv_sampled     = '{}_unlabeled.csv'.format(cfg.filenames[findex]) # sampled CSV

    # directories
    snap_folder         = cfg.fpath / 'snapPCAP'
    split_folder        = cfg.fpath / 'splitPCAP'
    sample_folder       = cfg.fpath / 'sampledPCAP'
    if not os.path.exists(snap_folder):      os.mkdir(snap_folder)
    if not os.path.exists(split_folder):     os.mkdir(split_folder)
    if not os.path.exists(sample_folder):   os.mkdir(sample_folder)

    # full paths to files
    pcap                = cfg.fpath / pcap
    pcap_snap           = snap_folder / pcap_snap
    pcap_split          = split_folder / pcap_split
    pcap_sampled        = sample_folder / pcap_sampled
    csv_sampled_export  = cfg.packetfolder / csv_sampled

    # commands
    goflowsconf     = wd / cfg.vectorfolder / cfg.vectors[j]
    goflowscmd      = '{} run features {} export csv {} source libpcap {}'.format(cfg.goflowspath,goflowsconf,csv_sampled_export,pcap_sampled)
    labelingcmd     = 'python3 {} {} {}'.format(cfg.labelingpath,cfg.packetfolder/cfg.filenames[findex],labelmode)

    cleansplitPCAP  = 'rm {}/*'.format(cfg.fpath/'splitPCAP')
    editsplitcmd    = 'editcap -c {} {} {}'.format(split,pcap_snap,pcap_split)
    capinfoscmd     = r'capinfos -M -c {} | grep packets'.format(pcap)
    editsnapcmd     = 'editcap -s 127 {} {}'.format(pcap,pcap_snap)
    mergecapcmd     = 'mergecap -F pcap {}/* -w {}'.format(split_folder,pcap_sampled)


    # INFORMATIONAL OUTPUT
    # check passed optional arguments, filepaths and forged commands
    print('\n\n'+40*' '+' FILE: {}'.format(cfg.filenames[findex]))
    print(40*'~'+' SCRIPT: rpi-PacketSampling.py '+40*'~')
    print('\n'+20*'~'+' optional arguments '+20*'~')
    print("\n{}\t--verbose\n{}\t--superverbose\n{}\t--time\n{}\t--check".format(verbose,superverbose,time,check))
    print('\n{}, n = {}, split = {}'.format(cfg.psamplingmode[mode],n,split))
    print('\n'+20*'~'+' paths '+20*'~')
    print('\nJSON:\t{}'.format(goflowsconf))
    print('PCAP:\t{}\n\t{}\n\t{}\n\t{}'.format(pcap,pcap_snap,pcap_split,pcap_sampled))
    print('CSVs:\t{}\n\t{}'.format(csv_sampled_export,cfg.packetfolder/cfg.filenames[findex]))
    print('\nlogs:\t{}'.format(cfg.logs))
    print('times:\t{}'.format(cfg.time))
    print('\n'+20*'~'+' commands '+20*'~')
    print('\npacket-count: {}'.format(capinfoscmd))
    print('drop payload: {}'.format(editsnapcmd))
    print('clear folder: {}'.format(cleansplitPCAP))
    print('split PCAP: {}'.format(editsplitcmd))
    print('merge splits: {}'.format(mergecapcmd))
    print ('go-flows: {}'.format(goflowscmd))
    print('labeling: {}\n\n'.format(labelingcmd))


    if check: # calculate sampled packet-count for basic result verification
        print('>>> Calculating packet-count for result verification')
        totalpacketcount = subprocess.check_output(capinfoscmd, shell=True, universal_newlines=True)
        for word in totalpacketcount.split():
            if word.isdigit():
                totalpacketcount = int(word) # total number of packets in pcap
                totalpackets = np.arange(1,totalpacketcount+1,1) # create numpy array from total packet count for easy determination of sampled packet count
                totalsamplecount = len(totalpackets[0::n])
                print('\t< {}\n\t< {} packets total\n\t< {} packets sampled'.format(capinfoscmd,totalpacketcount,totalsamplecount))


    # DROP PAYLOAD
    print('>>> Dropping payload: {}'.format(editsnapcmd))
    os.system(editsnapcmd)


    # CLEAN SPLIT-FOLDER
    print('>>> Cleaning folder: {}'.format(cleansplitPCAP))
    os.system(cleansplitPCAP)


    # CREATE SPLIT-FILES
    print('>>> Splitting PCAP: {}'.format(editsplitcmd))
    os.system(editsplitcmd)


    # SAMPLING
    splitlist = os.listdir(split_folder) # get a list of all files in split-directory
    splitlist.sort() # sort list alphabetically, depending on OS you won't get a sorted list of files!
    splitcount = len(splitlist)

    # various variables to determine necessary packet-skips for sampling on split-file transition
    packetskip = 0
    samplepstart = 0
    nextpacketskip = 0
    nextsamplepstart = 0
    scount = 0 # iteration counter

    print('>>> Applying packet sampling')
    for file in splitlist: # iterate over every splitted file

        scount += 1
        if ((scount % 100) == 0) or (scount == 1) or (scount == splitcount): # limit informational output to first, every 100 splitfiles and last file
            print('\t> [{}/{}] {}'.format(scount,splitcount,file))

        # create capinfos command to gather packet count (pcount) of current split-file
        infosplit = split_folder / file
        capinfosplitcmd = r'capinfos -M -c {} | grep packets'.format(infosplit)
        pcount = subprocess.check_output(capinfosplitcmd, shell=True, universal_newlines=True)

        for word in pcount.split():
            if word.isdigit(): pcount = int(word)

        packetskip = nextpacketskip # skips for current split-file based on last iteration
        samplepcount = pcount - packetskip # packets to sample in current iteration, considering skips

        plist = np.arange(1,pcount+1,1) # array containing original packets numbers of current iterations file (readability in verbose)
        plistindex = np.arange(0,pcount,1) # same array, containing packet-indices


        #if mode == 1: # every n-th packet, including first packet of the pcap
        if mode == 5: # every n-th packet, including first packet of the pcap

            modulo = samplepcount % n

            if modulo != 0:
                nextpacketskip = n - modulo # number of packets to skip in next iteration
                nextsamplepstart = nextpacketskip
            else:
                nextpacketskip = 0
                nextsamplepstart = 0

            if verbose:
                print('\n\n\t'+20*'~'+' {} '.format(file)+20*'~')
                print('\n\t< {} skipped packets, this iteration'.format(packetskip))
                print('\t< {} skipped packets, next iteration'.format(nextpacketskip))

            pskip = plist[packetskip:] # array already considering packets to skip from last iteration
            psample = plistindex[packetskip::n] # index-numbers of packets to sample in current iteration
            psamplenumber = plist[packetskip::n] # packet-number of packets to sample in current iteration (readability in verbose)
            pdrop = np.delete(plist,psample.tolist()) # packets to drop in current iteration via editcap

            if verbose: # verbose output for improved sampling comprehension
                print('\n\t'+10*'~'+' sampling '+10*'~')
                pprint = packetOutput(plist,10,False) # generates list-styled packet output for better readability
                print('\n\t< Original, {} packets\n\t< [{} ... {}]'.format(len(plist),str(pprint[0]),str(pprint[1])))
                pprint = packetOutput(pskip,10,False)
                print('\n\t< Iteration, {} packets\n\t< [{} ... {}]'.format(len(pskip),str(pprint[0]),str(pprint[1])))
                pprint = packetOutput(psamplenumber,10,False)
                print('\n\t< Sampled: {} packets\n\t< [{} ... {}]'.format(len(psamplenumber),str(pprint[0]),str(pprint[1])))
                pprint = packetOutput(pdrop,10,False)
                print('\n\t< Dropped: {} packets\n\t< [{} ... {}]'.format(len(pdrop),str(pprint[0]),str(pprint[1])))

            pdrop = np.flip(pdrop) # flip the list to drop packets via editcap, starting from the end
            iteration = int(len(pdrop)/512)+1 # number of iterations until all packets are dropped, 512 packets per slice is a limiting factor from editcap

            for i in range(0,iteration):
                pslice = pdrop[0:512] # create a slice of 512 packets to remove with editcaps
                pdrop = pdrop[512:] # remove these 512 packets from droplist for next iteration

                if superverbose: # detailed output for dropped packets via editcap
                    print('\n\t\t'+10*'~'+' packet removal {}/{} '.format(i+1,iteration)+10*'~')
                    pprint = packetOutput(pslice,10,False)
                    print('\n\t\t<< Dropping, {} packets\n\t\t<< [{} ... {}]'.format(len(pslice),str(pprint[0]),str(pprint[1])))

                    if i < (iteration-1): # only display remaining packets until last iteration
                        pprint = packetOutput(pdrop,10,False)
                        print('\n\t\t<< Remaining, {} packets\n\t\t<< [{} ... {}]'.format(len(pdrop),str(pprint[0]),str(pprint[1])))  

                arg = [str(int) for int in pslice] # create string containing packet numbers to drop, seperated with whitespaces as argument for editcap execution
                arg = " ".join(arg)

                tmpsplitfile = split_folder / file # split-file in current iteration to process with editcap
                tmpfile = split_folder / 'tmp.pcap' # temporary file tmp.pcap created with editcap
                editcapcmd = 'editcap {} {} {}'.format(tmpsplitfile,tmpfile,arg) # editcap command to execute
                os.system(editcapcmd)

                movecmd = r'mv {} {} > NUL'.format(tmpfile,tmpsplitfile) # replace split-file with sampled temporary file
                os.system(movecmd)


    # MERGE split-files
    print('>>> Merging split-files: {}'.format(mergecapcmd))
    os.system(mergecapcmd)


    # VERIFICATION
    if check: # compare real sampled packet-count with calculated packet-count for basic result verification
        print('>>> Verifying sampled packet-count')
        capinfoscmd = r'capinfos -M -c {} | grep packets'.format(pcap_sampled)
        samplepacketcount = subprocess.check_output(capinfoscmd, shell=True, universal_newlines=True)
        for word in samplepacketcount.split():
            if word.isdigit():
                samplepacketcount = int(word)
                if samplepacketcount == totalsamplecount: print(Fore.GREEN+'\t< {}\n\t< {} packets sampled\n\t< {} packets calculated\n\t< Verification SUCCEEDED'.format(capinfoscmd,samplepacketcount,totalsamplecount)+Style.RESET_ALL)
                else: print(Fore.RED+'\t< {} packets sampled\n\t< {} packets calculated\n\t< Verification FAILED'.format(samplepacketcount,totalsamplecount)+Style.RESET_ALL)


    # FLOW-CREATION
    print('>>> Create flows with go-flows from {}'.format(csv_sampled_export))
    os.system(goflowscmd) # execute go-flows to process passed packet-sampled PCAP file


    # LABELING
    if verbose: print('>>> Labeling: {}'.format(labelingcmd))
    os.system(labelingcmd)

    if time:
        end = timer()
        t = epochtime.time()
        print('\n(rpi-PacketSampling.py, runtime: %.3f' % (end-start),'seconds)\n')
        with open(cfg.time,'a') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=",")
            csvwriter.writerow([t,'rpi-PacketSampling.py',cfg.filenames[findex],'end'])

    exit()