#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 11 09:25:55 2020

@author: pjr
"""

from pandas import read_csv
from timeit import default_timer as timer
from pathlib import Path, PureWindowsPath, PurePath, PurePosixPath

import time as epochtime
import numpy as np
import pandas as pd
import csv
import subprocess
import os
import re
import sys
import math


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
def convertToArray(dataset,features,verbose=False,time=False):
    for feature in features: # iterate over given features
        print('\t> {}'.format(feature))
        # converting given strings from go-flows perpacket features or NaNs into np.arrays
        dataset[feature] = dataset[feature].apply(lambda x: 
            np.fromstring(x[1:len(x)-1],dtype=int, sep=" ") if type(x) == str 
            else (np.array([float('nan')]) if pd.isna(x) 
            else x))
    return
# per-flow sampling using iterations
def flowSampling(dataset,n,features,mode=0,verbose=False,time=False):
    
    #cfg.fsamplingmode = {0: 'every {}-th packet'.format(n), 1: 'sample & skip {} packets'.format(n), 2: 'sample first {} packets of a flow'.format(n), 3: 'sample n, skip n-1, sample n-2 ... (n={})'.format(n)}
    
    # temporary list for sampling
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

    superverbose = False

    if verbose and not superverbose:
        print(40*' '+' SAMPLING: {} (n={})'.format(cfg.fsamplingmode[mode],n))
        print(40*'~'+' FUNCTION: flowSampling '+40*'~'+'\n')

    for feature in features: # iterate over features containing accumulated values

        print('\t> {}'.format(feature))

        if mode == 1: dataset[feature] = dataset[feature].apply(lambda x: x[::n]) # sample every n-th packet

        elif mode == 2: # sample n, skip n packets
            superverbose = False
            tmp = []

            for i in range(0,len(dataset.index)):
                psample = []
                tmp = dataset[feature][i].copy() # copy current cells content for sampling
                iterations = int(len(tmp)/(2*n))+1

                for j in range (0,iterations):
                    psample.extend(tmp[0:n]) # extend list with first n packets of cells content
                    tmp = tmp[2*n:] # remove sampled packets & packets to skip

                    if superverbose:
                        print('\n\n'+10*'~'+' sampling, iteration: {}/{} '.format((j+1),iterations)+10*'~')
                        print('Sampled:')
                        print(len(psample))
                        print(psample)

                dataset.at[i,feature] = psample # replace current cell with sampled values

        elif mode == 3: dataset[feature] = dataset[feature].apply(lambda x: x[:n]) # sample first n packets

        elif mode == 4: # sample n, skip n-1, sample n-2 ...
            superverbose = False
            tmp = []

            for i in range(0,len(dataset.index)):
                psample = []
                tmp = dataset[feature][i].copy()

                # counters for sampling
                m = n
                k = n

                if superverbose: print('[{}/{}]:\n{}\n{}'.format(i,len(dataset.index),tmp,type(tmp)))

                while (tmp.size > 0 and m > 0): # iterate as long as list is not empty and there are still values to sample
                    psample.extend(tmp[0:m]) # sample m values
                    k = m-1 # number of packets to skip
                    tmp = tmp[m+k:] # remove sampled plus skipped packets
                    m = k-1 # set value to sample for next iteration

                    if superverbose:
                        print('\n\n'+10*'~'+' sampling '+10*'~')
                        # only output non-empty list
                        if tmp.size > 0:
                            print('\nSliced:')
                            print(len(tmp))
                            print(tmp)
                        print('\nSampled:')
                        print(len(psample))
                        print(psample)

                dataset.at[i,feature] = psample # replace current cell with sampled values

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


if __name__ == '__main__':

    global verbose
    global time
    global check

    # set boolean variables based on argument passing
    verbose         = args.verbose
    superverbose    = args.superverbose
    time            = args.time
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


    # PER-FLOW SAMPLING post-processing for CAIA feature-vector
    keyword = 'apply(accumulate'
    print('>>> Identifying accumulated features')
    # get list of accumulated perpacket-features that have to be sampled
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
    if verbose: print('\n< Original:\n{}\n'.format(dataset[features].head(n=20)))

    print('\n\n>>> Converting accumulated values')
    convertToArray(dataset,features,verbose,time)
    if verbose: print('\n< Converted:\n{}'.format(dataset[features].head(n=20))), input('...\n')

    print('>>> Applying per-flow sampling')
    lambdaflowSampling(dataset,n,features,mode,verbose,time)
    if verbose: print('\n< Sampled:\n{}'.format(dataset[features].head(n=20))), input('...\n')


    # CALCULATIONS
    print('\n\n>>> Create features & calculate values')
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
    print('>>> Drop features')
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
    preordered = ['flowStartMilliseconds', 'sourceIPAddress', 'destinationIPAddress','sourceTransportPort', 'destinationTransportPort', 'protocolIdentifier','packetTotalCount,forward', 'packetTotalCount,backward']
    for feature in preordered: features.remove(feature) # remove preordered features from list
    features.sort() # sort remaining features
    dataset = dataset[preordered+features]

    if verbose:
        features = dataset.columns
        print('\n< Calculated:\n{}\n'.format(dataset[features].head(n=20))), input('...\n')
        printdata(dataset,'per-flow sampled',verbose)

    # save dataframe as CSV for further preprocessing & classification
    print('>>> Saving {}'.format(csv_sampled_export))
    dataset.to_csv(csv_sampled_export, index=False)


    # LABELING
    if verbose: print('>>> Labeling: {}\n'.format(labelingcmd))
    os.system(labelingcmd) # label benign & attack traffic as last step of preparation

    if time:
        end = timer()
        t = epochtime.time()
        print('\n(rpi-Flowsampling.py, runtime: %.3f' % (end-start),'seconds)\n')
        with open(cfg.time,'a') as csvfile: # write timestamp to csv
            csvwriter = csv.writer(csvfile, delimiter=",")
            csvwriter.writerow([t,'rpi-FlowSampling.py',cfg.filenames[findex],'end'])

    exit()