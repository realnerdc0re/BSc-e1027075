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


import config as cfg # necessary configurations from config.py

# create base-folders if necessary
if not os.path.exists(cfg.logs):            os.mkdir(cfg.logs)
if not os.path.exists(cfg.fpath):           os.mkdir(cfg.fpath)
if not os.path.exists(cfg.packetfolder):    os.mkdir(cfg.packetfolder)


# ARGUMENT PARSING
# command line argument passthrough for better usability
import argparse
parser = argparse.ArgumentParser(description='script for preprocessing labeled CSVs')
# positional arguments
parser.add_argument('file', metavar='file', type=int,nargs=1,help='select file to process: {}'.format(cfg.filenames))
parser.add_argument('n', metavar='n', type=int,nargs=1,help='non-zero integer, used to determine sampling-steps')
parser.add_argument('j', metavar='j', type=int,nargs=1,help='select feature-vector: {}'.format(cfg.vectors))
parser.add_argument('batch', metavar='batch', type=int,nargs=1,help='choose numerical value for StandardScaler batchsize')
# optional arguments
parser.add_argument('-v','--verbose', action='store_true', help='output additional informations')
parser.add_argument('--superverbose', action='store_true', help='output additional informations')
parser.add_argument('-m','--model', action='store_true', help='import model')
parser.add_argument('-s','--save', action='store_true', help='save model')
parser.add_argument('-l','--load', action='store_true', help='load preprocessed CSV')
parser.add_argument('-r','--remote', action='store_true', help='execution on remote machine, different method to kill dstat, changing foldername for results')
# display runtime or export timestamps and dstat-logs
timegroup = parser.add_mutually_exclusive_group(required=False)
timegroup.add_argument('-t','--time', action='store_true', help='display script runtime')
timegroup.add_argument('-e','--export', action='store_true', help='export timestamps & resource logs')
# force sampling method & mode
samplegroup = parser.add_mutually_exclusive_group(required=True)
samplegroup.add_argument('-f','--flowsampling', metavar='m', type=int, nargs=1, choices=cfg.fsamplingmode, help='select sampling-mode: {}'.format(cfg.fsamplingmode))
samplegroup.add_argument('-p','--packetsampling', metavar='m', type=int, nargs=1, choices=cfg.psamplingmode, help='select sampling-mode: {}'.format(cfg.psamplingmode))
args = parser.parse_args()


# starting dstat logging threaded
def threadFunc(): os.system(dstatcmd.format(cfg.dstat))
th = threading.Thread(target=threadFunc)

# progress bar signaling time to wait for dstat to write latest logs
def progressBar(it, prefix="", size=60, file=sys.stdout):
    count = len(it)
    def show(j):
        x = int(size*j/count)
        file.write("%s[%s%s] %i/%i\r" % (prefix, "·"*x, " "*(size-x), j, count))
        file.flush()

    show(0)

    for i, item in enumerate(it):
        yield item
        show(i+1)

    file.write("\n")
    file.flush()
    return
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
    if (not time): input('\n')

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
    if (not time): input('\n')
    #resetpoptions()
    return

# PRE-PROCESSING
# convert to smaller datatypes to reduce memory consumption
def conversion(dataset,verbose=False):

    if time: start = timer()

    if verbose: print('\n\n'+40*'~'+' FUNCTION: conversion '+40*'~')

    features = list(dataset) # get feature labels
    types = dataset.dtypes # get datatype per feature
    maxValues = dataset.max() # get maximum values per feature

    if verbose:
        print('\n'+20*'~'+' original '+20*'~')
        print('\n{}\n'.format(types))
        #print('\n{}\n'.format(maxValues))
        if (not time): input('')

    dicttype = {} # store index numbers and target-datatypes

    if verbose: print('>>> searching for 64bit numerical values')
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

    if verbose: print('>>> converting values')
    dataset = dataset.astype(dicttype,copy=False)

    types = dataset.dtypes
    if verbose:
        print('\n'+20*'~'+' converted '+20*'~')
        print('\n{}\n'.format(types))
        if (not time): input('')

    if verbose: printdata(dataset,'after-conversion',True)

    if time: 
        end = timer()
        if verbose: print('\nconversion\n[TIME]: %.3f' % (end-start),'seconds')

    return dataset
