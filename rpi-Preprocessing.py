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
from sklearn.decomposition import IncrementalPCA
#from sklearn.impute import SimpleImputer as Imputer
#from sklearn.model_selection import cross_val_score
#from sklearn.model_selection import StratifiedKFold
#from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier
from timeit import default_timer as timer
from pathlib import Path, PureWindowsPath

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


# FILES & PATHS
# capture files, https://www.unb.ca/cic/datasets/ids-2017.html
filenames = {0:'Merged',1:'Monday-WorkingHours',2:'Tuesday-WorkingHours',3:'Wednesday-WorkingHours',4:'Thursday-WorkingHours',5:'Friday-WorkingHours'}
# filenames of sampled, unlabeled CSVs
csvname = ["Merged.csv","Monday-WorkingHours.csv","Tuesday-WorkingHours.csv","Wednesday-WorkingHours.csv","Thursday-WorkingHours.csv","Friday-WorkingHours.csv"]
# working directory
wd = Path.cwd()
# logs
logd = wd / 'logs'
reportcsv = logd / 'report.csv'
resultcsv = logd / 'result.csv'
timecsv = logd / 'time.csv'
dstatcsv = logd / 'dstat.csv'
# sampled CSVs
fpath = wd / 'csv' / 'flow-sampled'
ppath = wd / 'csv' / 'packet-sampled'
# directory & files to save tmp np.array splits
npsaved = wd / 'tmp'
Xtrainnpy = 'Xtrain_split_{}v{}.npy'
Xtestnpy =  'Xtest_split_{}v{}.npy'
# models
fmodeld = fpath / 'fitted'
pmodeld = ppath / 'fitted'
#modelpkl = '{}_model_{}.pkl' # placeholder for file and 32/64bit
#modelpkl = '{}_model_32bit.pkl'
modelpkl = '{}_model_64bit.pkl'


# COMMANDS
# start dstat resource logging
dstat = 'dstat --epoch --cpu-adv --disk --mem-adv --output {} > /dev/null 2>&1 &'


# ARGUMENT PARSING
# command line argument passthrough for better usability
import argparse
parser = argparse.ArgumentParser(description='script for preprocessing labeled CSVs')
# positional arguments
parser.add_argument('file', metavar='file', type=int,nargs=1,help='select file to process: {}'.format(filenames))
parser.add_argument('batch', metavar='batch', type=int,nargs=1,help='choose numerical value for StandardScaler batchsize')
# optional arguments
parser.add_argument('-v','--verbose', action='store_true', help='output additional informations')
parser.add_argument('--superverbose', action='store_true', help='output additional informations')
parser.add_argument('-t','--time', action='store_true', help='measure runtimes & resource usage')
parser.add_argument('-e','--export', action='store_true', help='export timestamps & resource logs')
parser.add_argument('-m','--model', action='store_true', help='import model')
parser.add_argument('-s','--save', action='store_true', help='save model')
parser.add_argument('-l','--load', action='store_true', help='load preprocessed CSV')
# force sampling choice
samplegroup = parser.add_mutually_exclusive_group(required=True)
samplegroup.add_argument('-f','--flowsampling', action='store_true', help='use flow-sampled CSV files')
samplegroup.add_argument('-p','--packetsampling', action='store_true', help='use per-packet sampled CSV files')
args = parser.parse_args()



# starting dstat logging threaded
def threadFunc():
    os.system(dstat.format(dstatcsv))
    #proc = subprocess.Popen(["/usr/bin/dstat","--epoch","--cpu-adv","--output /home/noooberino/control.csv"],stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT,shell=True)
    #log = open('/home/noooberino/control.csv','a')
    #proc = subprocess.Popen(["/usr/bin/dstat","--epoch","--cpu-adv"],stdout=log,shell=True)
th = threading.Thread(target=threadFunc)

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
# clean given df from any infinite values by replacement
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
# remove single-value-features from given df, since these contain no informations
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

