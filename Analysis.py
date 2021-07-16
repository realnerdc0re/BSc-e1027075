#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 10 10:32:48 2021

@author: pjr
"""
from pandas import read_csv
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.decomposition import IncrementalPCA
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier
from timeit import default_timer as timer
from pathlib import Path, PureWindowsPath, PurePosixPath
from colorama import Fore, Style
from collections import Counter


import time as epochtime
import numpy as np
import pandas as pd
import psutil
import threading
import sys
import csv
import os
import gc
import joblib
import math
import importlib
import statistics


import matplotlib.pyplot as plt
import config as cfg


# ARGUMENT PARSING
# command line argument passthrough for better usability
import argparse
parser = argparse.ArgumentParser(description='script for preprocessing labeled CSVs')
# optional arguments
parser.add_argument('-v','--verbose', action='store_true', help='output additional informations')
parser.add_argument('--superverbose', action='store_true', help='output additional dataset related informations')
parser.add_argument('--false', action='store_true', help='output false classified instances')
parser.add_argument('--pca', action='store_true', help='use PCA components specified in configuration')
parser.add_argument('--analysis', action='store_true', help='evaluate PCA component numbers, saves components into configuration when combined with --pca')
# force PCAP selection
capturegroup = parser.add_mutually_exclusive_group(required=True)
capturegroup.add_argument('--merged', action='store_true', help='use compelte dataset merged PCAP')
capturegroup.add_argument('--monday', action='store_true', help='use Monday-WorkingHours PCAP')
capturegroup.add_argument('--tuesday', action='store_true', help='use Tuesday-WorkingHours PCAP')
capturegroup.add_argument('--wednesday', action='store_true', help='use Wednesday-WorkingHours PCAP')
capturegroup.add_argument('--thursday', action='store_true', help='use Thursday-WorkingHours PCAP')
capturegroup.add_argument('--friday', action='store_true', help='use Friday-WorkingHours PCAP')
capturegroup.add_argument('--test', action='store_true', help='use excerpt from Friday-Workinghours PCAP for testing')
capturegroup.add_argument('--experiment', action='store_true', help='use already created CSV from experiment')
# force sampling method & mode
samplegroup = parser.add_mutually_exclusive_group(required=True)
samplegroup.add_argument('-f','--flowsampling', action='store_true', help='flow-based vector')
samplegroup.add_argument('-p','--packetsampling', action='store_true', help='packet-based vector')
# force vector type choice
vectorgroup = parser.add_mutually_exclusive_group(required=True)
vectorgroup.add_argument('-a','--agm', action='store_true', help='AGM vector')
vectorgroup.add_argument('-c','--caia', action='store_true', help='CAIA vector')
args = parser.parse_args()


def importCSV(csvpath,csvusecols=None,verbose=False,chunksize=None,encoding='utf-8'):  

    if time: start = timer()

    # informational output
    print('\n\n'+40*'~'+' FUNCTION: importCSV (chunksize: {}) '.format(chunksize)+40*'~')
    print('\n>>> importing CSV: {}'.format(csvpath))

    csvdata = pd.DataFrame() # initialise empty dataframe

    # if no chunksize is given, read CSV in one step, otherwise read in chunks
    if chunksize == None:
        csvdata = read_csv(csvpath,usecols=csvusecols,skipinitialspace=True,encoding=encoding)
    # chunksize determines numbers of rows per chunk
    else:
        for chunk in read_csv(csvpath,usecols=csvusecols,skipinitialspace=True,encoding=encoding,chunksize=chunksize):
            csvdata = csvdata.append(chunk)

    printdata(csvdata,'imported')

    if verbose:
        print('\n{}'.format(csvdata.groupby('Label').size()))
        print('\n{}'.format(csvdata.groupby('Attack').size()))
        if (not time): input('\n...')

    if time: 
        end = timer()
        print('\nimportCSV\n[TIME]: %.3f' % (end-start),'seconds')
    return csvdata
def splitDataframe(dataset,testsize,verbose=False,time=False):

    if time: start = timer()

    # informational output
    if verbose:
        print('\n\n'+40*'~'+' FUNCTION: splitDataframe '+40*'~')
        print('\n>>> splitting dataframe into training & test portion')

    # splitting dataset, to have data for comparison later to estimate algorithm accuracy
    data = []

    # all but the very last column put into X
    X = dataset.iloc[:,:-1]
    # very last column (label) put into Y as separate column
    Y = dataset.iloc[:,-1]
    
    # splitting up the data into training & validation datasets into 70% training & 30% validation
    Xtrain, Xtest, Ytrain, Ytest = train_test_split(X, Y, test_size=testsize, random_state=1)

    data.append(Xtrain)
    data.append(Xtest)
    data.append(Ytrain)
    data.append(Ytest)

    if time: end = timer()

    if verbose:
        print('\n'+20*'~'+' original '+20*'~')
        print('\n{}'.format(dataset))
        if (not time): input('\n')
        print('\n'+10*'~'+' X '+10*'~')
        print('\n{}'.format(X))
        print('\n'+10*'~'+' Y '+10*'~')
        print('\n{}'.format(Y))
        if (not time): input('\n')

        print('\n'+10*'~'+' Xtrain '+10*'~')
        print('\n{}'.format(Xtrain))
        print('\n'+10*'~'+' Ytrain '+10*'~')
        print('\n{}'.format(Ytrain))
        if (not time): input('\n')

        print('\n'+10*'~'+' Xtest '+10*'~')
        print('\n{}'.format(Xtest))
        print('\n'+10*'~'+' Ytest '+10*'~')
        print('\n{}'.format(Ytest))
        if (not time): input('\n')

    if time: print('\nsplitFrame\n[TIME]: %.3f' % (end-start),'seconds')
    return data
def printdata(dataset,heading,verbose=False):
    print('\n\n'+40*'~'+' FUNCTION: printdata, {} '.format(heading)+40*'~')
    print('\n{}\n'.format(dataset))
    if verbose: print('\n{}'.format(dataset.info()))
    return
def cleanString(dataset,verbose=False,time=False):

    if verbose:
        print('\n\n'+40*'~'+' FUNCTION: cleanString '+40*'~')
        print('\n>>> searching strings')

    # table containing object-types per feature
    stype = dataset.dtypes

    if verbose: print('\n{}\n'.format(stype))

    # get features (index & label) containing Strings
    istr=[]
    lstr=[]

    # cycle through all features
    for i in range(0,len(stype)):
        if stype[i]=='object':
            istr.append(i)
            lstr.append(stype.index[i])

    if (not istr): return

    # remove features containing string from dataset
    removeFeatures(dataset,lstr,verbose,time)

    if verbose:
        stype = dataset.dtypes
        print('\n'+20*'~'+' cleaned '+20*'~')
        print('\n{}'.format(stype))

    return
def removeFeatures(dataset,feature,verbose=False,time=False):

    if time: start = timer()

    # informational output
    if verbose:
        for i in range(0,len(feature)):
            print('>>> removing feature: {}'.format(feature[i]))

    # drop features to remove directly from dataset
    dataset.drop(axis=1,columns=feature,inplace=True)

    if time:
        end = timer()
        print('\nremoveFeatures\n[TIME]: %.3f' % (end-start),'seconds')

    return
def searchNaN(dataset,verbose=False,time=False):
    features = []
    # informational output
    if verbose: print('\n\n'+40*'~'+' FUNCTION: searchNaN '+40*'~'+'\n')
    print('>>> searching NaNs')

    NaNs = dataset.isna().any()
    for i in range(0,NaNs.shape[0]):
        if NaNs.iloc[i] == True:
            print('\t+ {}'.format(NaNs.index[i]))
            features.append(NaNs.index[i])

    return features
def replaceNaN(dataset,name,features,replacement,verbose=False,time=False):
    if verbose:
        print('\n\n'+40*'~'+' FUNCTION: replaceNaN '+40*'~'+'\n')
        print('NaN features: {}'.format(features))
        print('NaN replacement: {}\n'.format(replacement))

    print('>>> replace {} NaNs'.format(name))
    i = -1
    for feature in features:
        i += 1
        if verbose: print('\t>> {}'.format(feature))
        dataset[feature] = dataset[feature].fillna(replacement[i])
    return
def calcMean(dataset,features,verbose=False,time=False):
    means = [] # initialize empty list
    if verbose: print('\n\n'+40*'~'+' FUNCTION: calcMean '+40*'~'+'\n')
    print('>>> Calculating mean values')

    for feature in features:
        mean = dataset[feature].mean() # calculate mean of current feature
        means.append(mean)
        if verbose: print('\t>> {}\n\t\t< {}'.format(feature,mean))

    return means # returns list of mean values
def poptions():
    #pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.precision',3)
def resetpoptions():
    pd.reset_option('display.max_columns', 15)
    pd.reset_option('display.max_rows', 15)
    pd.reset_option('display.precision', 6)


#AGM handling
# encode TCP flags
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

        if verbose:
            print('\nPre-Encoding:\nTCP flags: {}, {}, {}\n\tmodeCount: {},{}\n\tdistinct: {},{}'.format(modeflags,len(modeflags),type(modeflags),modecount,type(modecount),distinctcount,type(distinctcount)))

        dataset.at[row,modeCountfeature] = modecount # number of occurences for mode(s)
        dataset.at[row,distinctfeature]  = distinctcount # number of distinct elements

        if isinstance(modeflags,list) and len(modeflags)>0:
            for item in modeflags:
                #print('\nPost-Encoding:\ncurrent: {}'.format(item))

                if '0' in modeflags: break # don't set any flag if nonTCP flag is within the most occuring flags
                elif len(modeflags)==1 and modeflags[0].isspace(): break
                else:
                    for char in item: # iterate occuring flags
                        dataset.at[row,char] = 1 # set flag-features to 1
                        #print('flag {}: {}'.format(item,dataset[item][row]))
            #dataset.at[row,modefeature]      = modeflags

        if verbose:
            print(cfg.vcolor+'\nPost-Encoding:\n{}: {}, {}, {}'.format(row,dataset[feature][row],dataset[modeCountfeature][row],dataset[distinctfeature][row])+Style.RESET_ALL)

    print(cfg.vcolor+'\nPost-Encoding:\n{}\n'.format(dataset[flags])+Style.RESET_ALL)
    return
# convert TCP string feature into list
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


if __name__ == '__main__':

    verbose        = args.verbose
    false          = args.false
    agm            = args.agm
    caia           = args.caia
    flowsampling   = args.flowsampling
    packetsampling = args.packetsampling
    test           = args.test
    monday         = args.monday
    tuesday        = args.tuesday
    wednesday      = args.wednesday
    thursday       = args.thursday
    friday         = args.friday
    merged         = args.merged
    pcas           = args.pca
    analysis       = args.analysis
    experiment     = args.experiment

    if agm: # select AGM vector based on arguments
        mode = 'AGM'
        if flowsampling: j = 1
        elif packetsampling: j = 6
    elif caia: # select CAIA vector based on arguments
        mode = '5tuple'
        if flowsampling: j = 4
        elif packetsampling: j = 5

    if (not experiment):
        if test: # SNAPPED TEST PCAP
            csv_import = cfg.fpath / 'TestPCAPs' / 'Friday-WorkingHours_unlabeled.csv'
            filename = 'Friday-WorkingHours.pcap'
            labelname = 'Friday-WorkingHours'
            file = cfg.fpath / 'TestPCAPs' / filename # file for go-flows
            label = cfg.fpath / 'TestPCAPs' / labelname # file for labeling script
            csv   = cfg.fpath / 'TestPCAPs' / 'Friday-WorkingHours.csv'
        elif monday: # FULL WORKDAY PCAP
            csv_import = cfg.fpath / 'Monday-WorkingHours_unlabeled.csv'
            filename = 'Monday-WorkingHours.pcap'
            labelname = 'Monday-WorkingHours'
            file = cfg.fpath / filename # file for go-flows
            label = cfg.fpath / labelname # file for labeling script
            csv   = cfg.fpath / 'Monday-WorkingHours.csv'
        elif tuesday: # FULL WORKDAY PCAP
            csv_import = cfg.fpath / 'Tuesday-WorkingHours_unlabeled.csv'
            filename = 'Tuesday-WorkingHours.pcap'
            labelname = 'Tuesday-WorkingHours'
            file = cfg.fpath / filename # file for go-flows
            label = cfg.fpath / labelname # file for labeling script
            csv   = cfg.fpath / 'Tuesday-WorkingHours.csv'
        elif wednesday: # FULL WORKDAY PCAP
            csv_import = cfg.fpath / 'Wednesday-WorkingHours_unlabeled.csv'
            filename = 'Wednesday-WorkingHours.pcap'
            labelname = 'Wednesday-WorkingHours'
            file = cfg.fpath / filename # file for go-flows
            label = cfg.fpath / labelname # file for labeling script
            csv   = cfg.fpath / 'Wednesday-WorkingHours.csv'
        elif thursday: # FULL WORKDAY PCAP
            csv_import = cfg.fpath / 'Thursday-WorkingHours_unlabeled.csv'
            filename = 'Thursday-WorkingHours.pcap'
            labelname = 'Thursday-WorkingHours'
            file = cfg.fpath / filename # file for go-flows
            label = cfg.fpath / labelname # file for labeling script
            csv   = cfg.fpath / 'Thursday-WorkingHours.csv'
        elif friday: # FULL WORKDAY PCAP
            csv_import = cfg.fpath / 'Friday-WorkingHours_unlabeled.csv'
            filename = 'Friday-WorkingHours.pcap'
            labelname = 'Friday-WorkingHours'
            file = cfg.fpath / filename # file for go-flows
            label = cfg.fpath / labelname # file for labeling script
            csv   = cfg.fpath / 'Friday-WorkingHours.csv'
        elif merged: # FULL WEEK PCAP
            csv_import = cfg.fpath / 'UnsampledMerged_unlabeled.csv'
            filename = 'UnsampledMerged.pcap'
            labelname = 'UnsampledMerged'
            file = cfg.fpath / filename # file for go-flows
            label = cfg.fpath / labelname # file for labeling script
            csv   = cfg.fpath / 'UnsampledMerged.csv'

        goflowsconf = cfg.wd / cfg.vectorfolder / cfg.vectors[j]
        goflowscmd  = '{} run features {} export csv {} source libpcap {}'.format(cfg.goflowspath,goflowsconf,csv_import,file)
        labelingcmd = 'python3 {} {} {}'.format(cfg.labelingpath,label,mode)

        print('agm: {}\ncaia: {}\nflow-based: {}\npacket-based: {}\nverbose: {}\nvector: {}\npca: {}\nanalysis: {}\n'.format(agm,caia,flowsampling,packetsampling,verbose,cfg.vectors[j],pcas,analysis))
        print('goflows: {}\nlabeling: {}\n\n'.format(goflowscmd,labelingcmd))

        print('>> Execute go-flows: {}'.format(goflowscmd))
        os.system(goflowscmd)

        print('>> Execute labeling: {}'.format(labelingcmd))
        os.system(labelingcmd)
    else: csv = cfg.fpath / 'packet-sampledCSV' / 'Merged_mode5_vector6_steps3_packetbased' / 'Merged.csv' # manually set experiment file

    print('>> Import CSV: {}'.format(csv))
    dataset = read_csv(csv,usecols=None,skipinitialspace=True,encoding='utf-8')
    printdata(dataset,'dataset',True)
    print('\n{}'.format(dataset.groupby('Label').size()))


    # PREPROCESSING

    if agm and flowsampling:
        print('>>> Identifying accumulated features')
        keyword = 'apply(accumulate'; features = filterFeatures(dataset,keyword,verbose,False)

        print('>>> Identifying textual feature') # basically manual selection via keywords
        keyword = '_tcp'; textual = filterFeatures(dataset,keyword,verbose,False)
        keyword = 'destinationIP'; textual += filterFeatures(dataset,keyword,verbose,False)

        for element in textual:
            try: features.remove(element) # remove texutal features from numeric
            except ValueError: pass # ignore eventual missing elements

        print('>>> Converting accumulated features') # converts numerical features into numpy array
        convertToArray(dataset,features,1,verbose)
        if verbose: print(cfg.vcolor+'\n< Converted:\n{}'.format(dataset[features].head(n=20))); input('...\n'+Style.RESET_ALL)

        print('>> Obtain packet total count per flow')
        dataset.insert(0,'packetTotalCount',0)
        dataset['packetTotalCount'] = dataset['apply(accumulate(protocolIdentifier),forward)'].apply(lambda x: len(x)) # obtain packetTotalCount via IP protocol numbers feature before sampling
        
        print('>>> Converting _tcpFlags feature') # converts textual feature (including whitespaces as non-TCP flag) to list
        convertToArrayTCP(dataset,'apply(accumulate(_tcpFlags),forward)',2,False,False)

        print('>> Encode TCP flags') # manually select function to call tcp encoder
        tcpflagEncoderTCP(dataset,'apply(accumulate(_tcpFlags),forward)',False)
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

        printdata(dataset,'dataset',True)
        print('\n{}'.format(dataset.groupby('Label').size()))
        input('BEFORE RENAME')

        print('>>> Rename features')
        rename = dataset.columns
        for feature in (rename):
            tmp = feature.replace('apply(accumulate','(')
            print('\t> {} >> {}'.format(feature,tmp))
            dataset.rename(columns={feature:tmp},inplace=True)

        printdata(dataset,'dataset',True)
        print('\n{}'.format(dataset.groupby('Label').size()))
        input('BEFORE SORTING')

        print('>> Sort features')
        preordered = [
            'N',
            'C',
            'E',
            'U',
            'S',
            'R',
            'F',
            'P',
            'A',
            'packetTotalCount',
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
            "Attack",
            "Label"
        ]
        dataset = dataset[preordered] # re-order dataset

        printdata(dataset,'dataset',True)
        print('\n{}'.format(dataset.groupby('Label').size()))
        input('AFTER SORTING')

    originalsplits = splitDataframe(dataset,0.30,False,False)
    originalXtrain = originalsplits[0] # copy of original data including IP addresses
    originalXtest  = originalsplits[1] # copy of original data including IP addresses

    print('>> Clean strings')
    cleanString(dataset,True,False)


    # ANALYSIS STEPS
    feature_names = dataset.columns[:-1] # feature names excluding 'Label' to compare feature-importances later on
    if agm:
        maxTotalpackets = dataset['packetTotalCount'].max()
        minTotalpackets = dataset['packetTotalCount'].min()


    # SPLIT INTO TRAINING & TEST PORTION
    print('>> Split dataset into Xtrain, Xtest, Ytrain, Ytest')
    splits = splitDataframe(dataset,0.30,False,False)
    Xtrain = splits[0]
    Xtest  = splits[1]
    Ytrain = splits[2]
    Ytest  = splits[3]
    printdata(Xtrain,'Xtrain original')
    printdata(Xtest,'Xtest original')


    # PREPROCESSING
    print('>> Search NaN features\n\t> Xtrain')
    NaN = searchNaN(Xtrain,True,False)
    print('>> Calculate mean values')
    means = calcMean(Xtrain,NaN,True,False)
    print('>> Replace NaN values with mean values')
    replaceNaN(Xtrain,'Xtrain',NaN,means,True,False)
    print('>> Search NaN features\n\t> Xtest')
    NaN = searchNaN(Xtest,True,False)
    print('>> Calculate mean values')
    means = calcMean(Xtest,NaN,True,False)
    print('>> Replace NaN values with mean values')
    replaceNaN(Xtest,'Xtest',NaN,means,True,False)


    # STANDARDSCALER
    scaler = StandardScaler(copy=False)
    print('>> Standard Scaler fit/transform Xtest')
    Xtrain = scaler.fit_transform(Xtrain)
    print('>> Standard Scaler transform Xtest')
    Xtest = scaler.transform(Xtest)
    printdata(Xtrain,'Xtrain scaled')
    print('{} {} {}'.format(Xtrain.shape,Xtrain.dtype,type(Xtrain)))
    printdata(Xtest,'Xtest scaled')
    print('{} {} {}'.format(Xtest.shape,Xtest.dtype,type(Xtest)))



    # ANALYSIS EXPLAINED VARIANCE
    if analysis and pcas:
        variance = cfg.PCA_var
        xmax = Xtrain.shape[1] # maximum number of features
        pca = PCA().fit(Xtrain) # fit data to training portion
        plt.rcParams["figure.figsize"] = (12,6) # set figure size

        fig, ax = plt.subplots()
        xi = np.arange(1, xmax+1, step=1)
        y = np.cumsum(pca.explained_variance_ratio_) # build cumulative sum for explained variance

        plt.ylim(0,1)
        plt.xlim(0,xmax)
        plt.plot(xi, y, marker='o', linestyle='--', color='#566573')
        plt.xlabel('Number of Components')
        plt.xticks(np.arange(0, xmax+1, step=1)) #change from 0-based array index to 1-based human-readable label
        plt.ylabel('Cumulative Variance (%)')
        #plt.title('cumulative variance')
        plt.axhline(y=variance, color='black', linestyle='solid') # set horizontal line to visualize %-mark
        ax.grid(axis='x')
        plt.show()

        xcalc       = np.interp(variance,y,xi) # interpolate based on given datapoints
        xcomponents = math.ceil(xcalc) # use ceil function to round up to the next integer
        print('\n< PCA components, interpolated: {}\n< PCA components, selected: {}\n'.format(round(xcalc,2),xcomponents))


        # REPLACE PARAMETER IN CONFIGURATION
        searchstring  = 'n_PCA'
        replacestring = '{} = {}\n'.format(searchstring,str(xcomponents))

        cfgpath = os.path.abspath(cfg.__file__)
        print('{}'.format(cfgpath))

        with open(cfgpath, 'r') as file: # open configuration
            configdata = file.readlines() # read all lines

        for line in range(0,len(configdata)): # iterate all lines
            if configdata[line][0:len(searchstring)] == searchstring:
                linechange = line
                break
        configdata[linechange] = replacestring
        with open(cfgpath, 'w') as file:
            file.writelines(configdata)
        file.close() #close file


    # PCA
    if pcas:
        importlib.reload(cfg) # reload framework configuration to obtain changes
        components = cfg.n_PCA
        print('components: {}'.format(components))
        input('...')

        pca = PCA(n_components=components)
        print('>> PCA n = {}'.format(components))
        print('\t> fit Xtrain')
        pca.fit(Xtrain)
        print('>> PCA transform')
        print('\t> Xtrain')
        Xtrain = pca.transform(Xtrain)
        print('\t> Xtest')
        Xtest = pca.transform(Xtest)


    # PREDICTIONS
    model = RandomForestClassifier()
    print('>> Fitting RandomForest classifier')
    model = model.fit(Xtrain,Ytrain)

    print('>> Create predictions')
    predictions = model.predict(Xtest)
    featureimportance = model.feature_importances_

    if (false and agm): # verbose output for false predictions
        print('>> Output false predictions')
        falseclassified = originalXtest[Ytest != predictions]
        falsepositives = falseclassified[falseclassified['Attack'] == 'Normal'].copy()
        falsenegatives = falseclassified[falseclassified['Attack'] != 'Normal'].copy()
        poptions() # output all rows

        if agm: # prepare output for AGM vector
            renamefeatures = {
                'sourceIPAddress': 'srcIP',
                'mode(destinationIPAddress)': 'dstIPmode',
                'mode(sourceTransportPort)': 'srcPortmode',
                'mode(destinationTransportPort)': 'dstPortmode',
                'mode(_tcpFlags)': 'TCPmode',
                'mode(ipTTL)': 'ipTTLmode',
                'mode(protocolIdentifier)': 'protocolmode'
                }
            falsenegatives.rename(columns=renamefeatures,inplace=True)
            falsepositives.rename(columns=renamefeatures,inplace=True)

            outputlist = ['A','P','F','R','S','U','E','C','N','mode(_tcpFlags)','sourceIPAddress','mode(destinationIPAddress)','mode(sourceTransportPort)','mode(destinationTransportPort)','packetTotalCount','Attack',]
            output = [8,7,6,5,4,3,2,1,0,26,25,27,9,11,14,17,20,23,31,32]
        # list for tcpEncodeDecimal
        if caia:
            outputlist = []
            output     = []

        print('\nFalse negative instances:\n{}'.format(falsenegatives.iloc[:,output])) # all rows, feature-index numbers
        print('\nFalse positive instances:\n{}'.format(falsepositives.iloc[:,output]))
        print('\n\nFalse negatives summary:\n{}\n'.format(falsenegatives.groupby('Attack').size()))

    parameters = model.get_params(deep=True)
    accuracyscore = accuracy_score(Ytest,predictions)
    matrix = confusion_matrix(Ytest,predictions)
    report = classification_report(Ytest,predictions,digits=5)


    # RESULTS
    print('\n\n'+10*'~'+' {}: results '.format(model)+10*'~')
    print('\nModel-Parameters:\n{}'.format(parameters))
    print('\n\nAccuracy-Score: %.5f' % (accuracyscore))

    if not pcas:
        print(cfg.vcolor+'\n\nFeature-Importance Labels:\n{}\n{} elements, {}'.format(feature_names,len(feature_names),type(feature_names)))
        print('\nFeature-Importance Overview:')
        zipped = sorted(zip(feature_names,featureimportance),key=lambda x: x[1],reverse=True) # sort aggregated elements from iterables based on feature-importance value
        for feature,value in zipped:
            print('{}%\t{}'.format(format(value*100,".2f"),feature))
        print('\nFeature-Importance:\n{}\n{} elements, {} {}'.format(featureimportance,len(featureimportance),type(featureimportance),np.sum(featureimportance))+Style.RESET_ALL)

    if agm:
        print('\npacketTotalCount, minimum: {}'.format(minTotalpackets))
        print('packetTotalCount, maximum: {}'.format(maxTotalpackets))
        #for index,row in dataset.iterrows(): # search
        #    if row['packetTotalCount'] == maxTotalpackets:
        #        print('Flow containing maximum packetTotalCount:\n{}'.format(dataset.loc[[index]])) # output dataframe row with highest aggregated packet count

    print('\n\nConfusion-Matrix:\n')
    print('t       p r e d i c t')
    print('r         "0"    "1"')
    print('u  "0":',matrix[0])
    print('e  "1":',matrix[1])
    print('\n\nClassification-Report:\n\n',report)