# replace all Inf values with given replacement
def cleanInf(dataset,mode,verbose=False,time=False):

    if time: start = timer()

    modename = {0: 'value', 1: 'mean', 2: 'min', 3: 'max', 4: 'std'}

    # informational output
    if verbose:
        print('\n\n'+40*'~'+' FUNCTION: cleanInf '+40*'~')
        print('\n>>> searching Infs')

    # create pseudo-random values to a feature, add inf value for testing purpose
    #createRandom(dataset,'Random',False,False)
    #dataset.at[3,'Random'] = float("inf")

    # get summary for maximum values
    vmax = dataset.max(numeric_only=True)

    # get features (index & label) containing Infinite values
    # feature (column)-index
    iinf = []
    # feature (column)-label
    linf = []

    i = -1
    for x in vmax:
        i=i+1
        # if entry is float 'inf', append to list
        if(x == float('inf')):
            iinf.append(i)
            linf.append(vmax.index[i])

    # get row-number for Infinite values
    # initialise empty list
    iindex=[]   
    # empty list to fill with numpy arrays containing the row numbers for infinite values
    infRows=[]

    '''
    # variable i to adress numpy elements
    i = -1
    # cycles through features to determine row numbers containing Infinite values
    for column in linf:
        i = i+1

        #if (verbose and not time): print('\n{LOOP OUTPUT} feature:',column,'\nrow-numbers matching Infinite:')
        # cycling through all rows
        for j in range(0,dataset.shape[0]):
            if dataset[column][j] == float('inf'):
                iindex.append(j)
        # create temporary array from index list
        tmp = np.array(iindex)
        infRows.append(tmp)
        # reset index list
        iindex=[]
    '''

    # replace cells containing Infinite values with e.g. mean values of that feature or whatever is necessary
    if iinf:
        
        # variable i to adress numpy elements
        i = -1
        # cycles through features to determine row numbers containing Infinite values
        for column in linf:
            i = i+1

            #if (verbose and not time): print('\n{LOOP OUTPUT} feature:',column,'\nrow-numbers matching Infinite:')
            # cycling through all rows
            for j in range(0,dataset.shape[0]):
                if dataset[column][j] == float('inf'):
                    iindex.append(j)
            # create temporary array from index list
            tmp = np.array(iindex)
            infRows.append(tmp)
            # reset index list
            iindex=[]

        if verbose: 
            print('\n{}'.format(vmax))
            if (not time): input('\n')

        i = -1
        # cycle through features and replace Infinite values
        for column in linf:    
            i = i+1
            Infcount = len(infRows[i])

            # create series with removed Inf values
            tmp = removeCells(dataset,column,infRows[i],False,False)
            # calculate specific feature values for further replacement of Infs
            tmean = tmp.mean()
            tmax = tmp.max()
            tmin = tmp.min()
            tstd = tmp.std()

            if verbose:
                print('\n'+20*'~'+' replacement: {} '.format(column)+20*'~')
                print('\nmean: {}\nstd: {}\nmin: {}\nmax: {}'.format(tmean,tstd,tmin,tmax))
                print('\nmode: {}'.format(modename[mode]))
                print('cells: {}'.format(Infcount))

            # replacement-modes
            if mode == 0: value = 0
            elif mode == 1: value = tmean
            elif mode == 2: value = tmin
            elif mode == 3: value = tmax
            elif mode == 4: value = tstd

            if verbose: print('\n>>> replacing Infinite values: {}'.format(column))
            writeCells(dataset,column,infRows[i],value,verbose,False)

    else: return

    if verbose:
        vmax = dataset.max(numeric_only=True)
        print('\n'+20*'~'+' cleaned '+20*'~')
        print('\n{}'.format(vmax))
        if (not time): input('\n')

    if time: 
        end = timer()
        print('\ncleanInf\n[TIME]: %.3f' % (end-start),'seconds')

    # return whatever needed for method to clean specific cells or drop features    
    return