# CLASSIFICATION
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
# Standard (z-Score) Scaler (proportional scaling) using dataframe
def scalingDataframe(datasets,features,verbose=False,time=False):
    
    if time: start = timer()

    #scaler = MinMaxScaler()
    scaler = StandardScaler()
    tmpscaled = []

    # informational output
    if verbose:
        print('\n\n'+40*'~'+' FUNCTION: scalingDataframe: {} '.format(scaler)+40*'~')
        print('\n>>> scaling values')

    # get all features if no features are given as argument
    if not features: features = list(datasets[0])

    # TRAINING
    # fit & transform Xtrain
    tmp = datasets[0]
    if verbose: print('>>> fit & transform Xtrain')
    tmp[features] = scaler.fit_transform(tmp[features])
    tmpscaled.append(tmp)

    # TEST (transform)
    # transform Xtest
    tmp = datasets[1]
    if verbose: print('>>> transform Xtest')
    tmp[features] = scaler.transform(tmp[features])
    tmpscaled.append(tmp)

    if time: end = timer()

    if verbose:
        print('\n'+10*'~'+' Xtrain, original '+10*'~')
        print('\n{}'.format(datasplit[0]))
        print('\n'+10*'~'+' Xtest, original '+10*'~')
        print('\n{}'.format(datasplit[1]))
        if (not time): input('\n')
        
        print('\n'+10*'~'+' Xtrain, fit & transformed '+10*'~')
        print('\n{}'.format(tmpscaled[0]))
        print('\n'+10*'~'+' Xtest, fit & transformed '+10*'~')
        print('\n{}'.format(tmpscaled[1]))
        if (not time): input('\n')

    if time: print('\nscalingDataframe\n[TIME]: %.3f' % (end-start),'seconds')

    return tmpscaled
# apply PCA on scaled data
def PCAnalysis(dataset,components,verbose=False,time=False):
    
    if time: start = timer()
    
    # informational output
    print('\n\n'+40*'~'+' FUNCTION: PCAnalysis '+40*'~')
    print('\n>>> apply principal component analysis')
    
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
        if (not time): input('\n\n')
    
    if time: print('\nPCAnalysis\n[TIME]: %.3f' % (end-start),'seconds')
    
    return Xpca
