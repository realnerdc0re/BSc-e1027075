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

import config as cfg


# ARGUMENT PARSING
# command line argument passthrough for better usability
import argparse
parser = argparse.ArgumentParser(description='script for preprocessing labeled CSVs')
# optional arguments
parser.add_argument('-v','--verbose', action='store_true', help='output additional informations')
parser.add_argument('--superverbose', action='store_true', help='output additional dataset related informations')
parser.add_argument('--false', action='store_true', help='output false classified instances')
parser.add_argument('--pca', action='store_true', help='output false classified instances')
# force PCAP selection
capturegroup = parser.add_mutually_exclusive_group(required=True)
capturegroup.add_argument('--merged', action='store_true', help='use compelte dataset merged PCAP')
capturegroup.add_argument('--friday', action='store_true', help='use Friday-WorkingHours PCAP')
capturegroup.add_argument('--test', action='store_true', help='use excerpt from Friday-Workinghours PCAP for testing')
# force sampling method & mode
samplegroup = parser.add_mutually_exclusive_group(required=True)
samplegroup.add_argument('-f','--flowsampling', action='store_true', help='flow-based vector')
samplegroup.add_argument('-p','--packetsampling', action='store_true', help='packet-based vector')
# force vector type choice
vectorgroup = parser.add_mutually_exclusive_group(required=True)
vectorgroup.add_argument('-a','--agm', action='store_true', help='AGM vector')
vectorgroup.add_argument('-c','--caia', action='store_true', help='CAIA vector')
args = parser.parse_args()



# import CSV
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
def tcpflagEncoder(dataset,feature,verbose=False):
    if verbose:
        print(cfg.vcolor+'\n'+40*'~'+' FUNCTION: tcpflagEncoder '+40*'~')
        print('\ntcpFlags: {}\n\npre-encoding: \n{}'.format(cfg.tcpflags,dataset[feature])+Style.RESET_ALL)

    # create features for all possible TCP flags, initialized with 0
    flags = ['A','P','F','R','S','U','E','C','N']
    for flag in flags:
        dataset.insert(0,flag,0)

    for i in range(0,dataset.shape[0]):
        cell = dataset[feature][i] # current cell

        if isinstance(cell,str) and len(cell)>0:
            for j in range(0,len(cell)):
                for char in cell[j]:
                    dataset.at[i,char] = 1

    if verbose: print(cfg.vcolor+'\npost-encoding:\n{}'.format(dataset[flags])+Style.RESET_ALL)
def tcpflagEncoderDecimal(dataset,feature,verbose=False):
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
        elif math.isnan(cell): # set NaN to 0
            dataset.at[i,feature] = int(0)

    if verbose: print(cfg.vcolor+'\npost-encoding:\n{}'.format(dataset[feature])+Style.RESET_ALL)

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