# replace all NaNs with given replacement
def cleanNaN(dataset,replacement,verbose=False,time=False):

    if time: start = timer()

    # informational output
    if verbose:
        print('\n\n'+40*'~'+' FUNCTION: cleanNaN '+40*'~')
        print('\n>>> searching NaNs')

    # summary for NaN values
    vNaN = dataset.isnull().sum()
    lNaN = []

    if verbose: print('\n{}\n'.format(vNaN))

    i = -1
    for value in vNaN:
        i += 1
        # if there is at least one NaN value in the summary
        if(value > 0):
            lNaN.append(vNaN.index[i])

    # cycles through features containing NaN values
    for column in lNaN:
        if verbose: print('>>> replacing NaNs: {}'.format(column))
        dataset[column] = dataset[column].replace(np.nan, replacement)

    if time:
        end = timer()
        print('\ncleanNaN\n[TIME]: %.3f' % (end-start),'seconds')

    return
# remove features containing strings from given df
def cleanString(dataset,verbose=False,time=False):

    if time: start = timer()

    # informational output
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

    if time:
        end = timer()

    if verbose:
        stype = dataset.dtypes
        print('\n'+20*'~'+' cleaned '+20*'~')
        print('\n{}'.format(stype))
        if (not time): input('\n')

    if time: print('\ncleanString\n[TIME]: %.3f' % (end-start),'seconds')

    return
# remove single-value-features from given df
def cleanSingleValue(dataset,verbose=False,time=False):

    if time: start = timer()

    # informational output
    if verbose:
        print('\n\n'+40*'~'+' FUNCTION: cleanSingleValue '+40*'~')
        print('\n>>> searching unique-value features')

    ldrop = []
    # summary for non-unique values
    counts = dataset.nunique()

    # list of features contained in dataset
    labels = dataset.columns.values

    # iterates over all features
    for i in range(0,len(counts)):
        # check for features containing a single unique value
        if counts[i] == 1:
            # add such feature to droplist
            ldrop.append(labels[i])

    if ldrop: # if single-value features exists
        if verbose: print('\n{}\n'.format(counts))

        removeFeatures(dataset,ldrop,verbose,time)

        if verbose:
            counts = dataset.nunique()
            print('\n\n'+20*'~'+' cleaned '+20*'~')
            print('\n{}'.format(counts))

    if time: 
        end = timer()
        print('\ncleanSingleValue\n[TIME]: %.3f' % (end-start),'seconds')

    return
# remove given feature from given df
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
# manipulate content of given cells from given dataframe-feature
def writeCells(dataset,feature,cells,content,verbose=False,time=False):

    if time: start = timer()

    # informational output
    if verbose:
        print('\n'+10*'~'+' writeCells '+10*'~')
        print('\nvalue: {}'.format(content))
        print('cells: {}'.format(len(cells)))
        print('\n>>> replace cells content with {}'.format(content))

    # replace given cells with given content
    for j in cells:
        dataset.at[j,feature] = content

    if time: 
        end = timer()
        print('\nwriteCells\n[TIME]: %.3f' % (end-start),'seconds')

    return
# split given df into training & test portions
def splitDataframe(dataset,testsize,verbose=False,time=False):
    
    if time: start = timer()
    
    # informational output
    if verbose:
        print('\n\n'+40*'~'+' FUNCTION: splitDataframe '+40*'~')
        print('\n>>> splitting dataframe into training & test portion')
    
    
    # splitting dataset, to have data for comparison later to estimate algorithm accuracy
    # write dataset values into array
    #array = dataset.values
    # empty list to return X_train, X_validation, Y_train, Y_validation
    data = []

    # all but the very last column put into X
    X = dataset.iloc[:,:-1]
    # very last column (label) put into Y as separate column
    Y = dataset.iloc[:,-1]
    
    # splitting up the data into training & validation datasets into 70% training & 30% validation
    # Xtrain & Ytrain for preparing models
    # Xtest & Ytest to use later for validation
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
    
    # return list of arrays or dataframes
    return data