# make predicitons
def makePredictions(model,Xtest,Ytest,export):

    if time: start = timer()
    print('\n\n'+40*'~'+' FUNCTION: makePredictions '+40*'~') # informational output

    # make predictions for the validation data Xtest, create reports based on predictions and the GT-table Ytest
    print('>>> make predictions')
    predictions = model.predict(Xtest)
    print('>>> create confusion-matrix')
    matrix = confusion_matrix(Ytest,predictions)
    # saving the classification-report directly into pandas dataframe to enable easy export to csv if necessary
    print('>>> create classification-report')
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

    # to not exceed rpi RAM size, split files into 500k rows per file
    splitsize = 5*10**5
    # read CSV line-by-line
    chunksize = 1
    # number of components for PCA
    n_Xpca = 4

    # optional arguments
    verbose = args.verbose
    superverbose = args.superverbose
    if superverbose: verbose = True
    flowsampling = args.flowsampling
    packetsampling = args.packetsampling
    time = args.time
    save = args.save
    load = args.load
    model = args.model
    export = args.export

    model = args.model
    # positional arguments
    findex = args.file[0]
    batchsize = args.batch[0]

    # set paths for CSV and model, based on sampling-choice
    if flowsampling: 
        path = fpath / csvname[findex] # sampled CSV
        modeld = fmodeld # pickel model-file
    elif packetsampling: 
        path = ppath / csvname[findex]
        modeld = pmodeld

    # set filepath for pickle modelfile if necessary
    if (model or save): modelfile = modeld / modelpkl.format(filenames[findex])

    if export: # remove any exisiting CSV
        for file in os.listdir(logd):
            Path.unlink(logd / file)

    if time: 
        os.system('killall dstat') # kill any running dstat process
        start = timer() # runtime
        t = epochtime.time() # epochtime
        th.start() # start dstat loggin
        #print('\nrpi-Preprocessing.py\n\t<<< start: {}'.format(t))

        if export: # write timestamp to csv
            if flowsampling: description = 'flow-sampled'
            elif packetsampling: description = 'packet-sampled'

            if os.path.isfile(timecsv): # check if file already exists
                with open(timecsv,'a') as csvfile:
                    csvwriter = csv.writer(csvfile, delimiter=",")
                    csvwriter.writerow(['epochtime','scriptname','segment','status']) # labels
                    csvwriter.writerow([t,'rpi-Preprocessing.py','main','start'])
            else:
                with open(timecsv,'w') as csvfile: # create file
                    csvwriter = csv.writer(csvfile, delimiter=",")
                    csvwriter.writerow(['epochtime','scriptname','segment','status']) # labels
                    csvwriter.writerow([t,'rpi-Preprocessing.py','main','start'])


    # OUTPUT passed optional arguments & filepath
    print('\n\n'+40*'~'+' SCRIPT: rpi-Preprocessing.py '+40*'~')
    print('\n'+20*'~'+' optional arguments '+20*'~')
    print("\n{}\t--verbose\n{}\t--superverbose\n{}\t--time\n{}\t--save\n{}\t--load\n{}\t--export\n{}\t--model\n\n{}\t--flowsampling\n{}\t--packetsampling".format(verbose,superverbose,time,save,load,export,model,flowsampling,packetsampling))
    print('\n'+20*'~'+' processing '+20*'~')
    print('\nbatchsize = {}\nsplitsize = {}'.format(batchsize,splitsize))
    print('\n'+20*'~'+' file '+20*'~'+'\n')
    if model or save: print('{}'.format(modelfile))
    print('{}\n'.format(path))
    if (not time): input('\n')


    # DO THIS AFTER LABELING, JUST TEMPORARY FIX HERE
    dropfeature = []
    dropfeature.append('flowStartMilliseconds')



    # IMPORT CSV

    if time:
        t = epochtime.time()
        #print('\nrpi-Preprocessing.py\n\t<<< start: {}'.format(t))
        if export: # write timestamp to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','importCSV','start'])

    dataset = pd.DataFrame()

    Xtrain = pd.DataFrame()
    Xtest = pd.DataFrame()
    Ytrain = pd.Series(dtype=int)
    Ytest = pd.Series(dtype=int)

    data = []
    print('>>> importing & pre-processing CSV line-by-line')
    # read csv in chunks
    for chunk in read_csv(path,chunksize=10**5,usecols=None,skipinitialspace=True,encoding='utf-8'):

        # DO THIS AFTER LABELING (flowStartMilliseconds)
        removeFeatures(chunk,dropfeature,False,False)

        chunk = conversion(chunk,False) # convert values into smaller datatypes
        # clean features
        cleanString(chunk,False,False)
        cleanNaN(chunk,0,False,False)
        # split into training & test portion on the fly
        chunksplit = splitDataframe(chunk,0.30,False,False) # [Xtrain,Xtest,Ytrain,Ytest]
        # accumulate splits
        Xtrain = Xtrain.append(chunksplit[0])
        Xtest = Xtest.append(chunksplit[1])
        Ytrain = Ytrain.append(chunksplit[2])
        Ytest = Ytest.append(chunksplit[3])

    del chunksplit
    del chunk
    gc.collect()

    if time:
        t = epochtime.time()
        #print('\nrpi-Preprocessing.py\n\t<<< start: {}'.format(t))
        if export: # write timestamp to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','importCSV','end'])



    # SCALER FIT

    if time:
        t = epochtime.time()
        #print('\nrpi-Preprocessing.py\n\t<<< start: {}'.format(t))
        if export: # write timestamp to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','Standardscaler-fit','start'])

    scaler = StandardScaler(copy=False)
    features = list(Xtrain) # used later to initialise empty numpy arrays via len(features)
    n = Xtrain.shape[0] # number of rows
    processed = 0

    print('>>> partial fit StandardScaler')
    # iterating over given data without dropping already processed rows
    while processed < n:
        toprocess = min(batchsize, n-processed) # current number of rows to process
        #Xtrain_partial = Xtrain[processed:processed+toprocess] # specific slice to process in current iteration
        scaler.partial_fit(Xtrain[processed:processed+toprocess]) # partial_fit scaler on current slice
        processed += toprocess # number of already processed rows, used to determin when to leave the loop

    #del Xtrain_partial
    #gc.collect()

    # initialise empty numpy arrays
    Xtrain_scaled = np.empty(shape=[0,len(features)])
    Xtest_scaled = np.empty(shape=[0,len(features)])

    if time:
        t = epochtime.time()
        #print('\nrpi-Preprocessing.py\n\t<<< start: {}'.format(t))
        if export: # write timestamp to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','Standardscaler-fit','end'])



    # SPLIT FILE

    if time:
        t = epochtime.time()
        #print('\nrpi-Preprocessing.py\n\t<<< start: {}'.format(t))
        if export: # write timestamp to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','Split','start'])

    # Xtrain: split training data into smaller portions for transformation and save to disk to free up memory
    n = Xtrain.shape[0]
    splitsize = 5*10**5
    toprocess = min(splitsize, n)
    iteration = int(n/splitsize)+1
    index = 0

    print('>>> split Xtrain')
    while toprocess > 0:
        index += 1
        npsave = npsaved / Xtrainnpy.format(index,iteration)
        if verbose: print('\tsave: {}'.format(npsave))
        print('\t{}/{}:'.format(index,iteration))
        print('\t\t<<< converting df to np.array')
        npXtrain = Xtrain[:][0:toprocess].to_numpy().astype(np.float32) # convert slice into np array
        Xtrain = Xtrain.drop(Xtrain.index[0:toprocess]) # drop processed slice from df
        print('\t\t<<< saving splitted Xtrain')
        np.save(npsave,npXtrain)
        if verbose: print('\n{}\n{} {} {}MB\n'.format(npXtrain,npXtrain.shape,npXtrain.dtype,int(npXtrain.nbytes/1024**2)))
        n -= toprocess # number of rows that need to be processed
        toprocess = min(splitsize, n)# get slice-size for next iteration

    iXtrain = np.arange(1,index+1,1) # create array to restore splitted files afterwards

    del Xtrain
    del npXtrain
    gc.collect()


    # SPLIT FILE
    # Xtest: split test data into smaller portions for transformation and save to disk to free up memory
    n = Xtest.shape[0]
    size = min(splitsize, n)
    iteration = int(n/splitsize)+1
    fnumber = iteration
    index = 0
    print('>>> split Xtest')
    while size > 0:
        index += 1
        npsave = npsaved / Xtestnpy.format(index,iteration)
        if verbose: print('\tsave: {}'.format(npsave))
        print('\t{}/{}:'.format(index,iteration))
        print('\t\t<<< converting df to np.array')
        npXtest = Xtest[:][0:size].to_numpy().astype(np.float32)
        Xtest = Xtest.drop(Xtest.index[0:size])
        print('\t\t<<< saving splitted Xtest')
        np.save(npsave,npXtest)
        if verbose: print('\n{}\n{} {} {}MB\n'.format(npXtest,npXtest.shape,npXtest.dtype,int(npXtest.nbytes/1024**2)))
        n -= size
        size = min(splitsize, n)

    iXtest = np.arange(1,index+1,1) # create array to restore splitted files afterwards
    del Xtest
    del npXtest
    gc.collect()

    if time:
        t = epochtime.time()
        #print('\nrpi-Preprocessing.py\n\t<<< start: {}'.format(t))
        if export: # write timestamp to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','Split','stop'])



    # SCALER TRANSFORM

    if time:
        t = epochtime.time()
        #print('\nrpi-Preprocessing.py\n\t<<< start: {}'.format(t))
        if export: # write timestamp to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','Scaler-transform-Xtrain','start'])

    # Xtrain
    print('>>> transform Xtrain')
    for index in iXtrain: # cycle through split-files and apply StandardScaler transform on the fly

        Xtrain_scaled = np.empty(shape=[0,len(features)]) # initialise empty numpy array

        npload = npsaved / Xtrainnpy.format(index,len(iXtrain))

        #npload = spath / 'tmp' / (filenames[findex]+"_Xtrain_"+str(index)+".npy") # forge path to load split-file
        if verbose: print('\nload: {}'.format(npload))
        print('\t{}/{}:'.format(index,len(iXtrain)))
        print('\t\t<<< loading splitted Xtrain')

        tmp = np.load(npload).astype(np.float32) # load split-file
        if verbose: print('\n{}\n{} {} {}MB\n'.format(tmp,tmp.shape,tmp.dtype,int(tmp.nbytes/1024**2)))

        print('\t\t<<< transform Xtrain')
        n = tmp.shape[0]
        size = min(batchsize, n)
        while size > 0:
            tmpscaled = scaler.transform(tmp[:][0:size],copy=None) # transform rows
            tmp = np.delete(tmp,np.s_[0:size:1],axis=0) # delete rows from array
            Xtrain_scaled = np.append(Xtrain_scaled,tmpscaled,axis=0).astype(np.float32)

            if verbose:
                print(tmpscaled)
                print(Xtrain_scaled)

            n -= size
            size = min(batchsize,n)

        del tmpscaled

        # save scaled split to disk
        npsave = npsaved / Xtrainnpy.format(index,len(iXtrain))
        #scaledsave = spath / "tmp" / (filenames[findex]+"_Xtrain_scaled_"+str(index)+".npy")
        if verbose: print('\nsave: {}'.format(npsave))
        print('\t\t<<< saving scaled Xtrain')
        np.save(npsave,Xtrain_scaled)
        if verbose: print('\nXtrain_scaled:\n\n{}\n{} {} {}MB\n'.format(Xtrain_scaled,Xtrain_scaled.shape,Xtrain_scaled.dtype,int(Xtrain_scaled.nbytes/1024**2)))
        del Xtrain_scaled
    del tmp

    if time:
        t = epochtime.time()
        #print('\nrpi-Preprocessing.py\n\t<<< start: {}'.format(t))
        if export: # write timestamp to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','Scaler-transform-Xtrain','end'])

    # SCALER TRANSFORM

    if time:
        t = epochtime.time()
        #print('\nrpi-Preprocessing.py\n\t<<< start: {}'.format(t))
        if export: # write timestamp to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','Scaler-transform-Xtest','start'])

    # Xtest
    print('>>> transform Xtest')
    for index in iXtest: # cycle through split-files and apply StandardScaler transform on the fly

        Xtest_scaled = np.empty(shape=[0,len(features)]) # initialise empty numpy array

        npload = npsaved / Xtestnpy.format(index,len(iXtest))
        #npload = spath / "tmp" / (filenames[findex]+"_Xtest_"+str(index)+".npy") # forge path to load split-file
        if verbose: print('\nload: {}'.format(npload))
        print('\t{}/{}:'.format(index,len(iXtest)))
        print('\t\t<<< loading splitted Xtest')

        tmp = np.load(npload).astype(np.float32) # load split-file
        if verbose: print('\n{}\n{} {} {}MB\n'.format(tmp,tmp.shape,tmp.dtype,int(tmp.nbytes/1024**2)))

        print('\t\t<<< transform Xtest')
        n = tmp.shape[0]
        size = min(batchsize, n)
        while size > 0:
            tmpscaled = scaler.transform(tmp[:][0:size],copy=None) # transform rows
            tmp = np.delete(tmp,np.s_[0:size:1],axis=0) # delete rows from array
            Xtest_scaled = np.append(Xtest_scaled,tmpscaled,axis=0).astype(np.float32)

            if verbose:
                print(tmpscaled)
                print(Xtest_scaled)

            n -= size
            size = min(batchsize,n)

        del tmpscaled

        # save scaled split to disk
        npsave = npsaved / Xtestnpy.format(index,len(iXtest))
        #scaledsave = spath / "tmp" / (filenames[findex]+"_Xtest_scaled_"+str(index)+".npy")
        if verbose: print('\nsave: {}'.format(scaledsave))
        print('\t\t<<< saving scaled Xtest')
        np.save(npsave,Xtest_scaled)
        if verbose: print('\nXtest_scaled:\n\n{}\n{} {} {}MB\n'.format(Xtest_scaled,Xtest_scaled.shape,Xtest_scaled.dtype,int(Xtest_scaled.nbytes/1024**2)))
        del Xtest_scaled
    del tmp

    if time:
        t = epochtime.time()
        #print('\nrpi-Preprocessing.py\n\t<<< start: {}'.format(t))
        if export: # write timestamp to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','Scaler-Transform-Xtest','end'])


    # PCA

    if time:
        t = epochtime.time()
        #print('\nrpi-Preprocessing.py\n\t<<< start: {}'.format(t))
        if export: # write timestamp to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','PCA-fit-transform-Xtrain','start'])

    Xpca = []
    ipca = IncrementalPCA(n_components = n_Xpca, batch_size = 10**5)

    print('>>> apply PCA partial fit')
    # PARTIAL FIT to Xtrain
    for index in iXtrain: # cycle through split files
        npload = npsaved / Xtrainnpy.format(index,len(iXtrain))
        #npload = spath / "tmp" / (filenames[findex]+"_Xtrain_scaled_"+str(index)+".npy")
        split = np.load(npload).astype(np.float32)
        #Xtrain = np.append(Xtrain,split,axis=0)
        print('\t{}/{}:'.format(index,len(iXtrain)))
        print('\t\t<<< partial fit to Xtrain')
        ipca.partial_fit(split)
    del split

    # TRANSFORM



    # Xtrain
    Xtrain = np.empty(shape=[0,n_Xpca]) # initialise empty numpy array
    print('>>> apply PCA transform Xtrain')
    for index in iXtrain:
        #npload = spath / "tmp" / (filenames[findex]+"_Xtrain_scaled_"+str(index)+".npy")
        npload = npsaved / Xtrainnpy.format(index,len(iXtrain))
        split = np.load(npload).astype(np.float32)
        print('\t{}/{}:'.format(index,len(iXtrain)))
        print('\t\t<<< transform Xtrain')
        split = ipca.transform(split)
        Xtrain = np.append(Xtrain,split,axis=0).astype(np.float32)
    del split

    if time:
        t = epochtime.time()
        #print('\nrpi-Preprocessing.py\n\t<<< start: {}'.format(t))
        if export: # write timestamp to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','PCA-fit-transform-Xtrain','end'])

    if verbose: print('\nXtrain (PCA):\n\n{}\n{} {} {}MB\n'.format(Xtrain,Xtrain.shape,Xtrain.dtype,int(Xtrain.nbytes/1024**2)))

    if time:
        t = epochtime.time()
        #print('\nrpi-Preprocessing.py\n\t<<< start: {}'.format(t))
        if export: # write timestamp to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','PCA-transform-Xtest','start'])

    Xtest = np.empty(shape=[0,n_Xpca]) # initialise empty numpy array
    print('>>> apply PCA transform Xtest')
    for index in iXtest:
        npload = npsaved / Xtestnpy.format(index,len(iXtest))
        #npload = spath / "tmp" / (filenames[findex]+"_Xtest_scaled_"+str(index)+".npy")
        split = np.load(npload).astype(np.float32)
        print('\t{}/{}:'.format(index,len(iXtest)))
        print('\t\t<<< transform Xtest')
        split = ipca.transform(split)
        Xtest = np.append(Xtest,split,axis=0).astype(np.float32)
    del split

    if time:
        t = epochtime.time()
        #print('\nrpi-Preprocessing.py\n\t<<< start: {}'.format(t))
        if export: # write timestamp to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','PCA-transform-Xtest','end'])

    if verbose: print('\nXtest (PCA):\n\n{}\n{} {} {}MB\n'.format(Xtest,Xtest.shape,Xtest.dtype,int(Xtest.nbytes/1024**2)))


    # RANDOM FOREST CLASSIFIER

    if time:
        t = epochtime.time()
        #print('\nrpi-Preprocessing.py\n\t<<< start: {}'.format(t))
        if export: # write timestamp to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','RandomForest-model','start'])

    # select already fitted modelfile or fit model
    if model:
        del Xtrain
        print('>>> importing model')
        model = joblib.load(modelfile)
    else:
        model = RandomForestClassifier()
        print('>>> fit RandomForestClassifier')
        model = model.fit(Xtrain,Ytrain)
        del Xtrain
        if save:
            print('>>> saving model')
            joblib.dump(model,modelfile)

    print('>>> create predictions')
    predictions = model.predict(Xtest)

    print('>>> create confusion-matrix')
    matrix = confusion_matrix(Ytest,predictions)

    print('>>> create classification-report')
    report = pd.DataFrame(classification_report(Ytest,predictions,digits=5,output_dict=True)).transpose()

    print('>>> save parameters, accuracy-score and feature-importance')
    parameters = model.get_params(deep=True)
    accuracyscore = accuracy_score(Ytest,predictions)
    featureimportance = model.feature_importances_

    if time:
        t = epochtime.time()
        #print('\nrpi-Preprocessing.py\n\t<<< start: {}'.format(t))
        if export: # write timestamp to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','RandomForest-model','end'])

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
        print('\n>>> exporting results to folder: {}'.format(logd))
        # list of all informations we want to save for later evaluation
        evaluation = {'model':[model],'parameters':[parameters],'accuracy-score':[accuracyscore],'feature-importance':[featureimportance],'confusion-matrix':[matrix]}
        results = pd.DataFrame.from_dict(evaluation,orient='index',columns=['summary'])
        # save results
        results.to_csv(resultcsv)
        report.to_csv(reportcsv)

    if time:
        end = timer()
        t = epochtime.time()
        print('\nPreprocessing.py\n[EPOCH, end]: {}'.format(t))
        print('[RUNTIME]: %.3f' % (end-start),'seconds')

        if export: # write timestamps to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'rpi-Preprocessing.py','main','end'])

    # DSTAT MONITORING
    # get running dstat pid
    # -q ...doesn't output pid to console, -s ...single-shot, only displays 
    pid = os.system('pidof /usr/bin/python3 /usr/bin/dstat -sq')
    #pid = os.system('pidof /usr/bin/python3 /usr/bin/dstat -s')
    
    # wait 50 seconds for dstat before terminating the process, seems like dstat writes its output to the target-file around every 45 seconds
    epochtime.sleep(50)

    # kill running dstat process
    os.kill(pid,9)

    exit()