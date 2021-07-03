#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 11 09:25:55 2020

@author: pjr
"""
from pandas import read_csv
from timeit import default_timer as timer
from pathlib import Path, PureWindowsPath, PurePath, PurePosixPath
from collections import Counter
from colorama import Fore, Style

import time as epochtime
import numpy as np
import pandas as pd
import csv
import subprocess
import os
import re
import sys
import math
import statistics

import config as cfg # necessary configurations from config.py

# create base-folders if necessary
if not os.path.exists(cfg.logs):        os.mkdir(cfg.logs)
if not os.path.exists(cfg.fpath):       os.mkdir(cfg.fpath)
if not os.path.exists(cfg.flowfolder):  os.mkdir(cfg.flowfolder)

# ARGUMENT PARSING
# command line argument passthrough for better usability
import argparse
parser = argparse.ArgumentParser(description='script for sampling PCAP files via go-flows (flow-based sampling), output is CSV')
# positional arguments
parser.add_argument('mode', metavar = 'mode', type=int,nargs=1,help='select sampling mode: {}'.format(cfg.fsamplingmode))
parser.add_argument('file', metavar = 'file', type=int,nargs=1,help='select file to process: {}'.format(cfg.filenames))
parser.add_argument('n', metavar='n', type=int,nargs=1,help='integer used to determine sampling steps')
parser.add_argument('j', metavar='j', type=int,nargs=1,help='choose feature-vector: {}'.format(cfg.vectors))
# optional arguments
parser.add_argument('-v','--verbose', action='store_true', help='output additional informations')
parser.add_argument('--superverbose', action='store_true', help='output additional informations, including loop iteration output')
parser.add_argument('--debug', action='store_true', help='output debugging informations, including flow-features containing NaNs')
parser.add_argument('-t','--time', action='store_true', help='measure runtimes')
args = parser.parse_args()


# FUNCTIONS
# set/reset options for maximum columns to display and floating point output precision
def poptions():
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.precision',3)
    return
def resetpoptions():
    pd.reset_option('display.max_columns', 15)
    pd.reset_option('display.max_rows', 15)
    pd.reset_option('display.precision', 6)
    return
# import CSV
def importCSV(csvpath,csvusecols=None,verbose=False,encoding='utf-8'):

    if verbose: print('\n\n'+40*'~'+' FUNCTION: importCSV '+40*'~')
    print('\n>>> Importing {}'.format(csvpath))
    csvdata = read_csv(csvpath,usecols=csvusecols,skipinitialspace=True,encoding=encoding)
    return csvdata
# outputs basic datset informations
def printdata(dataset,heading,verbose=False):

    if verbose: print('\n'+40*'~'+' FUNCTION: printdata, {} '.format(heading) +40*'~'+'\n')
    print('< Columns:\n{}\n'.format(dataset.columns))
    print('< Dataset:\n{}\n'.format(dataset))
    print('{}\n'.format(dataset.describe()))
    return
# returns list of accumulated per-packet features
def perpacketFeatures(dataset,keyword,verbose=False,time=False):

    features = dataset.columns
    tmp = []

    for feature in features:
        if feature[0:len(keyword)] == keyword:
            tmp.append(feature)
            print('\t+ {}'.format(feature))
        else: print('\t- {}'.format(feature))

    return tmp
# returns list of features based on keyword
def filterFeatures(dataset,keyword,verbose=False,time=False):
    features = dataset.columns
    tmp = []

    for feature in features:
        if keyword in feature:
            tmp.append(feature)
            print('\t+ {}'.format(feature))
        else: print('\t- {}'.format(feature))
    return tmp
# converts accumulated per-packet features into np.array
def convertToArray(dataset,features,mode,verbose=False):
    for feature in features: # iterate over given features
        print('\t> {}'.format(feature))

        if mode == 1: # creates numpy array based on numeric feature
            dataset[feature] = dataset[feature].apply(lambda x: 
                np.fromstring(x[1:len(x)-1],dtype=int, sep=" ") if type(x) == str
                else (np.array([float('nan')]) if pd.isna(x) 
                else x))

        if mode == 2: # creates list based on textual feature
            dataset[feature] = dataset[feature].apply(lambda x: x[1:len(x)-1].split())

    return
# converts TCP flags (textual feature) into list, considering empty flags (whitespaces) and flows only containing non-TCP packets
def convertToArrayTCP(dataset,features,mode,verbose=False,superverbose=False):
    print('\t> {}'.format(features))

    if verbose:print(cfg.vcolor+'\n\n'+40*'~'+' FUNCTION: convertToArrayTCP '+40*'~'+Style.RESET_ALL)

    if mode == 1: # creates numpy array based on numeric feature
        dataset[feature] = dataset[feature].apply(lambda x: 
            np.fromstring(x[1:len(x)-1],dtype=int, sep=" ") if type(x) == str 
            else (np.array([float('nan')]) if pd.isna(x) 
            else x))

    if mode == 2: # creates list based on textual feature
        for row in range(0,len(dataset.index)):

            cell      = dataset[features][row] # current cell
            tmp       = cell[1:-1] # cuts off brackets
            stringlen = len(tmp) # length of current cells string

            newcell     = [] # initialize empty list
            skipflag    = 0 # flag signaling one character to skip
            skipflag2   = 0 # flag signaling two characters to skip
            whiteflag   = 0 # flag signaling whitespace is detected

            if superverbose: # output every single flow
                print(cfg.vcolor+'\n\n'+80*'~')
                print('Original ({} packets):\n[{}]: {}'.format(dataset['packetTotalCount'][row],row,dataset[features][row]))

            if stringlen == 0: newcell.append('0') # set non-TCP flag if there are no flags at all
            else:
                for i in range(0,stringlen): # iterate every character in current cell

                    # skip character if flags are set
                    if skipflag ==1: # double-flag
                        skipflag = 0
                        continue
                    elif skipflag2 == 1: # tripple flag
                        skipflag2 = 0
                        continue

                    # alwasy non-TCP flag if first character is a whitespace
                    if i == 0 and tmp[i].isspace():
                        newcell.append('0')
                        whiteflag = 1
                        continue

                    # check for characters
                    if i<(stringlen-1) and (tmp[i].isalpha() and tmp[i+1].isspace()): # single flag
                        newcell.append(tmp[i])
                        whiteflag = 0
                        continue
                    elif i<(stringlen-1) and (tmp[i].isalpha() and tmp[i+1].isalpha()): # double flag condition
                        tmpflag = tmp[i]+tmp[i+1] # combine both flags
                        skipflag = 1
                        whiteflag = 0
                        if (i+2< stringlen-1) and tmp[i+2].isalpha(): # tripple flag condition
                            skipflag2 = 1
                            whiteflag = 0
                            tmpflag = tmpflag + tmp[i+2] # add 3rd flag to double-flag combination
                        newcell.append(tmpflag)
                        continue
                    # check for whitespaces
                    if i<(stringlen-1) and (tmp[i].isspace() and tmp[i+1].isspace()):
                        newcell.append('0')
                        continue
                    elif i<(stringlen-1) and (tmp[i].isspace() and whiteflag == 1 and tmp[i+1].isalpha()):
                        newcell.append('0')
                        continue

                    # check last character
                    if i == (stringlen-1) and tmp[i].isalpha():
                        newcell.append(tmp[i])
                        continue
                    elif i == (stringlen-1) and (tmp[i].isspace()):
                        newcell.append('0')
                        continue

                # correction necessary, nasty go-flows behaviour on flows containing only non-TCP flags
                if newcell.count('0') == len(newcell):
                    newcell = ['0'] * dataset['packetTotalCount'][row] # manually forge list with correct length

                    if superverbose: print('Corrected ({} packets):\n[{}]: {}'.format(len(newcell),row,newcell))

            #replacing cell
            dataset.at[row,features] = newcell

            if superverbose:
                print(cfg.vcolor+'Converted ({} packets):\n[{}]: {}'.format(len(newcell),row,dataset[features][row]))
                print('Comparison ({} packets, protocol identifier):\n[{}]: {}'.format(len(dataset['apply(accumulate(protocolIdentifier),forward)'][row]),row,dataset['apply(accumulate(protocolIdentifier),forward)'][row]))
                print(80*'~'+Style.RESET_ALL)
                input('...')
    return
# encode TCP flags considering non-TCP packets, splits up for multiple flags with same occurence in a flow to gather the actual most occuring flag
def tcpflagEncoderTCP(dataset,feature,verbose=False,superverbose=False):
    if verbose: print(cfg.vcolor+'\n'+40*'~'+' FUNCTION: tcpflagEncoder '+40*'~')
    print(cfg.vcolor+'\nPre-Encoding: \n{}'.format(dataset[feature]))

    # features to calculate
    distinctfeature = '{}: {}'.format(feature,'distinct')
    modeCountfeature = '{}: {}'.format(feature,'modeCount')

    # initialize new features with 0
    dataset.insert(len(dataset.columns),distinctfeature,0)
    dataset.insert(len(dataset.columns),modeCountfeature,0)

    # initialise flag features with 0 (as first column)
    flags = ['A','P','F','R','S','U','E','C','N']
    for flag in flags: dataset.insert(0,flag,0)

    # seaparate flag combinations into separate flags
    for row in range(0,len(dataset.index)): # iterate every single row

        newflags   = [] # initialize empty list to obtain all occuring (separated) flags
        modeflags  = [] # initialize empty list containing flag(s) for TCP flag mode (can be multiple)
        cell       = dataset[feature][row] # current celll
        modes      = Counter(cell).most_common() # get list with tuple for most common elements
        counterlen = len(modes) # list containing all occuring flags and their occurence in current cell

        if superverbose:
            print(cfg.vcolor+'\n\n'+80*'~')
            print('[{}]\nPre-Calculation:\n{}'.format(row,cell))

        # compare occurences if there is more than one flag with same occurence
        if counterlen == 1: # only a single flag occuring
            modeflags.append(modes[0][0]) # most common element name
            modecount     = int(modes[0][1]) # most common element occurence
            distinctcount = 1 # naturally only one distinct element
            if superverbose:
                print('\nMode:\n{}'.format(modeflags))
                print(cfg.vcolor+80*'~'+Style.RESET_ALL); input('...')

        elif counterlen == 0: # no flag occuring
            modeflags.append(0)
            modecount     = 0
            distinctcount = 0
            if superverbose:
                print('\nMode:\n{}}'.format(modeflags))
                print(cfg.vcolor+80*'~'+Style.RESET_ALL); input('...')

        elif counterlen > 1: # multi-flag occurences
            multiflag = 0 # initialize flag to signal if two flags with similar occurences are found

            if superverbose: print('\nMultiple:\t{}'.format(modes))

            tmprange = np.arange(0,counterlen-1) # array containing all index numbers from elements to compare
            for i in tmprange: # iterate over list elements
                modecount = int(modes[0][1]) # set modeCount
                distinctcount = len(np.unique(cell)) # set distinct number of flags

                if modes[i][1] == modes[i+1][1]: # similar occurence for at least two flags
                    if multiflag == 0:
                        modeflags.append(modes[i][0]) # append flag #1
                        modeflags.append(modes[i+1][0]) # append flag #2
                        multiflag = 1
                        continue
                    elif multiflag == 1:
                        modeflags.append(modes[i+1][0]) # append flag #3
                        continue
                else: # just one flag occuring most
                    if multiflag == 0:
                        modeflags.append(modes[i][0]) # append flag #1
                        if superverbose:
                            print('\nMode:\n{}'.format(modeflags))
                            print(cfg.vcolor+80*'~'+Style.RESET_ALL); input('...')
                        break
                    elif multiflag == 1: break

            tmpflags = []
            # convert flag-combinations to single flags
            if multiflag: # if multiple flags with similar occurences
                for item in modeflags: # iterate over flags
                    for char in item: # iterate actual flag-characters
                        tmpflags.append(char) # save separated flags in list

                if superverbose: print('Converted:\t{}'.format(tmpflags))

                # search most occuring flag for multiple similar occuring combinations
                if '0' in tmpflags: # if non-TCP flags is amongst most occuring flag, don't set any flag
                    modeflags = ['0']
                    if superverbose: print('{}'.format(modeflags))
                else:
                    Counting = Counter(tmpflags).most_common() # get most common flag within most occuring flag-combinations
                    if superverbose: print('Occurences:\t{}'.format(Counting))

                    modeflags = [] # initialize list
                    for i in range(0,len(Counting)): # iterate most common flags
                        if i < (len(Counting)-1):
                            if Counting[i][1] > Counting [i+1][1]: # current flag occuring more often?
                                modeflags.append(Counting[0][0])
                                break
                            elif Counting[i+1][1] == Counting [i+1][1]: # similar occurence?
                                modeflags.append(Counting[i][0])# add 1st flag
                                modeflags.append(Counting[i+1][0]) # add 2nd flag
                if superverbose:
                    print('\nMode:\n{}'.format(modeflags))
                    print(cfg.vcolor+80*'~'+Style.RESET_ALL); input('...')

        if verbose: print('\nPre-Encoding:\nTCP flags: {}, {}\n\tmodeCount: {},{}\n\tdistinct: {},{}'.format(modeflags,type(modeflags),modecount,type(modecount),distinctcount,type(distinctcount)))

        dataset.at[row,modeCountfeature] = modecount # number of occurences for mode(s)
        dataset.at[row,distinctfeature]  = distinctcount # number of distinct elements

        if isinstance(modeflags,list) and len(modeflags)>0:
            for item in modeflags:
                #print('\nPost-Encoding:\ncurrent: {}'.format(item))

                if '0' in modeflags: break # don't set any flag if nonTCP flag is within the most occuring flags
                else:
                    for char in item: # iterate occuring flags
                        dataset.at[row,char] = 1 # set flag-features to 1
                        #print('flag {}: {}'.format(item,dataset[item][row]))
            #dataset.at[row,modefeature]      = modeflags

        if verbose:
            print(cfg.vcolor+'\nPost-Encoding:\n{}: {}, {}, {}'.format(row,dataset[feature][row],dataset[modeCountfeature][row],dataset[distinctfeature][row])+Style.RESET_ALL)

    print(cfg.vcolor+'\nPost-Encoding:\n{}\n'.format(dataset[flags])+Style.RESET_ALL)
    return

# per-flow sampling using lambda functions
def lambdaflowSampling(dataset,n,features,mode=0,verbose=False,time=False):

    superverbose = False # manual switch to output loop iterations

    if verbose and not superverbose:
        print(40*' '+' SAMPLING: {} (n={})'.format(cfg.fsamplingmode[mode],n))
        print(40*'~'+' FUNCTION: flowSampling '+40*'~'+'\n')

    for feature in features: # iterate over given list of features
        print('\t> {}'.format(feature))

        if mode == 1: # sample every n-th packet
            dataset[feature] = dataset[feature].apply(lambda x: x[::n])

        elif mode == 2: # sample n, skip n packets
            tmp = []

            for i in range(0,len(dataset.index)):
                psample = []
                tmp = dataset[feature][i].copy() # copy current cells content for sampling
                iterations = int(len(tmp)/(2*n))+1

                for j in range (0,iterations):
                    psample.extend(tmp[0:n]) # extend list with first n packets of cells content
                    tmp = tmp[2*n:] # remove sampled packets & packets to skip

                    if superverbose:
                        print(cfg.vcolor+'\n\n'+10*'~'+' sampling, iteration: {}/{} '.format((j+1),iterations)+10*'~')
                        print('Sampled:')
                        print(len(psample))
                        print(psample+Style.RESET_ALL)

                dataset.at[i,feature] = psample # replace current cells content with sampled values

        elif mode == 3: # sample first n packets
            dataset[feature] = dataset[feature].apply(lambda x: x[:n])

        elif mode == 4: # sample n, skip n-1, sample n-2 ...
            tmp = []

            for i in range(0,len(dataset.index)):
                psample = []
                tmp = dataset[feature][i].copy()

                # counters for sampling
                m = n
                k = n

                if superverbose: print(cfg.vcolor+'[{}/{}]:\n{}\n{}'.format(i,len(dataset.index),tmp,type(tmp))+Style.RESET_ALL)

                #while (tmp.size > 0 and m > 0): # iterate as long as list is not empty and there are still values to sample
                while (len(tmp) > 0 and m > 0): # iterate as long as list is not empty and there are still values to sample
                    psample.extend(tmp[0:m]) # sample m values
                    k = m-1 # number of packets to skip
                    tmp = tmp[m+k:] # remove sampled plus skipped packets
                    m = k-1 # set value to sample for next iteration

                    if superverbose:
                        print(cfg.vcolor+'\n\n'+10*'~'+' sampling '+10*'~')
                        # only output non-empty list
                        if tmp.size > 0:
                            print('\nSliced:')
                            print(len(tmp))
                            print(tmp)
                        print('\nSampled:')
                        print(len(psample))
                        print(psample+Style.RESET_ALL)

                dataset.at[i,feature] = psample # replace current cells content with sampled values
    return
# returns formatted list for increased visibility in verbose output
def packetOutput(plist,n,verbose):
    tmp = []

    # creates list containing two elements (first and last n packets of given list) 
    tmp = [plist[0:n],plist[-n:]]

    for i in range(0,2):
        tmp[i] = [str(int) for int in tmp[i]]
        tmp[i] = " ".join(tmp[i])

    if verbose:
        print('\n\n'+40*'~'+' FUNCTION: packetOutput '+40*'~')
        print('\npacket-list, length:\n{}'.format(len(plist)))
        print('\npacket-list, content:\n{}'.format(plist))
        print('\npacket-list, formatted:\n{}'.format(tmp))
        if not time: input('\n...')

    return tmp
# search NaN values for debugging
def searchNaN(dataset,features,verbose=False,time=False):

    if time: start = timer()

    # informational output
    if verbose:
        print(cfg.vcolor+'\n'+40*'~'+' FUNCTION: searchNaN '+40*'~')

    print(cfg.vcolor+'>>> Searching NaNs')

    length = dataset.shape[0]
    count = 0
    for feature in features:
        currentcount = 0
        print('\t>> {} '.format(feature))
        if isinstance(dataset[feature][0],np.ndarray): # only check numpy arrays
            for i in range(0,length):
                if np.isnan(dataset[feature][i]).any(): # check if any element in array is NaN
                    count += 1
                    currentcount += 1
                    print(cfg.vcolor+'\t\t > found NaN in row {}: {}'.format(i,dataset[feature][i]))
            if currentcount == 0: print('\t\t > no NaNs found')
        else: continue
    print('<<< Total NaNs: {}\n\n'.format(count)+Style.RESET_ALL)

    if time:
        end = timer()
        print('\ncleanNaN\n[TIME]: %.3f' % (end-start),'seconds')

    return


if __name__ == '__main__':

    global verbose
    global time
    global check

    # set boolean variables based on argument passing
    verbose         = args.verbose
    superverbose    = args.superverbose
    time            = args.time
    debug           = args.debug
    if superverbose: verbose = True

    mode    = args.mode[0] # sampling-mode
    findex  = args.file[0] # file-index
    n       = args.n[0] # sampling steps
    j       = args.j[0] # feature-vector

    if time: 
        start = timer()
        t = epochtime.time()
        with open(cfg.time,'a') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=",")
            csvwriter.writerow([t,'rpi-FlowSampling.py',cfg.filenames[findex],'start'])

    # set mode for labeling.py
    if j<cfg.flowlimit: labelmode = 'AGM'
    elif j >= cfg.flowlimit: labelmode = '5tuple'


    # FILES, PATHS & COMMANDS based on given arguments
    wd = Path.cwd() # working directory

    # filenames
    pcap                = '{}.pcap'.format(cfg.filenames[findex]) # PCAP file to process
    csv_labeled         = '{}.csv'.format(cfg.filenames[findex]) # labeled, sampled CSV
    csv_sampled         = '{}_unlabeled.csv'.format(cfg.filenames[findex]) # sampled CSV

    # full paths to files
    pcap                = cfg.fpath / pcap
    csv_import          = cfg.fpath / csv_sampled
    csv_sampled_export  = cfg.flowfolder / csv_sampled
    csv_labeled_export  = cfg.flowfolder / csv_labeled

    # commands
    goflowsconf = wd / cfg.vectorfolder / cfg.vectors[j]
    goflowscmd  = '{} run features {} export csv {} source libpcap {}'.format(cfg.goflowspath,goflowsconf,csv_import,pcap)
    labelingcmd = 'python3 {} {} {}'.format(cfg.labelingpath,cfg.flowfolder/cfg.filenames[findex],labelmode)

    # INFORMATIONAL OUTPUT
    # check passed optional arguments, filepaths and forged commands
    print('\n\n'+40*' '+' FILE: {}'.format(cfg.filenames[findex]))
    print(40*'~'+' SCRIPT: rpi-FlowSampling.py '+40*'~')
    print('\n'+20*'~'+' optional arguments '+20*'~')
    print("\n{}\t--verbose\n{}\t--superverbose\n{}\t--time".format(verbose,superverbose,time))
    print('\n{}, n = {}'.format(cfg.fsamplingmode[mode],n))
    print('\n'+20*'~'+' paths & files'+20*'~')
    print('\nJSON:\t{}'.format(goflowsconf))
    print('PCAP:\t{}'.format(pcap))
    print('CSVs:\t{}\n\t{}\n\t{}'.format(csv_import,csv_sampled_export,csv_labeled_export))
    print('\nlogs:\t{}'.format(cfg.logs))
    print('times:\t{}'.format(cfg.time))
    print('\n'+20*'~'+' commands '+20*'~')
    print("\ngo-flows: {}".format(goflowscmd))
    print("labeling: {}".format(labelingcmd))


    # FLOW-COLLECTION
    print('\n\n>>> Collect flows with go-flows from {}'.format(pcap))
    os.system(goflowscmd) # execute go-flows to process passed PCAP file
    dataset = importCSV(csv_import,None,verbose)
    if verbose: printdata(dataset,'go-flows CSV',verbose)


    # PER-FLOW SAMPLING
    # CAIA
    if cfg.vectors[j][0:4] == 'CAIA': # select CAIA based on given JSON configuration
        print('<<< {}'.format(cfg.vectors[j]))

        keyword = 'apply(accumulate'
        print('>>> Identifying accumulated features')
        features = filterFeatures(dataset,keyword,verbose,time)

        keyword = 'TotalCount'
        print('>>> Identifying features containing: {}'.format(keyword))
        totalFeatures = filterFeatures(dataset,keyword,verbose,time)

        keyword = 'ipTotal'
        print('>>> Identifying features containing: {}'.format(keyword))
        ipTotal = filterFeatures(dataset,keyword,verbose,time)

        keyword = 'interPacket'
        print('>>> Identifying features containing: {}'.format(keyword))
        interPacket = filterFeatures(dataset,keyword,verbose,time)
        if verbose: print(cfg.vcolor+'\n< Original:\n{}\n'.format(dataset[features].head(n=20))+Style.RESET_ALL)

        print('>>> Converting accumulated values')
        convertToArray(dataset,features,1,verbose)
        if verbose: print(cfg.vcolor+'\n< Converted:\n{}'.format(dataset[features].head(n=20))), input('...\n'+Style.RESET_ALL)

        if n != 0:
            print('>>> Applying flow-based sampling')
            lambdaflowSampling(dataset,n,features,mode,verbose,time)
            if verbose: print(cfg.vcolor+'\n< Sampled:\n{}'.format(dataset[features].head(n=20))), input('...\n'+Style.RESET_ALL)
        else: # skip sampling
            print('>>> No flow-based sampling, processing original capture')


        # CALCULATIONS
        print('>>> Create features & calculate values')
        # totalPacketCounts as CAIA features
        print('\t>> Calculate packetTotalCount features')
        key = ['forward','backward']
        for word in key:
            newfeature = '{},{}'.format('packetTotalCount',word)
            print('\t\t> {}'.format(newfeature))
            dataset.insert(6,newfeature,0)
            # manually set feature to gather packet counts from
            if word   == 'forward':    tmp = 'apply(accumulate(octetTotalCount),forward)'
            elif word == 'backward':   tmp = 'apply(accumulate(octetTotalCount),backward)'
            dataset[newfeature] = dataset[tmp].apply(lambda x: 0 if np.isnan(x).all() else len(x))

        # calculate min, mean, max & stdev for CAIA features
        print('\t>> Calculate min, mean, max and stdev features')
        key     = ['min','mean','max','stdev'] # parameters to calculate
        for feature in (ipTotal+interPacket):
            for word in key:
                newfeature = '{}: {}'.format(feature,word)
                print('\t\t> {}'.format(newfeature))
                dataset.insert(len(dataset.columns),newfeature,float(0)) # initialise new features after last column

                # apply calculations on new features
                if   word == 'min':   dataset[newfeature] = dataset[feature].apply(lambda x: None if np.isnan(x).any() else int(np.amin(x)))
                elif word == 'mean':  dataset[newfeature] = dataset[feature].apply(lambda x: None if np.isnan(x).any() else sum(x)/len(x))
                elif word == 'max':   dataset[newfeature] = dataset[feature].apply(lambda x: None if np.isnan(x).any() else int(np.amax(x)))
                elif word == 'stdev': # calculating variance according to Welford
                    for i in range (0,len(dataset.index)):
                        stdev = None
                        cell = dataset[feature][i] # current cell

                        if np.isnan(cell).any(): dataset.at[i,newfeature] = stdev
                        elif len(cell) == 1:     dataset.at[i,newfeature] = 0
                        else:
                            # initialize variables
                            N  = 0
                            m  = 0
                            m2 = 0

                            for val in cell:
                                N       +=1
                                delta   = val - m
                                m       = m + delta/N
                                delta2  = val - m
                                m2      = m2 +delta*delta2
                            stdev = math.sqrt(m2/(N-1))

                            dataset.at[i,newfeature] = stdev

                        if superverbose:
                            print(cfg.vcolor+'\n'+80*'~')
                            print('[{}]:\nCell: {}, {}\nStdev: {}'.format(i,cell,type(cell),stdev))
                            print(80*'~'+Style.RESET_ALL); input('')
                #elif word == 'stdev': dataset[newfeature] = dataset[feature].apply(lambda x: None if np.isnan(x).any() else np.std(x))

        # calculate totalCounts
        print('\t>> Calculate total features')
        for feature in totalFeatures:
            print('\t\t> {}'.format(feature))
            dataset[feature] = dataset[feature].apply(lambda x: 0 if np.isnan(x).any() else sum(x))


        # DROP, RENAME & SORT
        # drop features not necessary anymore
        print('>>> Dropping features')
        for feature in (ipTotal+interPacket):
            print('\t> {}'.format(feature))
            dataset.drop(columns=feature,inplace=True)

        #features = dataset.columns
        #print('Features before Renaming:\n{}'.format(features))
        #input('...')

        print('>>> Rename features')
        renamedict = {
            "packetTotalCount,forward":                                     'count(packetTotalCount,forward)',
            "apply(accumulate(octetTotalCount),forward)":                   'count(octetTotalCount,forward)',
            "apply(accumulate(tcpSynTotalCount),forward)":                  'count(tcpSynTotalCount,forward)',
            "apply(accumulate(tcpAckTotalCount),forward)":                  'count(tcpAckTotalCount,forward)',
            "apply(accumulate(tcpFinTotalCount),forward)":                  'count(tcpFinTotalCount,forward)',
            "apply(accumulate(_tcpCwrTotalCount),forward)":                 'count(_tcpCwrTotalCount,forward)',

            'apply(accumulate(ipTotalLength),forward): min':                'min(ipTotalLength,forward)',
            'apply(accumulate(ipTotalLength),forward): mean':               'mean(ipTotalLength,forward)',
            'apply(accumulate(ipTotalLength),forward): max':                'max(ipTotalLength,forward)',
            'apply(accumulate(ipTotalLength),forward): stdev':              'stdev(ipTotalLength,forward)',

            'apply(accumulate(_interPacketTimeSeconds),forward): min':      'min(_interPacketTimeSeconds,forward)',
            'apply(accumulate(_interPacketTimeSeconds),forward): mean':     'mean(_interPacketTimeSeconds,forward)',
            'apply(accumulate(_interPacketTimeSeconds),forward): max':      'max(_interPacketTimeSeconds,forward)',
            'apply(accumulate(_interPacketTimeSeconds),forward): stdev':    'stdev(_interPacketTimeSeconds,forward)',

            "packetTotalCount,backward":                                    'count(packetTotalCount,backward)',
            "apply(accumulate(octetTotalCount),backward)":                  'count(octetTotalCount,backward)',
            "apply(accumulate(tcpSynTotalCount),backward)":                 'count(tcpSynTotalCount,backward)',
            "apply(accumulate(tcpAckTotalCount),backward)":                 'count(tcpAckTotalCount,backward)',
            "apply(accumulate(tcpFinTotalCount),backward)":                 'count(tcpFinTotalCount,backward)',
            "apply(accumulate(_tcpCwrTotalCount),backward)":                'count(_tcpCwrTotalCount,backward)',

            'apply(accumulate(ipTotalLength),backward): min':               'min(ipTotalLength,backward)',
            'apply(accumulate(ipTotalLength),backward): mean':              'mean(ipTotalLength,backward)',
            'apply(accumulate(ipTotalLength),backward): max':               'max(ipTotalLength,backward)',
            'apply(accumulate(ipTotalLength),backward): stdev':             'stdev(ipTotalLength,backward)',

            'apply(accumulate(_interPacketTimeSeconds),backward): min':     'min(_interPacketTimeSeconds,backward)',
            'apply(accumulate(_interPacketTimeSeconds),backward): mean':    'mean(_interPacketTimeSeconds,backward)',
            'apply(accumulate(_interPacketTimeSeconds),backward): max':     'max(_interPacketTimeSeconds,backward)',
            'apply(accumulate(_interPacketTimeSeconds),backward): stdev':   'stdev(_interPacketTimeSeconds,backward)'
        }
        dataset = dataset.rename(columns=renamedict) # re-name features

        print('>>> Sorting features')
        preordered = [
            'flowStartMilliseconds',
            'sourceIPAddress',
            'destinationIPAddress',
            'sourceTransportPort',
            'destinationTransportPort',
            'protocolIdentifier',

            'count(packetTotalCount,forward)',
            'count(octetTotalCount,forward)',
            'count(tcpSynTotalCount,forward)',
            'count(tcpAckTotalCount,forward)',
            'count(tcpFinTotalCount,forward)',
            'count(_tcpCwrTotalCount,forward)',

            'min(ipTotalLength,forward)',
            'mean(ipTotalLength,forward)',
            'max(ipTotalLength,forward)',
            'stdev(ipTotalLength,forward)',

            'min(_interPacketTimeSeconds,forward)',
            'mean(_interPacketTimeSeconds,forward)',
            'max(_interPacketTimeSeconds,forward)',
            'stdev(_interPacketTimeSeconds,forward)',

            'count(packetTotalCount,backward)',
            'count(octetTotalCount,backward)',
            'count(tcpSynTotalCount,backward)',
            'count(tcpAckTotalCount,backward)',
            'count(tcpFinTotalCount,backward)',
            'count(_tcpCwrTotalCount,backward)',

            'min(ipTotalLength,backward)',
            'mean(ipTotalLength,backward)',
            'max(ipTotalLength,backward)',
            'stdev(ipTotalLength,backward)',

            'min(_interPacketTimeSeconds,backward)',
            'mean(_interPacketTimeSeconds,backward)',
            'max(_interPacketTimeSeconds,backward)',
            'stdev(_interPacketTimeSeconds,backward)'
        ]
        dataset = dataset[preordered]
    # AGM
    elif cfg.vectors[j][0:3] == 'AGM': # select AGM based on given JSON configuration
        print('<<< {}'.format(cfg.vectors[j]))

        print('>>> Identifying accumulated features')
        keyword = 'apply(accumulate'; features = filterFeatures(dataset,keyword,verbose,time)

        print('>>> Identifying textual feature') # basically manual selection via keywords
        keyword = '_tcp'; textual = filterFeatures(dataset,keyword,verbose,time)
        keyword = 'destinationIP'; textual += filterFeatures(dataset,keyword,verbose,time)

        for element in textual:
            try: features.remove(element) # remove texutal features from numeric
            except ValueError: pass # ignore eventual missing elements

        print('>>> Converting accumulated features') # converts numerical features into numpy array
        convertToArray(dataset,features,1,verbose)
        if verbose: print(cfg.vcolor+'\n< Converted:\n{}'.format(dataset[features].head(n=20))); input('...\n'+Style.RESET_ALL)

        dataset.insert(len(dataset.columns),'packetTotalCount',0) # initialise new feature after last column
        dataset['packetTotalCount'] = dataset['apply(accumulate(protocolIdentifier),forward)'].apply(lambda x: len(x)) # obtain packetTotalCount via IP protocol numbers feature before sampling

        print('>>> Converting destinationIPAddress feature') # converts textual feature to list
        convertToArray(dataset,['apply(accumulate(destinationIPAddress),forward)'],2,verbose)

        print('>>> Converting _tcpFlags feature') # converts textual feature (including whitespaces as non-TCP flag) to list
        convertToArrayTCP(dataset,'apply(accumulate(_tcpFlags),forward)',2,verbose,superverbose)

        if verbose: print(cfg.vcolor+'\n< Converted:\n{}'.format(dataset[textual].head(n=20))); input('...\n'+Style.RESET_ALL)

        if n != 0:
            print('>>> Applying flow-based sampling')
            lambdaflowSampling(dataset,n,features+textual,mode,verbose,time)
            if verbose: print(cfg.vcolor+'\n< Sampled:\n{}'.format(dataset[features+textual].head(n=20))); input('...\n'+Style.RESET_ALL)
        else: print('>>> No flow-based sampling, processing original capture')

        if debug:
            searchNaN(dataset,features,verbose=True,time=False)
            print(cfg.vcolor+'Dtypes:\n{}'.format(dataset.dtypes)); input('...\n'+Style.RESET_ALL)

        # CALCULATIONS
        # encode tcpFlags & convert to numpy array
        print('>>> Encoding TCP flags as one feature per flag')
        tcpflagEncoderTCP(dataset,'apply(accumulate(_tcpFlags),forward)',verbose,superverbose)
        textual.remove('apply(accumulate(_tcpFlags),forward)')

        print('>>> Drop textual TCP flag feature')
        dropTCP = ['apply(accumulate(_tcpFlags),forward)']
        for feature in dropTCP:
            print('\t> {}'.format(feature))
            dataset.drop(columns=feature,inplace=True)

        # distinct: number of unique values, mode: most occuring value, modeCount: count for most occuring value
        print('>>> Create features & calculate values')
        print('\t> {}'.format('packetTotalCount')) # gather total packet count after sampling
        dataset['packetTotalCount'] = dataset['apply(accumulate(protocolIdentifier),forward)'].apply(lambda x: len(x)) # obtain packetTotalCount via IP protocol numbers feature

        key = ['distinct','mode','modeCount'] # AGM feature functions
        for feature in (features): # numpy array features
            for word in key:
                newfeature = '{}: {}'.format(feature,word)
                print('\t> {}'.format(newfeature))
                dataset.insert(len(dataset.columns),newfeature,0) # initialise new feature after last column

                if   word == 'distinct':  dataset[newfeature] = dataset[feature].apply(lambda x: 0 if (len(x)==1 and np.isnan(x)) else len(np.unique(x)) if len(x)>0 else x)
                elif word == 'mode':      dataset[newfeature] = dataset[feature].apply(lambda x: np.nan if (any(np.isnan(x)) and len(x)==1) else (np.bincount(x).argmax() if len(x)>0 else x))
                elif word == 'modeCount':
                    dataset[newfeature] = dataset[feature].apply(lambda x: np.nan if (any(np.isnan(x)) and len(x)==1) else (np.count_nonzero(x==int(np.bincount(x).argmax()) if len(x)>0 else int(0))))
                    dataset[newfeature] = dataset[newfeature].apply(lambda x: x[0] if isinstance(x,list) else x) # get rid of single-element lists (for better comparison flow-based/packet-based unsampled data)

        for feature in (textual): # textual features (destinationIPAddress)
            for word in key:
                newfeature = '{}: {}'.format(feature,word)
                print('\t> {}'.format(newfeature))
                dataset.insert(len(dataset.columns),newfeature,0) # initialise new feature after last column

                if   word == 'distinct':  dataset[newfeature] = dataset[feature].apply(lambda x: len(np.unique(x)))
                elif word == 'mode':      dataset[newfeature] = dataset[feature].apply(lambda x: [item[0] for item in Counter(x).most_common(1)])
                elif word == 'modeCount': dataset[newfeature] = dataset[feature].apply(lambda x: [item[1] for item in Counter(x).most_common(1)][0])


        # CHECK CALCULATIONS
        if verbose: #compare calculations to original array values
            print(cfg.vcolor+'>>> Check applied calculations\n')
            for feature in (features+textual):
                tmp = pd.DataFrame() # initialise empty dataframe
                modes = ['modeCount','mode','distinct']
                for mode in modes:
                    tmp.insert(0,mode,dataset[feature+': {}'.format(mode)]) # forge dataframe to increased readability of output
                tmp.insert(0,feature,dataset[feature]) # add original feature column
                print(cfg.vcolor+'{}'.format(tmp)); input('...'+Style.RESET_ALL)


        # CHECK FOR NaN values again
        if debug: searchNaN(dataset,features,verbose=True,time=False)


        # DROP original features (non-textual)
        print('>>> Drop features')
        dropfeatures = features+textual+['apply(accumulate(destinationIPAddress),forward): mode']
        for feature in dropfeatures:
            print('\t> {}'.format(feature))
            dataset.drop(columns=feature,inplace=True)


        # RENAME features
        # https://stackoverflow.com/questions/2484156/is-str-replace-replace-ad-nauseam-a-standard-idiom-in-python
        print('>>> Rename features')
        rename = dataset.columns
        for feature in (rename):
            tmp = feature.replace('apply(accumulate','(')
            print('\t> {} >> {}'.format(feature,tmp))
            dataset.rename(columns={feature:tmp},inplace=True)

        print('>>> Sorting features')
        preordered = [
            'flowStartMilliseconds',
            'N',
            'C',
            'E',
            'U',
            'S',
            'R',
            'F',
            'P',
            'A',
            'sourceIPAddress',
            "((_tcpFlags),forward): distinct",
            "((_tcpFlags),forward): modeCount",
            "((sourceTransportPort),forward): distinct",
            "((sourceTransportPort),forward): mode",
            "((sourceTransportPort),forward): modeCount",
            "((destinationTransportPort),forward): distinct",
            "((destinationTransportPort),forward): mode",
            "((destinationTransportPort),forward): modeCount",
            "((protocolIdentifier),forward): distinct",
            "((protocolIdentifier),forward): mode",
            "((protocolIdentifier),forward): modeCount",
            "((ipTTL),forward): distinct",
            "((ipTTL),forward): mode",
            "((ipTTL),forward): modeCount",
            "((octetTotalCount),forward): distinct",
            "((octetTotalCount),forward): mode",
            "((octetTotalCount),forward): modeCount",
            "((destinationIPAddress),forward): distinct",
            "((destinationIPAddress),forward): modeCount",
            'packetTotalCount'
        ]
        dataset = dataset[preordered] # re-order dataset

        print('>>> Renaming features')
        renamedict = {
            "((_tcpFlags),forward): distinct":                  'distinct(_tcpFlags)',
            "((_tcpFlags),forward): modeCount":                 'modeCount(_tcpFlags)',
            "((sourceTransportPort),forward): distinct":        'distinct(sourceTransportPort)',
            "((sourceTransportPort),forward): mode":            'mode(sourceTransportPort)',
            "((sourceTransportPort),forward): modeCount":       'modeCount(sourceTransportPort)',
            "((destinationTransportPort),forward): distinct":   'distinct(destinationTransportPort)',
            "((destinationTransportPort),forward): mode":       'mode(destinationTransportPort)',
            "((destinationTransportPort),forward): modeCount":  'modeCount(destinationTransportPort)',
            "((protocolIdentifier),forward): distinct":         'distinct(protocolIdentifier)',
            "((protocolIdentifier),forward): mode":             'mode(protocolIdentifier)',
            "((protocolIdentifier),forward): modeCount":        'modeCount(protocolIdentifier)',
            "((ipTTL),forward): distinct":                      'distinct(ipTTL)',
            "((ipTTL),forward): mode":                          'mode(ipTTL)',
            "((ipTTL),forward): modeCount":                     'modeCount(ipTTL)',
            "((octetTotalCount),forward): distinct":            'distinct(octetTotalCount)',
            "((octetTotalCount),forward): mode":                'mode(octetTotalCount)',
            "((octetTotalCount),forward): modeCount":           'modeCount(octetTotalCount)',
            "((destinationIPAddress),forward): distinct":       'distinct(destinationIPAddress)',
            "((destinationIPAddress),forward): modeCount":      'modeCount(destinationIPAddress)'
        }
        dataset = dataset.rename(columns=renamedict) # re-name features

    if verbose:
        features = dataset.columns
        print(cfg.vcolor+'\n< Calculated:\n{}\n'.format(dataset[features].head(n=20))+Style.RESET_ALL), input('...\n')
        printdata(dataset,'per-flow sampled',verbose)

    # save dataframe as CSV for further preprocessing & classification
    print('>>> Saving {}'.format(csv_sampled_export))
    dataset.to_csv(csv_sampled_export, index=False)


    # LABELING
    if verbose: print(cfg.vcolor+'>>> Labeling: {}'.format(labelingcmd)+Style.RESET_ALL)
    os.system(labelingcmd) # label benign & attack traffic as last step of preparation

    if time:
        end = timer()
        t = epochtime.time()
        print('\n(rpi-Flowsampling.py, runtime: %.3f' % (end-start),'seconds)\n')
        with open(cfg.time,'a') as csvfile: # write timestamp to csv
            csvwriter = csv.writer(csvfile, delimiter=",")
            csvwriter.writerow([t,'rpi-FlowSampling.py',cfg.filenames[findex],'end'])

    exit()