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

# DICTIONARIES
# available sampling-modes, used for informational outputs
samplingmode = {1:'every n-th packet',2:'sample & skip n packets',3:'sample first n packets of a flow',4:'sample n, skip n-1, sample n-2 ...'}
# capture files, https://www.unb.ca/cic/datasets/ids-2017.html
filenames = {1:'Monday-WorkingHours',2:'Tuesday-WorkingHours',3:'Wednesday-WorkingHours',4:'Thursday-WorkingHours',5:'Friday-WorkingHours'}
# feature vectors
featurevectors = {1:'AGM_10s.json', 2:'AGM_60s.json',3:'AGM_3600s.json',4:'CAIA_flowSampling.json',5:'CAIA_packetSampling.json'}


# PATHS & COMMANDS
wd = Path.cwd() # working directory
hd = Path.home() # home directory
rootd = PurePath(wd).root # root directory
mntd = PurePosixPath('/mnt') # mount directory
flowfolder =  mntd / 'data' / 'CIC-IDS2017' / 'PCAP' / 'flow-sampledCSV'
fpath = mntd / 'data' / 'CIC-IDS2017' / 'PCAP'
logd = wd / 'logs'
timecsv = logd / 'time.csv'
# commands
goflowspath = hd / 'Git' / 'go-flows' / 'go-flows'
labelingpath = mntd / 'data' / 'BSc-e1027075' / 'Labeling.py'


# ARGUMENT PARSING
# command line argument passthrough for better usability
import argparse
parser = argparse.ArgumentParser(description='script for sampling PCAP files via go-flows (flow-based sampling), output is CSV')
# positional arguments
parser.add_argument('mode', metavar = 'mode', type=int,nargs=1,help='select sampling mode: {}'.format(samplingmode))
parser.add_argument('file', metavar = 'file', type=int,nargs=1,help='select file to process: {}'.format(filenames))
parser.add_argument('n', metavar='n', type=int,nargs=1,help='integer used to determine sampling steps')
parser.add_argument('j', metavar='j', type=int,nargs=1,help='choose feature-vector: {}'.format(featurevectors))
# optional arguments
parser.add_argument('-v','--verbose', action='store_true', help='output additional informations')
parser.add_argument('--superverbose', action='store_true', help='output additional informations, including loop iteration output')
parser.add_argument('-t','--time', action='store_true', help='measure runtimes')
args = parser.parse_args()


# set/reset options for maximum columns to display and floating point output precision
def poptions():
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.precision',3)
def resetpoptions():
    pd.reset_option('display.max_columns', 15)
    pd.reset_option('display.max_rows', 15)
    pd.reset_option('display.precision', 6)
# import CSV
def importCSV(csvpath,csvusecols=None,verbose=False,encoding='utf-8'):
    # informational output
    print('\n\n'+40*'~'+' FUNCTION: importCSV '+40*'~')
    print('\n>>> importing CSV...')
    csvdata = read_csv(csvpath,usecols=csvusecols,skipinitialspace=True,encoding=encoding)
    return csvdata

# OUTPUT functions
# outputs additional informations only shown in verbose mode
def verboseprint(dataset):
    print('\nDataset, Shape:\n',dataset.shape)
    print('\nDataset, Columns:\n',dataset.columns)
    print('\n\nDataFrame, Info:')
    dataset.info(max_cols=10)
    return
