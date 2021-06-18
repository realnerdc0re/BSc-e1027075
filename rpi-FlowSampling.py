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
def convertToArray(dataset,features,mode,verbose=False,time=False):
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
# per-flow sampling using iterations
def flowSampling(dataset,n,features,mode=0,verbose=False,time=False):
    tmp = []

    if verbose and not superverbose:
        print(40*' '+' SAMPLING: {} (n={})'.format(cfg.fsamplingmode[mode],n))
        print(40*'~'+' FUNCTION: flowSampling '+40*'~')

    # iterate over list of given features
    for feature in features:

        print('\t> {}'.format(feature))

        # iterate over every single row of the feature
        for i in range(0,len(dataset.index)):
            # list to collect packets to sample, has to be reset for every row iteration
            psample = []
            
            if superverbose:
                print('\n\n'+40*' '+' SAMPLING: {} '.format(cfg.fsamplingmode[mode])+' (n={}).format(n)')
                print(40*'~'+' FUNCTION: flowSampling: {}, row: {}/{} '.format(feature,(i+1),len(dataset.index))+40*'~')
                print('\nOriginal:')
                print(len(dataset[feature][i]))
                print(dataset[feature][i])

            # mode 0: sample every n-th packet of the flow (including first packet)
            if mode == 1:
                dataset.at[i,feature] = dataset[feature][i][0::n]
                
                if superverbose:
                        print('\nSampled:')
                        print(len(dataset[feature][i]))
                        print(dataset[feature][i])
                        input('\n...')
            
            # mode 1: sample n packets, skip n packets...
            elif mode == 2:
                # copy current cells content for sampling
                tmp = dataset[feature][i].copy()
                
                iteration = int(len(tmp)/(2*n))+1
    
                for j in range (0,iteration):
                    # extend sampling list with first n packets in cell
                    psample.extend(tmp[0:n])
                    # remove sampled packets plus packets to skip
                    tmp = tmp[2*n:]
                    
                    if superverbose:
                        print('\n\n'+10*'~'+' sampling, iteration: {}/{} '.format((j+1),iteration)+10*'~')
                        print('Sampled:')
                        print(len(psample))
                        print(psample)
                
                # write sampled packet-list in current cell
                dataset.at[i,feature] = psample
                
                # pauses after every single row iteration
                #if superverbose: input('\n{SUPERVERBOSE} press ENTER to continue.')
            
            # mode 2: sample first n packets of the flow
            elif mode == 3:
                dataset.at[i,feature] = dataset[feature][i][0:n]
                
                if superverbose:
                        print('\nSampled:')
                        print(len(dataset[feature][i]))
                        print(dataset[feature][i])
        
            # mode 3: sample n, skip n-1, sample n-2, skip n-3... packets of the flow
            elif mode == 4:
                # copy current cells content for sampling
                tmp = dataset[feature][i].copy()
                
                # counters for sampling
                m = n
                k = n
                # iterate as long as list is not empty and there are still values to sample
                while (tmp and m > 0):
                    # sample first m values
                    psample.extend(tmp[0:m])
                    # remove first m plus m-1 values from cell
                    k = m-1
                    tmp = tmp[m+k:]
                    # sample k-1 values in the following iteration
                    m = k-1
                    
                    if superverbose:
                        print('\n\n'+10*'~'+' sampling '+10*'~')
                        # only output non-empty list
                        if tmp:
                            print('\nSliced:')
                            print(len(tmp))
                            print(tmp)
                        print('\nSampled:')
                        print(len(psample))
                        print(psample)
                        
                        # pauses after every single row iteration
                        #input('\n{SUPERVERBOSE} press ENTER to continue.')

            else:
                print('\n[ERROR] invalid sampling-mode selected!')
                exit()

            #if superverbose and not mode == 1 and not mode == 3: 
            #       input('\n{VERBOSE} press ENTER to continue.')
        if superverbose:
            input('\n...')

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

                while (tmp.size > 0 and m > 0): # iterate as long as list is not empty and there are still values to sample
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
# encode post-calculations, takes single element list to apply encoding
def tcpflagEncoderOLD(dataset,feature,verbose=False):
    if verbose: print(cfg.vcolor+'\n'+40*'~'+' FUNCTION: tcpflagEncoder '+40*'~')

    # https://www.keycdn.com/support/tcp-flags
    tcpflags = {
        'A':100000000, # ACK
        'P': 10000000, # PSH
        'F':  1000000, # FIN
        'R':   100000, # RST
        'S':    10000, # SYN
        'U':     1000, # URG
        'E':      100, # ECE
        'C':       10, # CWR
        'N':        1  # NS
    }

    if verbose: print('\npre-encoding: \n{}'.format(dataset[feature])+Style.RESET_ALL)

    for i in range(0,len(dataset.index)):
        cell = dataset[feature][i] # current cell

        if isinstance(cell,list) and len(cell)>0:
            value = 0
            for char in cell[0]:
                value += cfg.tcpflags[char]

            dataset.at[i,feature] = int(str(value),2) # convert (pseudo) binary to decimal
            #dataset.at[i,feature] = value # simply use number as decimal
        elif (len(cell)==0): dataset.at[i,feature] = ''

    if verbose: print(cfg.vcolor+'\npost-encoding:\n{}'.format(dataset[feature])+Style.RESET_ALL)

    return