if __name__ == '__main__':

    verbose        = args.verbose
    false          = args.false
    agm            = args.agm
    caia           = args.caia
    flowsampling   = args.flowsampling
    packetsampling = args.packetsampling
    test           = args.test
    friday         = args.friday
    merged         = args.merged
    pca            = args.pca

    if agm:
        mode = 'AGM'
        if flowsampling: j = 1
        elif packetsampling: j = 6
    elif caia:
        mode = '5tuple'
        if flowsampling: j = 4
        elif packetsampling: j = 5

    if test: # SNAPPED TEST PCAP
        csv_import = cfg.fpath / 'TestPCAPs' / 'Friday-WorkingHours_unlabeled.csv'
        filename = 'Friday-WorkingHours.pcap'
        labelname = 'Friday-WorkingHours'
        file = cfg.fpath / 'TestPCAPs' / filename # file for go-flows
        label = cfg.fpath / 'TestPCAPs' / labelname # file for labeling script
        csv   = cfg.fpath / 'TestPCAPs' / 'Friday-WorkingHours.csv'
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

    print('agm: {}\ncaia: {}\nflow-based: {}\npacket-based: {}\nverbose: {}\nvector: {}\n'.format(agm,caia,flowsampling,packetsampling,verbose,cfg.vectors[j]))
    print('goflows: {}\nlabeling: {}\n\n'.format(goflowscmd,labelingcmd))

    print('>> Execute go-flows: {}'.format(goflowscmd))
    os.system(goflowscmd)

    print('>> Execute labeling: {}'.format(labelingcmd))
    os.system(labelingcmd)

    print('>> Import CSV: {}'.format(csv))
    dataset = read_csv(csv,usecols=None,skipinitialspace=True,encoding='utf-8')
    if verbose:
        printdata(dataset,'dataset',True)
        print('\n{}'.format(dataset.groupby('Label').size()))

    # PREPROCESSING
    if agm:
        print('>> Encode TCP flags') # manually select function to call tcp encoder
        #tcpflagEncoder(dataset,'mode(_tcpFlags)',True)
        tcpflagEncoderDecimal(dataset,'mode(_tcpFlags)',True)

    originalsplits = splitDataframe(dataset,0.30,False,False)
    originalXtest = originalsplits[1] # copy of original data including IP addresses

    print('>> Clean strings')
    cleanString(dataset,True,False)

    print('>> Search NaN features')
    NaN = searchNaN(dataset,True,False)

    print('>> Calculate mean values')
    means = calcMean(dataset,NaN,True,False)

    print('>> Replace NaN values with mean values')
    replaceNaN(dataset,'dataset',NaN,means,True,False)

    print('>> Split dataset into Xtrain, Xtest, Ytrain, Ytest')
    splits = splitDataframe(dataset,0.30,False,False)
    Xtrain = splits[0]
    Xtest  = splits[1]
    Ytrain = splits[2]
    Ytest  = splits[3]
    printdata(Xtrain,'Xtrain original')
    printdata(Xtest,'Xtest original')

    # STANDARDSCALER
    scaler = StandardScaler(copy=False)
    print('>> Standard Scaler fit/transform Xtest')
    Xtrain = scaler.fit_transform(Xtrain)
    print('>> Standard Scaler transform Xtest')
    Xtest = scaler.transform(Xtest)
    printdata(Xtrain,'Xtrain scaled')
    printdata(Xtest,'Xtest scaled')

    # PCA
    if pca:
        components = 4
        pca = PCA(n_components=components)
        print('>> PCA fit to Xtrain, n = {}'.format(components))
        pca.fit(Xtrain)
        print('>> PCA transform Xtrain, Xtest')
        Xtrain = pca.transform(Xtrain)
        Xtest = pca.transform(Xtest)

    # PREDICTIONS
    model = RandomForestClassifier()
    print('>> Fitting RandomForest classifier')
    model = model.fit(Xtrain,Ytrain)

    print('>> Create predictions')
    predictions = model.predict(Xtest)

    if false: # verbose output on false predictions
        print('>> Output false predictions')
        falseclassified = originalXtest[Ytest != predictions]
        falsepositives = falseclassified[falseclassified['Attack'] == 'Normal'].copy()
        falsenegatives = falseclassified[falseclassified['Attack'] != 'Normal'].copy()

        # rename feature for better readability
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

        poptions() # output all rows
        # list for tcpEncode
        outputlist = ['A','P','F','R','S','U','E','C','N','mode(_tcpFlags)','sourceIPAddress','mode(destinationIPAddress)','mode(sourceTransportPort)','mode(destinationTransportPort)','Attack',]
        output = [8,7,6,5,4,3,2,1,0,26,25,27,9,11,14,17,20,23,32]
        # list for tcpEncodeDecimal

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
    print('\n\nConfusion-Matrix:\n')
    print('t       p r e d i c t')
    print('r         "0"    "1"')
    print('u  "0":',matrix[0])
    print('e  "1":',matrix[1])
    print('\n\nClassification-Report:\n\n',report)