#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 10 14:46:13 2021

@author: pjr
"""

from pandas import read_csv
from pandas.plotting import scatter_matrix
from matplotlib import pyplot
from scipy.stats import zscore
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer as Imputer
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import StratifiedKFold
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier
from timeit import default_timer as timer

import time as epochtime
import numpy as np
import pandas as pd
import sys
import csv
import os

# capture files, https://www.unb.ca/cic/datasets/ids-2017.html
filenames = {0:'Merged',1:'Monday-WorkingHours',2:'Tuesday-WorkingHours',3:'Wednesday-WorkingHours',4:'Thursday-WorkingHours',5:'Friday-WorkingHours'}

# get working directory
wd = os.getcwd()
# forge logfolder, timestamps & dstat logs based on wd
logfolder = wd+"/logs"
reportcsv = logfolder+'/report.csv'
resultscsv = logfolder+'/results.csv'
timecsv = logfolder+'/time.csv'

# ARGUMENT PARSING
# command line argument passthrough for better usability
import argparse
parser = argparse.ArgumentParser(description='script for preprocessing labeled CSVs')
# positional arguments
parser.add_argument('file', metavar='file', type=int,nargs=1,help='select file to process: {}'.format(filenames))
# optional arguments
parser.add_argument('-v','--verbose', action='store_true', help='output additional informations')
parser.add_argument('--superverbose', action='store_true', help='output additional informations')
parser.add_argument('-t','--time', action='store_true', help='measure function-runtimes')
parser.add_argument('-e','--export', action='store_true', help='export timestamps')
parser.add_argument('-s','--save', action='store_true', help='save CSV for further processing')
parser.add_argument('-l','--load', action='store_true', help='load CSV')
# force sampling choice
samplegroup = parser.add_mutually_exclusive_group(required=True)
samplegroup.add_argument('-f','--flowsampling', action='store_true', help='use flow-sampled CSV files')
samplegroup.add_argument('-p','--packetsampling', action='store_true', help='use per-packet sampled CSV files')
# force OS choice, https://docs.python.org/3/library/argparse.html#mutual-exclusion
osgroup = parser.add_mutually_exclusive_group(required=True)
osgroup.add_argument('--rpi', action='store_true', help='use Raspberry Pi paths (pre-sampled CSVs)')
osgroup.add_argument('--linux', action='store_true', help='use Linux paths')
osgroup.add_argument('--osx', action='store_true', help='use MacOS paths')
osgroup.add_argument('--windows', action='store_true', help='use windows paths')
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

    printdata(csvdata,'imported',True)
    if (not time): input('\n...')

    if time: 
        end = timer()
        print('\nimportCSV\n[TIME]: %.3f' % (end-start),'seconds')

    return csvdata
# outputs additional informations only shown in verbose mode
def verboseprint(dataset):
    #print('\n{}\n'.format(dataset.columns))
    print('\n{}'.format(dataset.info()))
    return
# outputs basic datset informations
def printdata(dataset,heading,verbose=False):
    print('\n\n'+40*'~'+' FUNCTION: printdata, {} '.format(heading)+40*'~')
    print('\n{}\n'.format(dataset))

    if verbose: verboseprint(dataset)

    return
# dataset description and grouped summary for 'Label'
def summary(dataset):
    #poptions()
    print('\n'+20*'~'+' summary '+20*'~')
    print('\n{}'.format(dataset.describe()))
    print('\n{}'.format(dataset.groupby('Label').size()))
    if (not time): input('\n...')
    #resetpoptions()
    return
# convert 64bit numerical values into 32bit numerical values to save memory on further processing
def conversion(dataset):

    if time: start = timer()

    print('\n\n'+40*'~'+' FUNCTION: conversion '+40*'~')
    features = list(dataset) # get feature labels
    types = dataset.dtypes # get datatype per feature
    maxValues = dataset.max() # get maximum values per feature

    print('\n'+20*'~'+' original '+20*'~')
    print('\n{}\n'.format(types))
    #print('\n{}\n'.format(maxValues))
    if (not time): input('...')

    dicttype = {} # store index numbers and target-datatypes

    print('>>> searching for 64bit numerical values...')
    i = -1
    for x in types: # determine int64/float64 features
        i = i + 1
        if (x == 'int64'):
            if (-(2**8)/2 <= maxValues[i] <= (2**8)/2):
                dicttype[features[i]] = 'int8'
            elif (-(2**16)/2 <= maxValues[i] <= (2**16)/2):
                dicttype[features[i]] = 'int16'
            elif (-(2**32)/2 <= maxValues[i] <= (2**32)/2):
                dicttype[features[i]] = 'int32'
        elif (x == 'float64'):
            if (-(2**16)/2 <= maxValues[i] <= (2**16)/2):
                dicttype[features[i]] = 'float16'
            elif (-(2**32)/2 <= maxValues[i] <= (2**32)/2):
                dicttype[features[i]] = 'float32'

    print('>>> converting values...')
    dataset = dataset.astype(dicttype,copy=False)

    types = dataset.dtypes
    print('\n'+20*'~'+' converted '+20*'~')
    print('\n{}\n'.format(types))
    if (not time): input('...')

    printdata(dataset,'after-conversion',True)

    if time: 
        end = timer()
        print('\nconversion\n[TIME]: %.3f' % (end-start),'seconds')

    return



if __name__ == '__main__':

    global verbose
    global time
    global dataset

    verbose = args.verbose
    superverbose = args.superverbose
    if superverbose: verbose = True
    time = args.time
    flowsampling = args.flowsampling
    packetsampling = args.packetsampling

    export = args.export
    save = args.save
    load = args.load

    rpi = args.rpi
    windows = args.windows
    osx = args.osx
    linux = args.linux
    findex = args.file[0]

    if time: 
        start = timer() # runtime
        t = epochtime.time() # epochtime
        print('\nClassification.py\n[EPOCH, start]: {}'.format(t))

        if export: # write timestamp to csv
            if os.path.isfile(timecsv):
                with open(timecsv,'a') as csvfile:
                    csvwriter = csv.writer(csvfile, delimiter=",")
                    csvwriter.writerow([t,'Preprocessing.py','start'])
            else:
                with open(timecsv,'w') as csvfile:
                    csvwriter = csv.writer(csvfile, delimiter=",")
                    csvwriter.writerow([t,'Preprocessing.py','start'])

    # FILEPATHS
    # path to CSV files based on OS choice
    if windows:
        fpath = r"D:\CIC-IDS2017\PCAP\flow-sampledCSV"
        ppath = r"D:\CIC-IDS2017\PCAP\packet-sampledCSV"
        chunksize = None
    elif linux:
        fpath = r"/mnt/data/CIC-IDS2017/PCAP/flow-sampledCSV"
        ppath = r"/mnt/data/CIC-IDS2017/PCAP/packet-sampledCSV"
        chunksize = None
    elif rpi:
        fpath = r"/home/dietpi/BSc-e1027075/csv/flow-sampled"
        ppath = r"/home/dietpi/BSc-e1027075/csv/packet-sampled"
        chunksize = 10**5
    # filenames of sampled, unlabeled CSVs
    csvname = ["Merged.csv","Monday-WorkingHours.csv","Tuesday-WorkingHours.csv","Wednesday-WorkingHours.csv","Thursday-WorkingHours.csv","Friday-WorkingHours.csv"]
    # set path to sampeld CSV based on optional arguments and OS
    if flowsampling:
        if windows: path = fpath+"\\"+csvname[findex]
        elif (linux or rpi): path = fpath+"/"+csvname[findex]
        savepath = fpath+r"/processed"
    elif packetsampling:
        if windows: path = ppath+"\\"+csvname[findex]
        elif (linux or rpi): path = ppath+"/"+csvname[findex]
        savepath = ppath+r"/processed"

    # OUTPUT passed optional arguments & filepath
    print('\n\n'+40*'~'+' SCRIPT: Preprocessing.py '+40*'~')
    print('\n'+20*'~'+' optional arguments '+20*'~')
    print("\n{}\t--verbose\n{}\t--superverbose\n{}\t--time\n{}\t--flowsampling\n{}\t--packetsampling".format(verbose,superverbose,time,flowsampling,packetsampling))
    print('\n\n{}'.format(path))
    if (not time): input('\n...')

    # IMPORT
    dataset = importCSV(path,None,verbose,chunksize)

    # CONVERSION
    conversion(dataset)

    if time:
        end = timer()
        t = epochtime.time()
        print('\nDataConversion.py\n[EPOCH, end]: {}'.format(t))
        print('[RUNTIME]: %.3f' % (end-start),'seconds')

    exit()