if __name__ == '__main__':

    # set variables given in config.py
    splitsize   = cfg.splitsize
    chunksize   = cfg.chunksize
    n_Xpca      = cfg.n_PCA

    # set boolean variables based on argument passing
    time            = args.time
    save            = args.save
    load            = args.load
    model           = args.model
    model           = args.model
    remote          = args.remote
    export          = args.export
    verbose         = args.verbose
    superverbose    = args.superverbose
    flowsampling    = args.flowsampling
    packetsampling  = args.packetsampling
    if superverbose: verbose = True

    batch   = args.batch[0] # batch-size
    findex  = args.file[0] # file-index
    n       = args.n[0] # sampling-steps
    j       = args.j[0] # feature-vector

    if export:
        time = True
        print('>>> clear log-directory')
        for file in os.listdir(cfg.logs): # remove all files in the working directory logfolder
            Path.unlink(cfg.logs / file)


    # FILES, PATHS & COMMANDS
    wd = Path.cwd() # working directory

    # filenames
    csv_import  = '{}.csv'.format(cfg.filenames[findex])
    npy_Xtrain  = 'Xtrain_split_{}v{}.npy'
    npy_Xtest   = 'Xtest_split_{}v{}.npy'

    # directories
    log = 'logs_model-{}' # foldername to save logs

    # commands
    dstatcmd    = 'dstat --epoch --cpu-adv --disk --mem-adv --swap --output {} > /dev/null 2>&1 &'
    cplogs      = 'cp -r {} {}/'

    # placeholder pickle-model for 32/64bit systems, can also be used for remote/local
    #if remote:  modelpkl = '{}_model_remote.pkl'
    #else:       modelpkl = '{}_model_local.pkl'
    if remote:  modelpkl = cfg.model_remote
    else:       modelpkl = cfg.model_local

    # first set correct foldernames for preprocessing & classification logs
    if (model or save):
        if remote:  log = log.format('import_remote')
        else:       log = log.format('import_local')
    else: 
        if remote:  log = log.format('fit_remote')
        else:       log = log.format('fit_local')

    # set samplingmode and flags for further processing
    if flowsampling:
        flowsampling    = True
        packetsampling  = False
        samplefolder    = cfg.flowfolder
        m               = args.flowsampling[0]
    elif packetsampling:
        packetsampling  = True
        flowsampling    = False
        samplefolder    = cfg.packetfolder
        m               = args.packetsampling[0]

    # forge foldername to import CSV based on arguments
    foldername = '{}_mode{}_vector{}_steps{}'.format(cfg.filenames[findex],m,j,n)

    if flowsampling:
        foldername = '{}_perflowsampled'.format(foldername) # base folder to store results, models and & logs
        path = cfg.flowfolder / foldername / csv_import # sampled input CSV
        logs = cfg.flowfolder / foldername / log # full logfolder path to save results
        modeld = cfg.flowfolder / foldername / 'model' # full directory to export/import pickle model
    elif packetsampling:
        foldername = '{}_packetsampled'.format(foldername)
        path = cfg.packetfolder / foldername / csv_import
        logs = cfg.packetfolder / foldername / log
        modeld = cfg.packetfolder / foldername / 'model'

    # set full path to model file after all folder-paths are set up
    if (model or save): modelfile = modeld / modelpkl.format(cfg.filenames[findex])

    # create log & model folders if necessary
    if not os.path.exists(cfg.logs):    os.mkdir(cfg.logs)
    if not os.path.exists(modeld):      os.mkdir(modeld)

    if time: 
        if remote: os.system('killall python2')
        else: os.system('killall dstat')
        start = timer()
        t = epochtime.time()
        if export: # write timestamp to csv
            th.start() # start dstat loggin
            with open(cfg.time,'w') as timecsv: # create file
                csvwriter = csv.writer(timecsv, delimiter=",")
                csvwriter.writerow(['epochtime','scriptname','segment','status']) # labels
                csvwriter.writerow([t,'rpi-Preprocessing.py','main','start'])


    # OUTPUT passed optional arguments & filepath
    print('\n\n'+40*'~'+' SCRIPT: rpi-Preprocessing.py '+40*'~')
    print('\n'+20*'~'+' optional arguments '+20*'~')
    print('\n{}\t--verbose\n{}\t--superverbose\n{}\t--time\n{}\t--save\n{}\t--load\n{}\t--export\n{}\t--model\n{}\t--remote\n\n{}\t--flowsampling\n{}\t--packetsampling'.format(verbose,superverbose,time,save,load,export,model,remote,flowsampling,packetsampling))
    print('\n'+20*'~'+' processing '+20*'~')
    print('\nbatchsize = {}\nsplitsize = {}'.format(batch,splitsize))
    print('\n'+20*'~'+' paths & file '+20*'~'+'\n')
    print('FOLDER:\t{}\n\t{}\n\t{}\n'.format(cfg.logs,samplefolder,foldername))
    print('JSON:\t{}'.format(cfg.vectors[j]))
    if model or save: print('MODEL:\t{}'.format(modelpkl.format(cfg.filenames[findex])))
    print('CSV:\t{}'.format(csv_import))
    print('\n'+20*'~'+' commands '+20*'~')
    print('\ndstat: {}\n\n'.format(dstatcmd))


    # IMPORT CSV
    if time:
        t = epochtime.time()
        if export: # write timestamp to csv
            with open(cfg.time,'a') as timecsv:
                csvwriter = csv.writer(timecsv, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','import CSV','start'])

    print('>>> Importing CSV line-by-line, splitting into Xtrain & Xtest')
    # initialise empty dataframes
    dataset = pd.DataFrame()
    Xtrain  = pd.DataFrame()
    Xtest   = pd.DataFrame()
    Ytrain  = pd.Series(dtype=int)
    Ytest   = pd.Series(dtype=int)

    for chunk in read_csv(path,chunksize=10**5,usecols=None,skipinitialspace=True,encoding='utf-8'): # read csv in chunks
        chunk = conversion(chunk,False) # convert values into smaller datatypes
        cleanString(chunk,False,False) # remove string-features
        cleanNaN(chunk,0,False,False) # remove NaNs
        chunksplit = splitDataframe(chunk,0.30,False,False) # split into training & test portion on the fly:[Xtrain,Xtest,Ytrain,Ytest]

        # accumulate splits
        Xtrain  = Xtrain.append(chunksplit[0])
        Xtest   = Xtest.append(chunksplit[1])
        Ytrain  = Ytrain.append(chunksplit[2])
        Ytest   = Ytest.append(chunksplit[3])

    features = list(Xtrain) # used later to initialise empty np arrays via len(features)
    del chunksplit
    del chunk
    gc.collect()


    # SCALER FIT
    if time:
        t = epochtime.time()
        if export: # write timestamp to csv
            with open(cfg.time,'a') as timecsv:
                csvwriter = csv.writer(timecsv, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','fit scaler','start'])

    print('>>> StandardScaling partial fit to Xtrain')
    scaler = StandardScaler(copy=False)
    n = Xtrain.shape[0] # number of rows
    processed = 0
    while processed < n: # iterating until processed rows equals total rows of Xtrain
        toprocess = min(batch, n-processed) # number of rows to process in this iteration
        scaler.partial_fit(Xtrain[processed:processed+toprocess]) # partial_fit scaler on current slice
        processed += toprocess # increase number of already processed rows, used to determin when to leave the loop


    # SPLITTING DATA INTO SMALLER FILES
    if time:
        t = epochtime.time()
        if export: # write timestamp to csv
            with open(cfg.time,'a') as timecsv:
                csvwriter = csv.writer(timecsv, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','split files','start'])


    print('>>> Splitting data to reduce memory consumption') # split training data into smaller portions for transformation and save to disk to free up memory
    n = Xtrain.shape[0]
    toprocess = min(splitsize, n)
    iteration = int(n/splitsize)+1
    index = 0
    while toprocess > 0:
        index += 1
        print('\t[{}/{}] Xtrain'.format(index,iteration))
        npsave = cfg.tmp / npy_Xtrain.format(index,iteration)

        print('\t\t> Converting dtype')
        npXtrain = Xtrain[:][0:toprocess].to_numpy().astype(np.float32) # convert slice into np array
        Xtrain = Xtrain.drop(Xtrain.index[0:toprocess]) # drop processed slice from df

        print('\t\t> Saving')
        np.save(npsave,npXtrain)
        n -= toprocess # number of rows that need to be processed
        toprocess = min(splitsize, n)# get slice-size for next iteration
        if verbose: print('\n< {}\n{}\n{} {} {}MB\n'.format(npy_Xtrain.format(index,iteration),npXtrain,npXtrain.shape,npXtrain.dtype,int(npXtrain.nbytes/1024**2)))

    iXtrain = np.arange(1,index+1,1) # create array to restore splitted files afterwards
    del Xtrain
    del npXtrain
    gc.collect()

    n = Xtest.shape[0]
    toprocess = min(splitsize, n)
    iteration = int(n/splitsize)+1
    index = 0
    while toprocess > 0:
        index += 1
        print('\t[{}/{}] Xtest'.format(index,iteration))

        print('\t\t> Converting dtype')
        npXtest = Xtest[:][0:toprocess].to_numpy().astype(np.float32)
        Xtest = Xtest.drop(Xtest.index[0:toprocess])

        print('\t\t> Saving')
        npsave = cfg.tmp / npy_Xtest.format(index,iteration)
        np.save(npsave,npXtest)
        n -= toprocess
        toprocess = min(splitsize, n)
        if verbose: print('\n< {}\n{}\n{} {} {}MB\n'.format(npy_Xtest.format(index,iteration),npXtest,npXtest.shape,npXtest.dtype,int(npXtest.nbytes/1024**2)))
    iXtest = np.arange(1,index+1,1) # create array to restore splitted files later
    del Xtest
    del npXtest
    gc.collect()


    # SCALER TRANSFORM
    if time:
        t = epochtime.time()
        #print('\nrpi-Preprocessing.py\n\t<<< start: {}'.format(t))
        if export: # write timestamp to csv
            with open(cfg.time,'a') as timecsv:
                csvwriter = csv.writer(timecsv, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','scale Xtrain','start'])


    print('>>> StandardScaling')
    for index in iXtrain: # cycle through split-files and apply StandardScaler transform on the fly
        print('\t[{}/{}] Xtrain'.format(index,len(iXtrain)))
        Xtrain_scaled = np.empty(shape=[0,len(features)]) # initialise empty numpy array
        npload = cfg.tmp / npy_Xtrain.format(index,len(iXtrain)) # split-file to load in current iteration
        tmp = np.load(npload).astype(np.float32) # load split-file
        if verbose: print('\n< {}\n{}\n{} {} {}MB\n'.format(npy_Xtrain.format(index,len(iXtrain)),tmp,tmp.shape,tmp.dtype,int(tmp.nbytes/1024**2)))

        print('\t\t> Transforming')
        n = tmp.shape[0]
        size = min(batch, n)
        while size > 0:
            tmpscaled = scaler.transform(tmp[:][0:size],copy=None) # transform rows
            tmp = np.delete(tmp,np.s_[0:size:1],axis=0) # delete rows from array
            Xtrain_scaled = np.append(Xtrain_scaled,tmpscaled,axis=0).astype(np.float32)
            n -= size
            size = min(batch,n)
            if superverbose: print('\n{}\n{} {} {}MB'.format(Xtrain_scaled,Xtrain_scaled.shape,Xtrain_scaled.dtype,int(Xtrain_scaled.nbytes/1024**2)))
        if verbose: print('\n < {}\n{}\n{} {} {}MB\n'.format(npy_Xtrain.format(index,len(iXtrain)),Xtrain_scaled,Xtrain_scaled.shape,Xtrain_scaled.dtype,int(Xtrain_scaled.nbytes/1024**2)))
        del tmpscaled

        print('\t\t> Saving')
        npsave = cfg.tmp / npy_Xtrain.format(index,len(iXtrain))
        np.save(npsave,Xtrain_scaled)
        del Xtrain_scaled
    del tmp


    if time:
        t = epochtime.time()
        if export: # write timestamp to csv
            with open(cfg.time,'a') as timecsv:
                csvwriter = csv.writer(timecsv, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','scale Xtest','start'])

    for index in iXtest: # cycle through split-files and apply StandardScaler transform on the fly

        print('\t[{}/{}] Xtest'.format(index,len(iXtest)))
        Xtest_scaled = np.empty(shape=[0,len(features)]) # initialise empty numpy array
        npload = cfg.tmp / npy_Xtest.format(index,len(iXtest))
        tmp = np.load(npload).astype(np.float32) # load split-file
        if verbose: print('\n< {}\n{}\n{} {} {}MB\n'.format(npy_Xtest.format(index,len(iXtest)),tmp,tmp.shape,tmp.dtype,int(tmp.nbytes/1024**2)))

        print('\t\t> Transforming')
        n = tmp.shape[0]
        size = min(batch, n)
        while size > 0:
            tmpscaled = scaler.transform(tmp[:][0:size],copy=None) # transform rows
            tmp = np.delete(tmp,np.s_[0:size:1],axis=0) # delete rows from array
            Xtest_scaled = np.append(Xtest_scaled,tmpscaled,axis=0).astype(np.float32)
            n -= size
            size = min(batch,n)
            if superverbose: print('\n{}\n{} {} {}MB'.format(Xtest_scaled,Xtest_scaled.shape,Xtest_scaled.dtype,int(Xtest_scaled.nbytes/1024**2)))
        if verbose: print('\n < {}\n{}\n{} {} {}MB\n'.format(npy_Xtest.format(index,len(iXtest)),Xtest_scaled,Xtest_scaled.shape,Xtest_scaled.dtype,int(Xtest_scaled.nbytes/1024**2)))
        del tmpscaled

        print('\t\t> Saving')
        npsave = cfg.tmp / npy_Xtest.format(index,len(iXtest))
        np.save(npsave,Xtest_scaled)
        del Xtest_scaled
    del tmp


    # PCA
    if time:
        t = epochtime.time()
        if export: # write timestamp to csv
            with open(cfg.time,'a') as timecsv:
                csvwriter = csv.writer(timecsv, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','fit PCA','start'])

    print('>>> Applying PCA fit')
    Xpca = []
    ipca = IncrementalPCA(n_components = n_Xpca, batch_size = 10**5)

    for index in iXtrain: # partial fit PCA to Xtrain, iterating over split-files
        print('\t[{}/{}] Xtrain'.format(index,len(iXtrain)))
        npload = cfg.tmp / npy_Xtrain.format(index,len(iXtrain))
        split = np.load(npload).astype(np.float32)

        print('\t\t> Fitting')
        ipca.partial_fit(split)
    del split


    if (not model): # PCA transform Xtrain (only necessary to fit model)
        print('>>> Applying PCA transform')
        Xtrain = np.empty(shape=[0,n_Xpca]) # initialise empty numpy array
        for index in iXtrain:
            print('\t[{}/{}] Xtrain'.format(index,len(iXtrain)))
            npload = cfg.tmp / npy_Xtrain.format(index,len(iXtrain))
            split = np.load(npload).astype(np.float32)
            if verbose: print('\n< {}\n{}\n{} {} {}MB\n'.format(npy_Xtrain.format(index,len(iXtrain)),split,split.shape,split.dtype,int(split.nbytes/1024**2)))

            print('\t\t> Transforming')
            split = ipca.transform(split)
            if verbose: print('\n < {}\n{}\n{} {} {}MB\n'.format(npy_Xtrain.format(index,len(iXtrain)),split,split.shape,split.dtype,int(split.nbytes/1024**2)))

            print('\t\t> Saving')
            Xtrain = np.append(Xtrain,split,axis=0).astype(np.float32) # append splits to single Xtrain np.array
        if verbose: print('\n< Xtrain (PCA):\n{}\n{} {} {}MB\n'.format(Xtrain,Xtrain.shape,Xtrain.dtype,int(Xtrain.nbytes/1024**2)))
        del split

    if time:
        t = epochtime.time()
        if export: # write timestamp to csv
            with open(cfg.time,'a') as timecsv:
                csvwriter = csv.writer(timecsv, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','PCA Xtest','start'])

    # Xtest
    Xtest = np.empty(shape=[0,n_Xpca]) # initialise empty numpy array
    if model: print('>>> Applying PCA transform')
    for index in iXtest:
        print('\t[{}/{}] Xtest'.format(index,len(iXtest)))
        npload = cfg.tmp / npy_Xtest.format(index,len(iXtest))
        split = np.load(npload).astype(np.float32)
        if verbose: print('\n< {}\n{}\n{} {} {}MB\n'.format(npy_Xtest.format(index,len(iXtest)),split,split.shape,split.dtype,int(split.nbytes/1024**2)))

        print('\t\t> Transforming')
        split = ipca.transform(split)
        if verbose: print('\n < {}\n{}\n{} {} {}MB\n'.format(npy_Xtest.format(index,len(iXtest)),split,split.shape,split.dtype,int(split.nbytes/1024**2)))

        print('\t\t> Saving')
        Xtest = np.append(Xtest,split,axis=0).astype(np.float32)
    if verbose: print('\n< Xtest (PCA):\n{}\n{} {} {}MB\n'.format(Xtest,Xtest.shape,Xtest.dtype,int(Xtest.nbytes/1024**2)))
    del split


    # RANDOM FOREST CLASSIFIER

    # select already fitted modelfile or fit model
    if model:
        if time:
            t = epochtime.time()
            if export: # write timestamp to csv
                with open(cfg.time,'a') as timecsv:
                    csvwriter = csv.writer(timecsv, delimiter=",")
                    csvwriter.writerow([t,'rpi-Preprocessing.py','import model','start'])

        print('>>> Importing model')
        model = joblib.load(modelfile)

    else:
        if time:
            t = epochtime.time()
            if export: # write timestamp to csv
                with open(cfg.time,'a') as timecsv:
                    csvwriter = csv.writer(timecsv, delimiter=",")
                    csvwriter.writerow([t,'rpi-Preprocessing.py','fit model','start'])

        print('>>> Fitting RandomForestClassifier')
        model = RandomForestClassifier()
        model = model.fit(Xtrain,Ytrain)
        del Xtrain

        if save:
            print('>>> saving model {}'.format(modelfile))
            joblib.dump(model,str(modelfile),compress=True)

    if time:
        t = epochtime.time()
        if export: # write timestamp to csv
            with open(cfg.time,'a') as timecsv:
                csvwriter = csv.writer(timecsv, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','predictions','start'])

    print('>>> Creating predictions')
    predictions = model.predict(Xtest)

    print('>>> Creating confusion-matrix')
    matrix = confusion_matrix(Ytest,predictions)

    print('>>> Creating classification-report')
    report = pd.DataFrame(classification_report(Ytest,predictions,digits=5,output_dict=True)).transpose()

    print('>>> Saving parameters, accuracy-score and feature-importance')
    parameters = model.get_params(deep=True)
    accuracyscore = accuracy_score(Ytest,predictions)
    featureimportance = model.feature_importances_


    # output final results
    print('\n\n'+10*'~'+' {}: results '.format(model)+10*'~')
    print('\nModel-Parameters:\n{}'.format(parameters))
    print('\n\nAccuracy-Score: %.5f' % (accuracyscore))
    print('\n\nFeature-Importance:\n{}'.format(featureimportance))
    print('\n\nConfusion-Matrix:\n')
    print('t       p r e d i c t')
    print('r         "0"    "1"')
    print('u  "0":',matrix[0])
    print('e  "1":',matrix[1])
    print('\n\nClassification-Report:\n\n',report)
    

    if export:
        print('\n>>> Exporting results to folder: {}'.format(cfg.logs))
        evaluation = {'model':[model],'parameters':[parameters],'accuracy-score':[accuracyscore],'feature-importance':[featureimportance],'confusion-matrix':[matrix],'PCA-components':[n_Xpca]}
        results = pd.DataFrame.from_dict(evaluation,orient='index',columns=['summary'])
        results.to_csv(cfg.result) # save results
        report.to_csv(cfg.report) # save classification-report

    if time:
        end = timer()
        t = epochtime.time()
        print('\n(runtime: %.3f' % (end-start),'seconds)\n')
        if export: # write timestamps to csv
            with open(cfg.time,'a') as timecsv:
                csvwriter = csv.writer(timecsv, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','main','end'])


    # STOP MONITORING
    if export:
        wait = 50 # seconds to wait before killing dstat
        if remote: # different method to kill dstat on a Raspberry Pi, running dietPi compared to killing the process on Ubuntu
            pids = os.popen('pidof /usr/bin/python2 /usr/bin/dstat').read() # get pids as string, containing pid from dstat process and the pid of the running script
            pids = [int(s) for s in pids.split(' ')] # convert strings to list
        else:
            pids = os.popen('pidof /usr/bin/python3 /usr/bin/dstat').read() # get pids as string, containing pid from dstat process and the pid of the running script
            pids = [int(s) for s in pids.split(' ')] # convert strings to list
            mypid = os.getpid() # pid of running script
            pids.remove(mypid)

        for i in progressBar(range(wait),'>>> Waiting for dstat (pid={}): '.format(pids[0]), wait):
            epochtime.sleep(1)

        print('>>> Killing dstat')
        os.kill(pids[0],9) # kill running dstat process (kills running script, has to be done that way since dstat is running in background)

        print('>>> Saving logs to folder {}'.format(logs))
        if not os.path.exists(logs): os.mkdir(logs) # create logfolder if necessary
        for root, dirs, files in os.walk(cfg.logs):
            for filename in files: # iterate over filenames found within the wd logfolder
                log = cfg.logs / filename # full path for current logfile
                print('\t> Saving {}'.format(filename))
                os.system(cplogs.format(log,logs))
        print(20*'#')

    exit()