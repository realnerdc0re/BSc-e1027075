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

# DICTIONARIES
# available sampling-modes, used for informational outputs
samplingmode = {1:'every n-th packet',2:'sample & skip n packets',3:'sample first n packets of a flow',4:'sample n, skip n-1, sample n-2 ...'}
# capture files, https://www.unb.ca/cic/datasets/ids-2017.html
filenames = {1:'Monday-WorkingHours',2:'Tuesday-WorkingHours',3:'Wednesday-WorkingHours',4:'Thursday-WorkingHours',5:'Friday-WorkingHours'}
# feature vectors
# https://pkg.go.dev/github.com/CN-TU/go-flows
featurevectors = {1:'AGM_10s.json', 2:'AGM_60s.json',3:'AGM_3600s.json',4:'CAIA_flowSampling.json',5:'CAIA_packetSampling.json'}


# PATHS
wd = Path.cwd() # working directory
hd = Path.home() # home directory
rootd = PurePath(wd).root # root directory
mntd = PurePosixPath('/mnt') # mount directory
flowfolder =  mntd / 'data' / 'CIC-IDS2017' / 'PCAP' / 'flow-sampledCSV'
fpath = mntd / 'data' / 'CIC-IDS2017' / 'PCAP'
logd = wd / 'logs'
timecsv = logd / 'time.csv'

# COMMANDS
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

# FLOW-PROCESSING functions
# returns list of accumulated per-packet features
def perpacketFeatures(dataset,keyword,verbose=False,time=False):

    features = dataset.columns
    tmp = [] # list of features matching given keyword

    if verbose:
        print('\n'+40*'~'+' FUNCTION: perpacketFeatures '+40*'~')
        print('\n'+20*'~'+' features '+20*'~'+'\n')
        print('{}'.format(features))

    print('\n'+20*'~'+' comparison '+20*'~'+'\n')
    for feature in features:
        if feature[0:len(keyword)] == keyword:
            print('== {}'.format(feature))
            tmp.append(feature)
        else: print('!= {}'.format(feature))
    print('\n'+52*'~'+'\n')

    return tmp

# converts accumulated per-packet features into np.array
def convertToArray(dataset,features,verbose=False,time=False):

    for feature in features: # iterate over given features
        print('\t> {}'.format(feature))

        # converting given strings from go-flows perpacket features or NaNs into np.arrays
        dataset[feature] = dataset[feature].apply(lambda x: np.fromstring(x[1:len(x)-1],dtype=int, sep=" ") if type(x) == str else (np.array([float('nan')]) if pd.isna(x) else x))

    return

# per-flow sampling using iterations
def flowSampling(dataset,n,features,mode=0,verbose=False,time=False):
    
    #samplingmode = {0: 'every {}-th packet'.format(n), 1: 'sample & skip {} packets'.format(n), 2: 'sample first {} packets of a flow'.format(n), 3: 'sample n, skip n-1, sample n-2 ... (n={})'.format(n)}
    
    # temporary list for sampling
    tmp = [] 

    if verbose and not superverbose:
        print(40*' '+' SAMPLING: {} (n={})'.format(samplingmode[mode],n))
        print(40*'~'+' FUNCTION: flowSampling '+40*'~')

    # iterate over list of given features
    for feature in features:

        print('\t> {}'.format(feature))

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

    return