# encode before calculations are applied, takes multi element list to apply encoding
def tcpflagPreEncoder(dataset,feature,verbose=False):

    if verbose:
        print(cfg.vcolor+'\n'+40*'~'+' FUNCTION: tcpflagPreEncoder '+40*'~')
        print('\ntcpFlags: {}\n\npre-encoding: \n{}'.format(cfg.tcpflags,dataset[feature])+Style.RESET_ALL)

    for i in range(0,dataset.shape[0]):
        cell = dataset[feature][i] # current cell

        if isinstance(cell,list) and len(cell)>0:
            tmp = np.empty([1,0])
            for j in range(0,len(cell)):
                value = 0 # initialise variable

                for char in cell[j]: # iterate through characters contained in current list-item
                    value += cfg.tcpflags[char] # encode according to tcpflags dict

                dec = int(str(value),2) # convert dual to decimal number
                tmp = np.append(tmp,dec).astype(int) # append as integer

            dataset.at[i,feature] = tmp # save array

    if verbose: print(cfg.vcolor+'\npost-encoding:\n{}'.format(dataset[feature])); input('...\n'+Style.RESET_ALL)

    return
# calculates TCP flag features and encode tcp flag modes as seperate feature per flag
def tcpflagEncoder(dataset,feature,verbose=False):
    if verbose: print(cfg.vcolor+'\n'+40*'~'+' FUNCTION: tcpflagEncoder '+40*'~')
    print(cfg.vcolor+'\npre-encoding: \n{}'.format(dataset[feature]))

    # distinct: number of unique values, mode: most occuring value, modeCount: count for most occuring value
    key = ['distinct','mode','modeCount'] # AGM feature functions


    for word in key:
        newfeature = '{}: {}'.format(feature,word)
        # calculate metrics for every new feature
        if   word == 'distinct':  dataset[newfeature] = dataset[feature].apply(lambda x: len(np.unique(x)))
        elif word == 'mode':      dataset[newfeature] = dataset[feature].apply(lambda x: [item[0] for item in Counter(x).most_common(1)])
        elif word == 'modeCount': dataset[newfeature] = dataset[feature].apply(lambda x: [item[1] for item in Counter(x).most_common(1)])
        print('\n{}\n'.format(dataset[newfeature]))

    flags = ['A','P','F','R','S','U','E','C','N']
    for flag in flags: 
        # create features for every possible TCP flags, initialized with 0
        dataset.insert(0,flag,0) # position each flag as first column

    tcpmode = '{}: {}'.format(feature,'mode')
    for i in range(0,dataset.shape[0]):
        cell = dataset[tcpmode][i] # select current cell

        if isinstance(cell,list) and len(cell)>0:
            for j in range(0,len(cell)):
                for char in cell[j]:
                    dataset.at[i,char] = 1 # set all occuring mode flags to 1

    print(cfg.vcolor+'\npost-encoding:\n{}'.format(dataset[flags])+Style.RESET_ALL)
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


    # FLOW-CREATION
    print('\n\n>>> Create flows with go-flows from {}'.format(pcap))
    os.system(goflowscmd) # execute go-flows to process passed PCAP file
    dataset = importCSV(csv_import,None,verbose)
    if verbose: printdata(dataset,'go-flows CSV',verbose)


    # PER-FLOW SAMPLING
    # CAIA VECTORS
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
        convertToArray(dataset,features,1,verbose,time)
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
        key = ['forward','backward']
        for word in key:
            for feature in totalFeatures:
                if word in feature:
                    newfeature = '{},{}'.format('packetTotalCount',word)
                    print('\t> {}'.format(newfeature))
                    dataset.insert(6,newfeature,0)
                    dataset[newfeature] = dataset[feature].apply(lambda x: len(x))
                    break

        # calculate min, mean, max & stdev for CAIA features
        key     = ['min','mean','max','stdev'] # parameters to calculate
        for feature in (ipTotal+interPacket):
            for word in key:
                newfeature = '{}: {}'.format(feature,word)
                print('\t> {}'.format(newfeature))
                dataset.insert(len(dataset.columns),newfeature,0) # initialise new feature after last column

                # apply calculations on new features
                if   word == 'min':   dataset[newfeature] = dataset[feature].apply(lambda x: np.amin(x))
                elif word == 'mean':  dataset[newfeature] = dataset[feature].apply(lambda x: sum(x)/len(x))
                elif word == 'max':   dataset[newfeature] = dataset[feature].apply(lambda x: np.amax(x))
                elif word == 'stdev': dataset[newfeature] = dataset[feature].apply(lambda x: np.std(x))

        # summarize totalCounts
        print('>>> Calculate')
        for feature in totalFeatures:
            print('\t> {}:'.format(feature))
            dataset[feature] = dataset[feature].apply(lambda x: sum(x))


        # DROP, RENAME & SORT
        # drop features not necessary anymore
        print('>>> Dropping features')
        for feature in (ipTotal+interPacket):
            print('\t> {}'.format(feature))
            dataset.drop(columns=feature,inplace=True)

        # rename features
        print('>>> Rename features')
        features = dataset.columns
        for feature in features:
            tmp = feature.replace('apply(accumulate','(')
            print('\t> {} >> {}'.format(feature,tmp))
            dataset.rename(columns={feature:tmp},inplace=True)

        # sort features
        print('>>> Sort features')
        features = dataset.columns.tolist() # get list of features
        preordered = [
        'flowStartMilliseconds',
        'sourceIPAddress',
        'destinationIPAddress',
        'sourceTransportPort',
        'destinationTransportPort',
        'protocolIdentifier',
        'packetTotalCount,forward',
        'packetTotalCount,backward'
        ]
        for feature in preordered: features.remove(feature) # remove preordered features from list
        features.sort() # sort remaining features
        dataset = dataset[preordered+features]

    # AGM VECTORS
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

        print('>>> Converting accumulated features') # converts to numpy array
        convertToArray(dataset,features,1,verbose,time)
        if verbose: print(cfg.vcolor+'\n< Converted:\n{}'.format(dataset[features].head(n=20))); input('...\n'+Style.RESET_ALL)

        print('>>> Converting textual features') # converts to list
        convertToArray(dataset,textual,2,verbose,time)
        if verbose: print(cfg.vcolor+'\n< Converted:\n{}'.format(dataset[textual].head(n=20))); input('...\n'+Style.RESET_ALL)

        if n != 0:
            print('>>> Applying flow-based sampling')
            lambdaflowSampling(dataset,n,features+textual,mode,verbose,time)
            if verbose: print(cfg.vcolor+'\n< Sampled:\n{}'.format(dataset[features+textual].head(n=20))); input('...\n'+Style.RESET_ALL)
        else:
            print('>>> No flow-based sampling, processing original capture')

        if debug:
            searchNaN(dataset,features,verbose=True,time=False)
            print(cfg.vcolor+'Dtypes:\n{}'.format(dataset.dtypes)); input('...\n'+Style.RESET_ALL)


        # ENCODE tcpFlags & CONVERT to numpy array
        print('>>> Encoding TCP flags, one feature per flag')
        tcpflagEncoder(dataset,'apply(accumulate(_tcpFlags),forward)',verbose=verbose)
        textual.remove('apply(accumulate(_tcpFlags),forward)')
        print('>>> Drop textual TCP flag feature')
        dataset.drop(columns='apply(accumulate(_tcpFlags),forward)',inplace=True)


        # CALCULATIONS
        print('>>> Create features & calculate values')
        key     = ['distinct','mode','modeCount'] # AGM feature functions
        # distinct: number of unique values, mode: most occuring value, modeCount: count for most occuring value

        for feature in (features): # numpy array features
            for word in key:
                newfeature = '{}: {}'.format(feature,word)
                print('\t> {}'.format(newfeature))
                dataset.insert(len(dataset.columns),newfeature,0) # initialise new feature after last column

                if   word == 'distinct':  dataset[newfeature] = dataset[feature].apply(lambda x: len(np.unique(x)))
                elif word == 'mode':      dataset[newfeature] = dataset[feature].apply(lambda x: np.nan if (any(np.isnan(x)) and len(x)==1) else (np.bincount(x).argmax() if len(x)>0 else x))
                elif word == 'modeCount': dataset[newfeature] = dataset[feature].apply(lambda x: np.nan if (any(np.isnan(x)) and len(x)==1) else (np.count_nonzero(x==np.bincount(x).argmax() if len(x)>0 else x))) # consider single value flows containing NaN

        for feature in (textual): # textual features (destinationIPAddress)
            for word in key:
                newfeature = '{}: {}'.format(feature,word)
                print('\t> {}'.format(newfeature))
                dataset.insert(len(dataset.columns),newfeature,0) # initialise new feature after last column

                if   word == 'distinct':  dataset[newfeature] = dataset[feature].apply(lambda x: len(np.unique(x)))
                elif word == 'mode':      dataset[newfeature] = dataset[feature].apply(lambda x: [item[0] for item in Counter(x).most_common(1)])
                elif word == 'modeCount': dataset[newfeature] = dataset[feature].apply(lambda x: [item[1] for item in Counter(x).most_common(1)])

        print('\t> {}'.format('packetTotalCount')) # calculate total packets for each flow
        dataset.insert(len(dataset.columns),'packetTotalCount',0) # initialise new feature after last column
        dataset['packetTotalCount'] = dataset[features[0]].apply(lambda x: len(x))


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
        print('>>> Rename features')
        rename = dataset.columns
        for feature in (rename):
            tmp = feature.replace('apply(accumulate','(')
            print('\t> {} >> {}'.format(feature,tmp))
            dataset.rename(columns={feature:tmp},inplace=True)


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