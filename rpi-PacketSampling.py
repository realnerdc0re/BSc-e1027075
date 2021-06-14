#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 11 09:25:55 2020

@author: pjr
"""

from pandas import read_csv
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
# set/reset options for maximum columns to display and floating point output precision
def poptions():
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', 10)
    pd.set_option('display.precision',3)
    return
def resetpoptions():
    pd.reset_option('display.max_columns', 15)
    pd.reset_option('display.max_rows', 15)
    pd.reset_option('display.precision', 6)
    return
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
        print(cfg.vcolor+'\n\n\n'+40*'~'+' FUNCTION: packetOutput '+40*'~')
        print('\npacket-list, length:\n{}'.format(len(plist)))
        print('\npacket-list, content:\n{}'.format(plist))
        print('\npacket-list, formatted:\n{}'.format(tmp)+Style.RESET_ALL)
        if (not time): input(cfg.vcolor+'\n...'+Style.RESET_ALL)
    
    return tmp
# encode combinations of tcp flags
def tcpflagEncoder(dataset,feature,verbose=False):

    if verbose:
        print(cfg.vcolor+'\n'+40*'~'+' FUNCTION: tcpflagEncoder '+40*'~')
        print('\ntcpFlags: {}\n\npre-encoding: \n{}'.format(cfg.tcpflags,dataset[feature])+Style.RESET_ALL)

    for i in range(0,len(dataset.index)):
        cell = dataset[feature][i] # current cell

        if isinstance(cell,str):
            value = 0
            for char in cell:
                value += cfg.tcpflags[char]

            dataset.at[i,feature] = int(str(value),2) # convert (pseudo) binary to decimal
            #dataset.at[i,feature] = value # use number as decimal instead of binary to decimal conversion

    if verbose: print(cfg.vcolor+'\npost-encoding:\n{}'.format(dataset[feature])); input('...\n'+Style.RESET_ALL)

    return
# encode tcp flags into separate features
def tcpflagEncoder2(dataset,feature,verbose=False):
    if verbose:
        print(cfg.vcolor+'\n'+40*'~'+' FUNCTION: tcpflagEncoder '+40*'~')
        print('\ntcpFlags: {}\n\npre-encoding: \n{}'.format(cfg.tcpflags,dataset[feature])+Style.RESET_ALL)

    # create features for all possible TCP flags, initialized with 0
    flags = ['tcp ACK','tcp PSH','tcp FIN','tcp RST','tcp SYN','tcp URG','tcp ECE','tcp CWR','tcp NS']
    dataset[flags] = 0

    printdata(dataset)
    input('::::')


    return
# import CSV as pandas dataframe
def importCSV(csvpath,csvusecols=None,verbose=False,encoding='utf-8'):
    # informational output
    if verbose: print('\n\n'+40*'~'+' FUNCTION: importCSV '+40*'~')
    print('\n>>> Importing {}'.format(csvpath))
    csvdata = read_csv(csvpath,usecols=csvusecols,skipinitialspace=True,encoding=encoding)
    return csvdata
# outputs basic datset informations
def printdata(dataset,heading,verbose=False):
    print('\n'+40*'~'+' FUNCTION: printdata, {} '.format(heading) +40*'~'+'\n')
    print('< Columns:\n{}\n'.format(dataset.columns))
    print('< Dataset:\n{}\n'.format(dataset))
    print('{}\n'.format(dataset.describe()))
    return


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
    if j<cfg.packetlimit or j>5: labelmode = 'AGM'
    elif j >= cfg.packetlimit: labelmode = '5tuple'


    # FILES, PATHS & COMMANDS
    wd = Path.cwd() # working directory

    # filenames
    pcap            = '{}.pcap'.format(cfg.filenames[findex]) # PCAP file to process
    pcap_snap       = '{}.pcap'.format(cfg.filenames[findex])
    pcap_split      = '{}_split.pcap'.format(cfg.filenames[findex])
    pcap_sampled    = '{}_sampled.pcap'.format(cfg.filenames[findex]) # sampled PCAP
    csv_sampled     = '{}_unlabeled.csv'.format(cfg.filenames[findex]) # sampled CSV

    csv_file        = cfg.packetfolder / csv_sampled

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
    if n ==0: pcap_sampled = pcap # point to original pcap instead of sampled capture


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

    if n != 0:
        if check: # calculate sampled packet-count for basic result verification
            print('>>> Calculating packet-count for result verification')
            totalpacketcount = subprocess.check_output(capinfoscmd, shell=True, universal_newlines=True)
            for word in totalpacketcount.split():
                if word.isdigit():
                    totalpacketcount = int(word) # total number of packets in pcap
                    totalpackets = np.arange(1,totalpacketcount+1,1)
                    totalsamplecount = len(totalpackets[0::n])
                    print('\t< {}\n\t< {} packets total\n\t< {} packets sampled'.format(capinfoscmd,totalpacketcount,totalsamplecount))


        # DROP PAYLOAD from every packet
        print('>>> Dropping payload: {}'.format(editsnapcmd))
        os.system(editsnapcmd)

        # CLEAN SPLIT-FOLDER
        print('>>> Cleaning folder: {}'.format(cleansplitPCAP))
        os.system(cleansplitPCAP)

        # CREATE SPLIT-FILES
        print('>>> Splitting PCAP: {}'.format(editsplitcmd))
        os.system(editsplitcmd)

        # SAMPLING
        # get a list of all files in split-directory, sort list alphabetically because depending on OS you may won't get a sorted list
        splitlist = os.listdir(split_folder) 
        splitlist.sort()
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

            # array containing packet-numbers of the current split-file
            plist = np.arange(1,pcount+1,1)
            # same array, containing packet-indices
            plistindex = np.arange(0,pcount,1)


            if mode == 5: # every n-th packet, including first packet of the pcap
                modulo = samplepcount % n

                if modulo != 0:
                    # number of packets to skip in next iteration
                    nextpacketskip = n - modulo
                    nextsamplepstart = nextpacketskip
                else:
                    nextpacketskip = 0
                    nextsamplepstart = 0

                if verbose:
                    print(cfg.vcolor+'\n\n\t'+20*'~'+' {} '.format(file)+20*'~')
                    print('\n\t< {} skipped packets, this iteration'.format(packetskip))
                    print('\t< {} skipped packets, next iteration'.format(nextpacketskip)+Style.RESET_ALL)

                # array already considering packets to skip from last iteration
                pskip = plist[packetskip:]
                # index-numbers of packets to sample in current iteration
                psample = plistindex[packetskip::n]
                # packet-number of packets to sample in current iteration (readability in verbose)
                psamplenumber = plist[packetskip::n]
                # packets to drop in current iteration via editcap
                pdrop = np.delete(plist,psample.tolist())

                if verbose: # verbose output for improved sampling comprehension
                    print(cfg.vcolor+'\n\t'+10*'~'+' sampling '+10*'~')
                    pprint = packetOutput(plist,10,False) # generates list-styled packet output for better readability
                    print('\n\t< Original, {} packets\n\t< [{} ... {}]'.format(len(plist),str(pprint[0]),str(pprint[1])))
                    pprint = packetOutput(pskip,10,False)
                    print('\n\t< Iteration, {} packets\n\t< [{} ... {}]'.format(len(pskip),str(pprint[0]),str(pprint[1])))
                    pprint = packetOutput(psamplenumber,10,False)
                    print('\n\t< Sampled: {} packets\n\t< [{} ... {}]'.format(len(psamplenumber),str(pprint[0]),str(pprint[1])))
                    pprint = packetOutput(pdrop,10,False)
                    print('\n\t< Dropped: {} packets\n\t< [{} ... {}]'.format(len(pdrop),str(pprint[0]),str(pprint[1]))+Style.RESET_ALL)

                # flip the list to drop packets via editcap, starting from the end
                pdrop = np.flip(pdrop)
                # number of iterations until all packets are dropped
                iteration = int(len(pdrop)/512)+1

                for i in range(0,iteration):
                    # create a slice of 512 packets to remove with editcaps
                    pslice = pdrop[0:512]
                    # remove these 512 packets from droplist for next iteration
                    pdrop = pdrop[512:]

                    if superverbose: # detailed output for dropped packets via editcap
                        print(cfg.vcolor+'\n\t\t'+10*'~'+' packet removal {}/{} '.format(i+1,iteration)+10*'~')
                        pprint = packetOutput(pslice,10,False)
                        print('\n\t\t<< Dropping, {} packets\n\t\t<< [{} ... {}]'.format(len(pslice),str(pprint[0]),str(pprint[1]))+Style.RESET_ALL)

                        if i < (iteration-1): # only display remaining packets until last iteration
                            pprint = packetOutput(pdrop,10,False)
                            print(cfg.vcolor+'\n\t\t<< Remaining, {} packets\n\t\t<< [{} ... {}]'.format(len(pdrop),str(pprint[0]),str(pprint[1]))+Style.RESET_ALL)
                    # create string containing packet numbers to drop
                    arg = [str(int) for int in pslice]
                    # seperated with whitespaces necessary as editcap argument
                    arg = " ".join(arg)

                    tmpsplitfile = split_folder / file # split-file in current iteration to process with editcap
                    tmpfile = split_folder / 'tmp.pcap' # temporary file tmp.pcap created with editcap
                    editcapcmd = 'editcap {} {} {}'.format(tmpsplitfile,tmpfile,arg)
                    os.system(editcapcmd)

                    # replace split-file with sampled temporary file
                    movecmd = r'mv {} {} > NUL'.format(tmpfile,tmpsplitfile)
                    os.system(movecmd)


        # MERGE split-files
        print('>>> Merging split-files: {}'.format(mergecapcmd))
        os.system(mergecapcmd)


        # VERIFICATION
        if check: # compare sampled packet-count with calculated packet-count for basic verification
            print('>>> Verifying sampled packet-count')
            capinfoscmd = r'capinfos -M -c {} | grep packets'.format(pcap_sampled)
            samplepacketcount = subprocess.check_output(capinfoscmd, shell=True, universal_newlines=True)
            for word in samplepacketcount.split():
                if word.isdigit():
                    samplepacketcount = int(word)
                    if samplepacketcount == totalsamplecount: print(Fore.GREEN+'\t< {}\n\t< {} packets sampled\n\t< {} packets calculated\n\t< Verification SUCCEEDED'.format(capinfoscmd,samplepacketcount,totalsamplecount)+Style.RESET_ALL)
                    else: print(Fore.RED+'\t< {} packets sampled\n\t< {} packets calculated\n\t< Verification FAILED'.format(samplepacketcount,totalsamplecount)+Style.RESET_ALL)
    else: print('>>> No packet-based sampling, processing original capture')


    # FLOW-CREATION
    print('>>> Create flows with go-flows: {}'.format(csv_sampled_export))
    os.system(goflowscmd)

    # AGM feature-vector post-processing
    if cfg.vectors[j][0:3] == 'AGM':
        dataset = importCSV(csv_sampled_export,None,verbose)
        printdata(dataset,cfg.vectors[j],verbose=False)

        print('>>> Encoding TCP flags')
        tcpflagEncoder(dataset,'mode(_tcpFlags)',verbose=verbose)

        print('>>> Dropping features')
        dropfeatures = ['mode(destinationIPAddress)']
        for feature in dropfeatures:
            print('\t> {}'.format(feature))
            dataset.drop(columns=feature,inplace=True)

        print('>>> Saving {}'.format(csv_sampled_export))
        dataset.to_csv(csv_sampled_export, index=False)


    # LABELING
    print('>>> Labeling: {}'.format(labelingcmd))
    os.system(labelingcmd)

    if verbose:
        dataset = importCSV(csv_file,None,verbose)
        printdata(dataset,'packet-sampled',verbose)

    if time:
        end = timer()
        t = epochtime.time()
        print('\n(rpi-PacketSampling.py, runtime: %.3f' % (end-start),'seconds)\n')
        with open(cfg.time,'a') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=",")
            csvwriter.writerow([t,'rpi-PacketSampling.py',cfg.filenames[findex],'end'])

    exit()