# per-flow sampling using lambda functions
def lambdaflowSampling(dataset,n,features,mode=0,verbose=False,time=False):

    superverbose = False

    if verbose and not superverbose:
        print(40*' '+' SAMPLING: {} (n={})'.format(samplingmode[mode],n))
        print(40*'~'+' FUNCTION: flowSampling '+40*'~'+'\n')

    for feature in features: # iterate over features containing accumulated values

        print('\t> {}'.format(feature))

        if mode == 1: dataset[feature] = dataset[feature].apply(lambda x: x[::n]) # sample every n-th packet

        # CHANGE MODE == 2 and MODE == 4 TO SOMETHING ALONG THE LINES OF:
        # dataset[feature] = dataset[feature].apply(lambda x: samplecell(x))
        # where samplecell(x) is a function sampling a single cell
        # DO SIMILAR WITH SAMPLING METHOD 4
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

    # set mode argument for later Labeling.py execution
    if j<4: labelmode = ' AGM'
    elif j >= 4: labelmode = ' 5tuple'

    # PATHS & COMMANDS based on given arguments
    pcap = fpath / pcapfile
    sampledcsv = fpath / 'flow-sampledCSV' / ucsv
    labeledcsv = fpath / 'flow-sampledCSV' / lcsv
    unlabeledcsv = fpath / ucsv
    goflowsconf = wd / 'go-flows-configurations' / featurevectors[j]
    goflowscmd = "{}".format(goflowspath)+" run features "+"{}".format(goflowsconf)+" export csv "+"{}".format(fpath/unlabeledcsv)+" source libpcap "+"{}".format(pcap)
    labelingcmd = "python3 "+"{}".format(labelingpath)+" "+"{}".format(csvd/filenames[findex])+labelmode


    # INFORMATIONAL OUTPUT
    # check passed optional arguments, filepaths and forged commands
    print('\n\n'+40*' '+' FILE: {}'.format(filenames[findex]))
    print(40*'~'+' SCRIPT: rpi-FlowSampling.py '+40*'~')
    print('\n'+20*'~'+' optional arguments '+20*'~')
    print("\n{}\t--verbose\n{}\t--superverbose\n{}\t--time".format(verbose,superverbose,time))
    print('\n{}, n = {}'.format(samplingmode[mode],n))
    print('\n'+20*'~'+' paths & files'+20*'~')
    print('\nJSON:\t{}'.format(goflowsconf))
    print('PCAP:\t{}'.format(pcap))
    print('CSVs:\t{}\n\t{}\n\t{}'.format(unlabeledcsv,sampledcsv,labeledcsv))
    print('\nlogs:\t{}'.format(logd))
    print('times:\t{}'.format(timecsv))
    print('\n'+20*'~'+' commands '+20*'~')
    print("\ngo-flows: {}".format(goflowscmd))
    print("labeling: {}".format(labelingcmd))


    # FLOW-CREATION
    print('\n\n>>> Create flows with go-flows')
    os.system(goflowscmd) # execute go-flows to process passed PCAP file
    dataset = importCSV(unlabeledcsv,None,verbose) # import flow-sampled CSV created with go-flows
    if verbose: printdata(dataset,'go-flows CSV',verbose)


    # PER-PACKET SAMPLING (flow-based)
    print('>>> identify sampled features')
    keyword = 'apply(accumulate'
    features = dataset.columns # get list of all features contained in dataset
    features = perpacketFeatures(dataset,keyword,verbose,time) # get list of accumulated perpacket-features that have to be sampled

    if verbose: print('< Original:\n{}\n'.format(dataset[features].head(n=20)))

    print('>>> Converting accumulated values')
    convertToArray(dataset,features,verbose,time)

    if verbose: print('\n< Converted:\n{}'.format(dataset[features].head(n=20))), input('...\n')

    print('>>> Sampling per-packet features')
    #flowSampling(dataset,n,features,mode,verbose,time) # sample per-packet features within each flow
    lambdaflowSampling(dataset,n,features,mode,verbose,time) # sample per-packet features within each flow

    if verbose: print('\n< Sampled:\n{}'.format(dataset[features].head(n=20))), input('...\n')

    # CALCULATIONS (calculate mean values for per-packet features)
    # TODO: could do more than this, e.g. min, max, stdev...
    print('>>> Calculate mean')
    for feature in features: # iterate over per-packet features
        print('\t> {}'.format(feature))

        #dataset[feature] = dataset[feature].apply(lambda x: sum(x)/len(x) if type(x) == np.ndarray else float('NaN'))
        dataset[feature] = dataset[feature].apply(lambda x: sum(x)/len(x))

    if verbose: print('\n< Calculated:\n{}\n'.format(dataset[features].head(n=20))), input('...\n')

    if verbose: printdata(dataset,'sampled',verbose)

    # save dataframe as CSV for further preprocessing & classification
    print('>>> Saving {}'.format(sampledcsv))
    dataset.to_csv(sampledcsv, index=False)
    if verbose: print('>>> Labeling: {}\n'.format(labelingcmd))

    os.system(labelingcmd) # label benign & attack traffic as last step of preparation

    if time:
        end = timer()
        t = epochtime.time()
        print('\n(rpi-Flowsampling.py, runtime: %.3f' % (end-start),'seconds)\n')
        with open(timecsv,'a') as csvfile: # write timestamp to csv
            csvwriter = csv.writer(csvfile, delimiter=",")
            csvwriter.writerow([t,'rpi-FlowSampling.py',filenames[findex],'end'])

    exit()