# outputs basic datset informations
def printdata(dataset,heading,verbose=False):
    print('\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION: printdata,',heading,'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    #print('\nDataset:\n',dataset.head(10))
    print('\nDataset:\n',dataset)
    print(dataset.describe())
    if verbose:
        verboseprint(dataset)
    #input('press ENTER to continue...\n')
    return

# FLOW-PROCESSING functions
# returns list of features that contains multiple packet-values based on feature-keyword
def perpacketFeatures(dataset,keyword,verbose=False,time=False):
    
    # get all features from given dataset
    features = dataset.columns
    # temporary list of features that match given keyword
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
        print('\n\t{}'.format(tmp))
        if (not time): input('\n...')
            
    return tmp
# TODO: improve speed? pretty slow
# convert single string or single integer (given with go-flows accumulate function or after NaN cleaning) into list of integers
# necessary to get the values as list of integers for sampling and calculations
def convertToList(dataset,features,verbose=False,time=False):
    
    for feature in features:
        
        if verbose and not superverbose:
            print('\n\n'+40*'~'+' FUNCTION: convertToList: {} '.format(feature)+40*'~')
            print('>>> processing...')
        
        for i in range(0,len(dataset.index)):
            if superverbose:
                print('\n'+20*'~'+' FUNCTION: convertToList: {}, row: {}/{} '.format(feature,(i+1),len(dataset.index))+20*'~')
                print('original:\n', dataset[feature][i])
                print('type:\n', type(dataset[feature][i]))
            
            # remove first and last character of the string (basically the brackets)
            if type(dataset[feature][i])==str: 
                dataset.at[i,feature] = dataset[feature][i][1:len(dataset[feature][i])-1]
                # convert strings to integers, use whitespace as separator, saves as list
                dataset.at[i,feature] = [int(s) for s in dataset[feature][i].split(' ')]
            # consider single integers (like replacements for NaNs)
            elif type(dataset[feature][i]==int):
                # store value as list-element
                dataset.at[i,feature] = [dataset[feature][i]]
            # output warning for other cases
            else:
                print('\n[WARNING] feature {} has wrong data-type!'.format(feature))
                if (not time): input('\n...')
            
            if superverbose:
                print('transformed:\n', dataset[feature][i])
                print('type:\n', type(dataset[feature][i]))
        
    
    if verbose and (not time): input('\n...')
            
    return
# sample first and every n-th package afterwards from given list of features
def flowSampling(dataset,n,features,mode=0,verbose=False,time=False):
    
    #samplingmode = {0: 'every {}-th packet'.format(n), 1: 'sample & skip {} packets'.format(n), 2: 'sample first {} packets of a flow'.format(n), 3: 'sample n, skip n-1, sample n-2 ... (n={})'.format(n)}
    
    # temporary list for sampling
    tmp = [] 
    
    # iterate over list of given features
    for feature in features:
        
        if verbose and not superverbose:
            print('\n'+40*' '+' SAMPLING: {} (n={})'.format(samplingmode[mode],n))  
            print(40*'~'+' FUNCTION: flowSampling: {} '.format(feature)+40*'~')
            print('>>> processing...')
        
        # iterate over every single row of the feature
        for i in range(0,len(dataset.index)):
            # list to collect packets to sample, has to be reset for every row iteration
            psample = []
            
            if superverbose:
                print('\n\n'+40*' '+' SAMPLING: {} '.format(samplingmode[mode])+' (n={}).format(n)')
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
    
    if verbose and (not superverbose) and (not time):
        input('\n...')
    
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
    verbose = args.verbose
    superverbose = args.superverbose
    if superverbose:
        verbose = True
    time = args.time

    mode = args.mode[0] # sampling-mode
    findex = args.file[0] # filename
    n = args.n[0] # sampling steps
    j = args.j[0] # feature-vector

    csvd = flowfolder # csv directory
    lcsv = str(filenames[findex])+str('.csv') # labeled CSV
    ucsv = str(filenames[findex])+str('_unlabeled.csv') # unlabeled CSV
    csvsave = csvd / lcsv
    pcapfile = filenames[findex]+str('.pcap')

    if not os.path.exists(csvd): os.mkdir(csvd)


    if time: 
        start = timer()
        t = epochtime.time()
        with open(timecsv,'a') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=",")
            csvwriter.writerow([t,'rpi-FlowSampling.py',filenames[findex],'start'])


    # TODO: make list for all necessary PCAP files from dataset
    # TODO: use argument parsing to select sampling-mode from command line
    # TODO: save flow-based sampled CSV into folder csvpath for further classification

    # set mode for labeling
    if j<4:
        labelmode = ' AGM'
    elif j >= 4:
        labelmode = ' 5tuple'

    # PATHS & COMMANDS
    # based on given arguments
    pcap = fpath / pcapfile
    sampledcsv = fpath / 'flow-sampledCSV' / ucsv
    labeledcsv = fpath / 'flow-sampledCSV' / lcsv
    unlabeledcsv = fpath / ucsv
    goflowsconf = wd / 'go-flows-configurations' / featurevectors[j]
    goflowscmd = "{}".format(goflowspath)+" run features "+"{}".format(goflowsconf)+" export csv "+"{}".format(fpath/unlabeledcsv)+" source libpcap "+"{}".format(pcap)
    labelingcmd = "python3 "+"{}".format(labelingpath)+" "+"{}".format(csvd/filenames[findex])+labelmode


    # check passed optional arguments, filepaths and forged commands
    print('\n\n'+40*' '+' FILE: {}'.format(filenames[findex]))
    print(40*'~'+' SCRIPT: rpi-FlowSampling.py '+40*'~')
    print('\n'+20*'~'+' optional arguments '+20*'~')
    #print("\n{}\t--verbose\n{}\t--superverbose\n{}\t--time\n{}\t--osx\n{}\t--windows".format(verbose,superverbose,time,osx,windows))
    print("\n{}\t--verbose\n{}\t--superverbose\n{}\t--time".format(verbose,superverbose,time))
    print('\n{}, n = {}'.format(samplingmode[mode],n))
    print('\n'+20*'~'+' paths & files'+20*'~')
    print('\nJSON:\t{}'.format(goflowsconf))
    print('PCAP:\t{}'.format(pcap))
    print('CSVs:\t{}\n\t{}\n\t{}'.format(unlabeledcsv,sampledcsv,labeledcsv))
    #print('sampled:\t{}'.format(sampledcsv))
    #print('labeled:\t{}'.format(labeledcsv))
    print('\nlogs:\t{}'.format(logd))
    print('times:\t{}'.format(timecsv))
    print('\n'+20*'~'+' commands '+20*'~')
    print("\ngo-flows: {}".format(goflowscmd))
    print("labeling: {}".format(labelingcmd))
    if (not time): input('\n...') 


    # FLOW-CREATION & LABELING
    # execute go-flows to process passed PCAP file
    print("\n\n>>> create flow-CSV from PCAP with go-flows")
    os.system(goflowscmd)
    # import output CSV from go-flows
    #poptions()
    dataset = importCSV(unlabeledcsv,None,verbose)
    if verbose:
        printdata(dataset,'go-flows CSV',verbose)
        if (not time): input('\n...') 


    # SAMPLING (flow-based)
    # get list of all features contained in dataset
    features = dataset.columns
    # get list of accumulated perpacket-features that have to be sampled
    features = perpacketFeatures(dataset,'apply(accumulate',verbose,time)
    # convert content of perpacket-features into an actual list for further processing
    print('\n\n>>> convert sampled values into list')
    convertToList(dataset,features,verbose,time)
    # sample perpacket-features
    flowSampling(dataset,n,features,mode,verbose,time)


    # CALCULATIONS
    # TODO: should do more than this, e.g. min, max, stdev...
    # calculate mean of remaining packet values after sampling
    for feature in features:
        print('\n\n>>> processing sampled packets: {}'.format(feature))
        for i in range(0,len(dataset.index)):
            dataset.at[i,feature] = sum(dataset[feature][i])/len(dataset[feature][i])

        if verbose:
            print('\n\n'+20*'~'+' Calculation, mean '+20*'~')
            print('\n{}'.format(dataset[feature]))
            if (not time): input('\n...') 

    if verbose:
        printdata(dataset,'sampled',verbose)
        if not time: input('\n...')

    # save dataframe as CSV for further preprocessing & classification
    print("\n>>> save data to CSV")
    dataset.to_csv(sampledcsv, index=False)
    #dataset.to_csv(csvsave, index=False)
    # label flow-based sampled CSV as last step of preparation for further classification
    print("\n>>> label CSV for further classification")
    print(">>> {}".format(labelingcmd))
    os.system(labelingcmd)

    if time: 
        end = timer()
        t = epochtime.time()
        print('\n(rpi-Flowsampling.py, runtime: %.3f' % (end-start),'seconds)\n')
        with open(timecsv,'a') as csvfile: # write timestamp to csv
            csvwriter = csv.writer(csvfile, delimiter=",")
            csvwriter.writerow([t,'rpi-FlowSampling.py',filenames[findex],'end'])

    if (not time): input('\n...')  
    exit()