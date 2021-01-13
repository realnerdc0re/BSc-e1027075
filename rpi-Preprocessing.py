#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 10 10:32:48 2021

@author: pjr
"""

from pandas import read_csv
#from pandas.plotting import scatter_matrix
#from matplotlib import pyplot
#from scipy.stats import zscore
from sklearn.model_selection import train_test_split
#from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
#from sklearn.impute import SimpleImputer as Imputer
#from sklearn.model_selection import cross_val_score
#from sklearn.model_selection import StratifiedKFold
#from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier
from timeit import default_timer as timer



import time as epochtime
import numpy as np
import pandas as pd
import psutil
import sys
import csv
import os
import gc

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
parser.add_argument('chunk', metavar='chunk', type=int,nargs=1,help='choose numerical value as chunksize for CSV import')
parser.add_argument('batch', metavar='batch', type=int,nargs=1,help='choose numerical value for batchsize for StandardScaler')

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

# PRE-PROCESSING
# convert to lower datatypes
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
        if (not time): input('...')

    dicttype = {} # store index numbers and target-datatypes

    if verbose: print('>>> searching for 64bit numerical values...')
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

    if verbose: print('>>> converting values...')
    dataset = dataset.astype(dicttype,copy=False)

    types = dataset.dtypes
    if verbose:
        print('\n'+20*'~'+' converted '+20*'~')
        print('\n{}\n'.format(types))
        if (not time): input('...')

    if verbose: printdata(dataset,'after-conversion',True)

    if time: 
        end = timer()
        if verbose: print('\nconversion\n[TIME]: %.3f' % (end-start),'seconds')

    return dataset
# clean given df from any infinite values by replacement
def cleanInf(dataset,mode,verbose=False,time=False):

    if time: start = timer()

    modename = {0: 'value', 1: 'mean', 2: 'min', 3: 'max', 4: 'std'}

    # informational output
    if verbose:
        print('\n\n'+40*'~'+' FUNCTION: cleanInf '+40*'~')
        print('\n>>> searching Infs...')

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
            if (not time): input('\n...')

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
        if (not time): input('\n...')

    if time: 
        end = timer()
        print('\ncleanInf\n[TIME]: %.3f' % (end-start),'seconds')

    # return whatever needed for method to clean specific cells or drop features    
    return
def cleanNaN(dataset,replacement,verbose=False,time=False):

    if time: start = timer()

    # informational output
    if verbose:
        print('\n\n'+40*'~'+' FUNCTION: cleanNaN '+40*'~')
        print('\n>>> searching NaNs...')

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
        print('\n>>> searching strings...')

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
        if (not time): input('\n...')

    if time: print('\ncleanString\n[TIME]: %.3f' % (end-start),'seconds')

    return
# remove single-value-features from given df, since these contain no informations
def cleanSingleValue(dataset,verbose=False,time=False):

    if time: start = timer()

    # informational output
    if verbose:
        print('\n\n'+40*'~'+' FUNCTION: cleanSingleValue '+40*'~')
        print('\n>>> searching unique-value features...')

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
        print('\n>>> replace cells content with {}...'.format(content))

    # replace given cells with given content
    for j in cells:
        dataset.at[j,feature] = content

    if time: 
        end = timer()
        print('\nwriteCells\n[TIME]: %.3f' % (end-start),'seconds')

    return

# CLASSIFICATION
# split given df into training & test portions
def splitDataframe(dataset,testsize,verbose=False,time=False):
    
    if time: start = timer()
    
    # informational output
    if verbose:
        print('\n\n'+40*'~'+' FUNCTION: splitDataframe '+40*'~')
        print('\n>>> splitting dataframe into training & test portion...')
    
    
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
        if (not time): input('\n...')
        print('\n'+10*'~'+' X '+10*'~')
        print('\n{}'.format(X))
        print('\n'+10*'~'+' Y '+10*'~')
        print('\n{}'.format(Y))
        if (not time): input('\n...')
        
        print('\n'+10*'~'+' Xtrain '+10*'~')
        print('\n{}'.format(Xtrain))
        print('\n'+10*'~'+' Ytrain '+10*'~')
        print('\n{}'.format(Ytrain))
        if (not time): input('\n...')
    
        print('\n'+10*'~'+' Xtest '+10*'~')
        print('\n{}'.format(Xtest))
        print('\n'+10*'~'+' Ytest '+10*'~')
        print('\n{}'.format(Ytest))
        if (not time): input('\n...')
        
    if time: print('\nsplitFrame\n[TIME]: %.3f' % (end-start),'seconds')
    
    # return list of arrays or dataframes
    return data
# Standard (z-Score) Scaler (proportional scaling) using dataframe
def scalingDataframe(datasets,features,verbose=False,time=False):
    
    if time: start = timer()

    #scaler = MinMaxScaler()
    scaler = StandardScaler()
    tmpscaled = []

    # informational output
    if verbose:
        print('\n\n'+40*'~'+' FUNCTION: scalingDataframe: {} '.format(scaler)+40*'~')
        print('\n>>> scaling values...')

    # get all features if no features are given as argument
    if not features: features = list(datasets[0])

    # TRAINING
    # fit & transform Xtrain
    tmp = datasets[0]
    if verbose: print('>>> fit & transform Xtrain...')
    tmp[features] = scaler.fit_transform(tmp[features])
    tmpscaled.append(tmp)

    # TEST (transform)
    # transform Xtest
    tmp = datasets[1]
    if verbose: print('>>> transform Xtest...')
    tmp[features] = scaler.transform(tmp[features])
    tmpscaled.append(tmp)

    if time: end = timer()

    if verbose:
        print('\n'+10*'~'+' Xtrain, original '+10*'~')
        print('\n{}'.format(datasplit[0]))
        print('\n'+10*'~'+' Xtest, original '+10*'~')
        print('\n{}'.format(datasplit[1]))
        if (not time): input('\n...')
        
        print('\n'+10*'~'+' Xtrain, fit & transformed '+10*'~')
        print('\n{}'.format(tmpscaled[0]))
        print('\n'+10*'~'+' Xtest, fit & transformed '+10*'~')
        print('\n{}'.format(tmpscaled[1]))
        if (not time): input('\n...')

    if time: print('\nscalingDataframe\n[TIME]: %.3f' % (end-start),'seconds')

    return tmpscaled
# apply PCA on scaled data
def PCAnalysis(dataset,components,verbose=False,time=False):
    
    if time: start = timer()
    
    # informational output
    print('\n\n'+40*'~'+' FUNCTION: PCAnalysis '+40*'~')
    print('\n>>> apply principal component analysis...')
    
    Xpca = []
    
    pca = PCA(n_components=components)
    
    # fit to Xtrain (generating learning model parameters from Xtrain)   
    pca.fit(dataset[0])
    # transform Xtrain & Xtest (applying generated model on Xtrain and Xtest)
    for i in range(0,2):
        tmp = pca.transform(dataset[i])
        Xpca.append(tmp)
    
    if time: end = timer()
    
    if verbose:
        print('\n\n'+10*'~'+' Xtrain, fit & transform '+10*'~')
        print('\n{}'.format(Xpca[0]))
        print('\n{}'.format(Xpca[0].shape))

        print('\n\n'+10*'~'+' Xtest, fit & transform '+10*'~')
        print('\n{}'.format(Xpca[1]))
        print('\n{}'.format(Xpca[1].shape))

        print('\n\n'+10*'~'+' PCA, explained variance '+10*'~')
        print('\n{}'.format(pca.explained_variance_ratio_))
        if (not time): input('\n...\n')
    
    if time: print('\nPCAnalysis\n[TIME]: %.3f' % (end-start),'seconds')
    
    return Xpca
# make predicitons
def makePredictions(model,Xtest,Ytest,export):

    if time: start = timer()
    print('\n\n'+40*'~'+' FUNCTION: makePredictions '+40*'~') # informational output

    # make predictions for the validation data Xtest, create reports based on predictions and the GT-table Ytest
    print('>>> make predictions...')
    predictions = model.predict(Xtest)
    print('>>> create confusion-matrix...')
    matrix = confusion_matrix(Ytest,predictions)
    # saving the classification-report directly into pandas dataframe to enable easy export to csv if necessary
    print('>>> create classification-report...')
    report = pd.DataFrame(classification_report(Ytest,predictions,digits=5,output_dict=True)).transpose()

    # save results
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

    '''
    # output to compare different results???
    print(Xtest)
    print(pd.DataFrame(Xtest).describe())
    print(predictions)
    '''

    if export:
        print('\n>>> exporting results to folder: {}'.format(logfolder))
        # list of all informations we want to save for later evaluation
        evaluation = {'model':[model],'parameters':[parameters],'accuracy-score':[accuracyscore],'feature-importance':[featureimportance],'confusion-matrix':[matrix]}
        results = pd.DataFrame.from_dict(evaluation,orient='index',columns=['summary'])
        # save results
        results.to_csv(resultscsv)
        report.to_csv(reportcsv)

    if time: 
        end = timer()
        print('\nmakePredictions\n[TIME]: %.3f' % (end-start),'seconds')

    return



if __name__ == '__main__':

    pid = os.getpid()
    memoryUse = int(psutil.Process(pid).memory_info()[0]/1000**2)
    print('\nmem-usage at start: {}MB\n'.format(int(memoryUse)))

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

    rpi = args.rpi
    windows = args.windows
    osx = args.osx
    linux = args.linux
    findex = args.file[0]

    chunksize = args.chunk[0]
    batchsize = args.batch[0]
    if chunksize == 0: chunksize = None

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
        #chunksize = None
    elif rpi:
        fpath = r"/home/dietpi/BSc-e1027075/csv/flow-sampled"
        ppath = r"/home/dietpi/BSc-e1027075/csv/packet-sampled"
        #chunksize = 10**3
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
    print('\n\n'+40*'~'+' SCRIPT: rpi-Preprocessing.py '+40*'~')
    print('\n'+20*'~'+' optional arguments '+20*'~')
    print("\n{}\t--verbose\n{}\t--superverbose\n{}\t--time\n{}\t--flowsampling\n{}\t--packetsampling".format(verbose,superverbose,time,flowsampling,packetsampling))
    print('\n\n{}\n'.format(path))
    if (not time): input('\n...')

    #chunksize = 10**6
    dropfeature = []
    dropfeature.append('flowStartMilliseconds')
    #dropfeature.append('')

    memoryUse = int(psutil.Process(pid).memory_info()[0]/1000**2)
    print('\nmem-usage before importing CSV: {}MB\n'.format(int(memoryUse)))

    # IMPORT depending on chosen chunksize
    if chunksize == None:
        dataset = importCSV(path,None,verbose,chunksize)
        # CLEANING
        removeFeatures(dataset,dropfeature,verbose,time)
        cleanString(dataset,verbose,time)
        cleanNaN(dataset,0,verbose,time)
    else:
        dataset = pd.DataFrame()

        # 
        Xtrain = pd.DataFrame()
        Xtest = pd.DataFrame()
        Ytrain = pd.Series(dtype=int)
        Ytest = pd.Series(dtype=int)

        scaler = StandardScaler(copy=False)

        data = []
        print('>>> importing & pre-processing CSV (chunksize={})...'.format(chunksize))
        # read csv in chunks
        for chunk in read_csv(path,chunksize=10**5,usecols=None,skipinitialspace=True,encoding='utf-8'):

            removeFeatures(chunk,dropfeature,False,False) # should be done after labeling (flowStartMilliseconds)

            chunk = conversion(chunk,False) # convert content into smaller datatypes

            # CLEANING
            cleanString(chunk,False,False)
            cleanNaN(chunk,0,False,False)

            # SPLITTING
            chunksplit = splitDataframe(chunk,0.30,False,False) # [Xtrain,Xtest,Ytrain,Ytest]
            # accumulate chunk-splits
            Xtrain = Xtrain.append(chunksplit[0])
            Xtest = Xtest.append(chunksplit[1])
            Ytrain = Ytrain.append(chunksplit[2])
            Ytest = Ytest.append(chunksplit[3])

        del chunksplit
        del chunk

    gc.collect()
    memoryUse = int(psutil.Process(pid).memory_info()[0]/1000**2)
    print('\nmem-usage after importing CSV: {}MB\n'.format(int(memoryUse)))


    #print('{}'.format(type(chunksplit[0])))

    #Xtrain = conversion(Xtrain,True)
    #print('Xtrain:\n{}\n'.format(type(Xtrain)))
    #printdata(Xtrain,True,False)

    #print('Ytrain:\n{}\n'.format(type(Ytrain)))
    #print(Ytrain)
    #Ytrain = Ytrain.to_numpy().astype(np.int8)
    #print('Ytrain:\n{}\n'.format(type(Ytrain)))
    #print(Ytrain)



    '''
    print('Xtrain:\n{}\n'.format(Xtrain))
    input('...')

    Xtrain = Xtrain.to_numpy().astype(np.float32)
    Xtest = Xtest.to_numpy()
    Ytrain = Ytrain.to_numpy()
    Ytest = Ytest.to_numpy()

    print('Xtrain:\n{}\n{} {} {}MB\n'.format(Xtrain,Xtrain.shape,Xtrain.dtype,int(Xtrain.nbytes/1024**2)))
    input('...')
    '''



    # memory logging, debug output
    Xtrain_size_df = int(Xtrain.memory_usage().sum()/1024**2)
    Xtest_size_df = int(Xtest.memory_usage().sum()/1024**2)
    Ytrain_size_df = (Ytrain.nbytes/1024**2)
    Ytest_size_df = (Ytest.nbytes/1024**2)
    total_size_df = int(Xtrain_size_df+Xtest_size_df+Ytrain_size_df+Ytest_size_df)
    print('\nmem-usage: Xtrain={}MB, Xtest={}MB, Ytrain={}MB, Ytest={}MB, Total={}MB'.format(Xtrain_size_df,Xtest_size_df,Ytrain_size_df,Ytest_size_df,total_size_df))
    #Xtrain.info(memory_usage="deep")
    #Xtest.info(memory_usage="deep")


    # SCALING
    features = list(Xtrain)
    #print('\n{}\n'.format(features))

    # applying scaler fit in batches, to not run into SWAP
    n = Xtrain.shape[0] # number of rows
    index = 0
    print('>>> partial fit StandardScaler (batchsize={})...'.format(batchsize))
    while index < n:
        size = min(batchsize, n-index) # for last iteration
        Xtrain_partial = Xtrain[index:index+size] # get batches from original data
        scaler.partial_fit(Xtrain_partial) # partial fit to batch
        index += size

    del Xtrain_partial

    gc.collect()
    memoryUse = int(psutil.Process(pid).memory_info()[0]/1024**2)
    print('\nmem-usage after partial fit: {}MB\n'.format(int(memoryUse)))


    Xtrain_scaled = np.empty(shape=[0,len(features)])
    Xtest_scaled = np.empty(shape=[0,len(features)])


    '''
    # create empty dataframe
    n = Xtest.shape[0] # number of rows
    tmpscaled=pd.DataFrame(index=np.arange(n),columns=features)

    splitindex = list(Xtest.index.values) # get exact copy of the row-index from Xtest
    tmp = pd.DataFrame(index=splitindex,columns=features) # create empty copy of Xtest
    print(tmp)
    '''


    Xtest_size_df = int(Xtest.memory_usage().sum()/1024**2)
    # scale Xtest in batches
    print('>>> transform Xtest in batches (batchsize={})...'.format(batchsize))
    n = Xtest.shape[0]
    size = min(batchsize, n)
    while size > 0:
        #tmp = scaler.transform(Xtest[features][index:index+size],copy=None)
        tmp = scaler.transform(Xtest[features][0:size],copy=None)
        Xtest = Xtest.drop(Xtest.index[0:size]) # immediately drop current batch from Xtest
        Xtest_scaled = np.append(Xtest_scaled,tmp,axis=0).astype(np.float32) # append, and convert to float32 on-the-fly

        # memory logging, debug output
        Xtest_size = int(Xtest.memory_usage().sum()/1024**2)
        Xtest_scaled_size = int(Xtest_scaled.nbytes/1024**2)
        memoryUse = int(psutil.Process(pid).memory_info()[0]/1024**2)
        print('{}MB:\t{}MB\t/\t{}MB\t/\t\u0394 {}MB'.format(memoryUse,Xtest_size,Xtest_scaled_size,(Xtest_size+Xtest_scaled_size)-Xtest_size_df))

        # get conditions for next loop-iteration check
        n -= size
        size = min(batchsize, n)
        #gc.collect()

    del Xtest # delete dataframe after scaling is done

    gc.collect()
    memoryUse = int(psutil.Process(pid).memory_info()[0]/1024**2)
    print('\nmem-usage after Xtest fit: {}MB\n'.format(int(memoryUse)))






    Xtrain_size_df = int(Xtrain.memory_usage().sum()/1024**2)

    # scale Xtrain in batches
    print('>>> transform Xtrain in batches (batchsize={}, size={}MB)...'.format(batchsize,Xtrain_size_df))
    n = Xtrain.shape[0]
    size = min(batchsize, n)
    while size > 0:
        #tmp = scaler.transform(Xtest[features][index:index+size],copy=None)
        tmp = scaler.transform(Xtrain[features][0:size],copy=None)
        #Xtrain = Xtrain.drop(index=Xtrain.index[0:size]) # immediately drop current batch from Xtest
        Xtrain.drop(index=Xtrain.index[0:size],inplace=True) # immediately drop current batch from Xtest
        Xtrain_scaled = np.append(Xtrain_scaled,tmp,axis=0).astype(np.float32) # append, and convert to float32 on-the-fly

        # memory logging, debug output
        Xtrain_size = int(Xtrain.memory_usage().sum()/1024**2)
        Xtrain_scaled_size = int(Xtrain_scaled.nbytes/1024**2)
        memoryUse = int(psutil.Process(pid).memory_info()[0]/1024**2)
        print('{}MB:\t{}MB\t/\t{}MB\t/\t\u0394 {}MB'.format(memoryUse,Xtrain_size,Xtrain_scaled_size,(Xtrain_size+Xtrain_scaled_size)-Xtrain_size_df))

        # get conditions for next loop-iteration check
        n -= size
        size = min(batchsize, n)
        #gc.collect()

    del Xtrain # delete dataframe after scaling is done

    gc.collect()
    memoryUse = int(psutil.Process(pid).memory_info()[0]/1024**2)
    print('\nmem-usage after Xtrain fit: {}MB\n'.format(int(memoryUse)))






    print('\nXtrain_scaled:\n\n{}\n\n{}, {}, {}MB\n'.format(Xtrain_scaled,Xtrain_scaled.shape,Xtrain_scaled.dtype,int(Xtrain_scaled.nbytes/1024**2)))
    if not time: input('...')
    print('\nXtest_scaled:\n\n{}\n\n{}, {}, {}MB\n'.format(Xtest_scaled,Xtest_scaled.shape,Xtest_scaled.dtype,int(Xtest_scaled.nbytes/1024**2)))
    if not time: input('...')

    #Xtest = tmpscaled



    # PCA


    # MODEL & PREDICTION





    # check processed data
    #verbose = False
    #printdata(dataset,'original',True)
    #input('...')
    #print('\n'+10*'~'+' Xtrain '+10*'~')
    #print('\n{}\n{}\n'.format(Xtrain,Xtrain.describe()))
    #types = Xtrain.dtypes
    #print('\n'+10*'~'+' Xtrain: scaled '+10*'~')
    #print('\n{}\n{}\n'.format(Xtrain,types))
    #input('...')
    #print('\n'+10*'~'+' Ytrain '+10*'~')
    #print('\n{}\n'.format(Ytrain))
    #input('...')

    #print('\n'+10*'~'+' Ytest '+10*'~')
    #print('\n{}\n'.format(Ytest))
    #input('...')





    #datascaled = scalingDataframe(datasplit,[],verbose,time)

    #n=4
    #Xpca = PCAnalysis(datascaled,n,verbose,time)

    #Xtrain = Xpca[0]
    #Xtest = Xpca[1]
    #Ytrain = datasplit[2]
    #Ytest = datasplit[3]

    '''
    model = RandomForestClassifier()
    print('>>> fitting model with {}...'.format(model))
    model = model.fit(Xtrain,Ytrain)
    makePredictions(model,Xtest,Ytest,False)
    '''

    if time:
        end = timer()
        t = epochtime.time()
        print('\nPreprocessing.py\n[EPOCH, end]: {}'.format(t))
        print('[RUNTIME]: %.3f' % (end-start),'seconds')

        if export: # write timestamps to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'Preprocessing.py','end'])

    exit()