#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 17 14:25:00 2020

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
#from memory_profiler import profile

import time as epochtime
import numpy as np
import pandas as pd
import sys
import csv
import pickle
import os
import joblib

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
parser = argparse.ArgumentParser(description='classification script, can be used on complete datasets, loading or saving fitted models and test-portions.')
# positional arguments
parser.add_argument('file', metavar='file', type=int,nargs=1,help='select file to process: {}'.format(filenames))
# optional arguments
parser.add_argument('-v','--verbose', action='store_true', help='output additional informations')
parser.add_argument('--superverbose', action='store_true', help='output additional informations')
parser.add_argument('-t','--time', action='store_true', help='measure function-runtimes')
parser.add_argument('-e','--export', action='store_true', help='export timestamps & results')
parser.add_argument('-m','--model', action='store_true', help='import model')
parser.add_argument('-d','--data',action='store_true', help='import dataXtrain, Ytrain, Xtest, Ytest')
parser.add_argument('-s','--save', action='store_true', help='export model and testdata for further classification')
parser.add_argument('-l','--load', action='store_true', help='import model and testdata for further classification')
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
def importCSV(csvpath,csvusecols=None,verbose=False,chunksize=None,encoding='utf-8'):  
    # informational output
    print('\n\n'+40*'~'+' FUNCTION: importCSV (chunksize: {}) '.format(chunksize)+40*'~')
    print('\n>>> importing CSV: {}'.format(csvpath))

    # if no chunksize is given, read CSV in one step, otherwise read in chunks
    if chunksize == None:
        csvdata = read_csv(csvpath,usecols=csvusecols,skipinitialspace=True,encoding=encoding)
    # chunksize determines numbers of rows per chunk
    else:
        chunk = read_csv(csvpath,usecols=csvusecols,skipinitialspace=True,encoding=encoding,chunksize=chunksize)
        csvdata = pd.concat(chunk) # concatenate chunks into single dataframe

    if verbose:
        print('\n{}\n'.format(csvdata.groupby('Label').size()))
        #print('\n{}'.format(csvdata.groupby('Attack').size()))
    return csvdata
# dataset ext2numerical
def ext2num(dataset,mapping,verbose):
    
    if not (verbose or time):
        print('\n...applying function ext2num\n')
    
    if verbose:
        print('\n\n'+40*'~'+' FUNCTION: ext2num '+40*'~')
        print('\n',dataset.groupby('Label').size())
        print('\nmapping:\n',mapping)

    #print('\n\napplying method ext2num...\n\n')

    if time:
        start = timer()
    
    dataset.replace({'Label':mapping},inplace=True)
    
    if time:
        end = timer()

    if verbose:
        print('\n',dataset.groupby('Label').size())
        if (not time): input('\n{VERBOSE} press ENTER to continue...\n')       
        
    if time: print('\next2num\n{TIME}: %.3f' % (end-start),'seconds')
    return

# OUTPUT functions
# outputs additional informations only shown in verbose mode
def verboseprint(dataset):
    print('\n{}\n'.format(dataset.columns))
    print('\n{}'.format(dataset.info()))
    if (not time): input('\n...')
    return
# outputs basic datset informations
def printdata(dataset,heading,verbose=False):
    print('\n\n'+40*'~'+' FUNCTION: printdata, {} '.format(heading)+40*'~')
    print('\n{}'.format(dataset))
    #if (not time): input('\n...')
    if not rpi: print('\n{}'.format(dataset.describe())) # skip for rpi
    if verbose and (not time): input('\n...')
    if verbose:
        verboseprint(dataset)
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

# SPLIT & SCALE functions
# create copy of dataframes in lists
def copyDfList(dflist,newlist,verbose=False,time=False):

    newlist = []
    # creates copies of the dataframes contained in given list
    # append those copies to a new list and return the new list
    for i in range(0,len(dflist)):
        tmp = dflist[i].copy()
        newlist.append(tmp)
        
    return newlist
# split given df into training & validation portions as array
def splitData(dataset,testsize,verbose=False,time=False):
    
    if time: start = timer()
    
    # informational output
    print('\n\n'+40*'~'+' FUNCTION: splitData '+40*'~')
    print('\n>>> splitting dataframe into training & test portion...')
    
    # splitting dataset, to have data for comparison later to estimate algorithm accuracy
    # write dataset values into array
    array = dataset.values
    # empty list to return X_train, X_validation, Y_train, Y_validation
    data = []

    # all but the very last column put into X
    X = array[:,:-1]
    # very last column (label) put into Y as separate column
    Y = array[:,-1]
    
    # splitting up the data into training & validation datasets into 80% training & 20% validation
    # X_train & Y_train for preparing models
    # X_validation & Y_validation to use later on
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
        
    if time: print('\nsplitData\n[TIME]: %.3f' % (end-start),'seconds')
    
    return data
# split given df into training & test portions
def splitDataframe(dataset,testsize,verbose=False,time=False):
    
    if time: start = timer()
    
    # informational output
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
# MinMax Scaler (proportional scaling) using numpy arrays
def scalingArray(data,verbose=False,time=False):
    scaler = MinMaxScaler()
    
    # X_train
    X = data[0]
    
    # fit and transform
    X_scaled = scaler.fit_transform(X)
    print(X_scaled)
    print(np.max(X_scaled))
    print(np.min(X_scaled))
    if (not time): input('...')
    
    
    return
# Standard (z-Score) Scaler (proportional scaling) using dataframe
def scalingDataframe(datasets,features,verbose=False,time=False):
    
    if time: start = timer()
    
    #scaler = MinMaxScaler()
    scaler = StandardScaler()
    tmpscaled = []
    
    # informational output
    print('\n\n'+40*'~'+' FUNCTION: scalingDataframe: {} '.format(scaler)+40*'~')
    print('\n>>> scaling values...')
    
    # get all features if no features are given as argument
    if not features: features = list(datasets[0])
    
    # TRAINING
    # fit & transform Xtrain
    tmp = datasets[0]
    print('>>> fit & transform Xtrain...')
    tmp[features] = scaler.fit_transform(tmp[features])
    tmpscaled.append(tmp)
       
    # TEST (transform)
    # transform Xtest    
    tmp = datasets[1]
    print('>>> transform Xtest...')
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

# PCA & MODEL functions
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
# apply ML model (replaced by makePredictions)
def applyModel(model,Xtrain,Ytrain,Xtest,Ytest,verbose=False,time=False):

    if time: start = timer()
    print('\n\n'+40*'~'+' FUNCTION: applyModel '+40*'~') # informational output

    # load already fitted model
    if load:
        print('\n>>> loading model: {}'.format(modelfile))
        with open(modelfile,'rb') as file:
            model = pickle.load(file)
    # fit model to Xtrain & Ytrain
    else:
        print('\n>>> fitting model with {}...'.format(model))
        model.fit(Xtrain,Ytrain)
        # save model to file for further classifications
        if save:
            print('\n>>> exporting model to file: {}'.format(modelfile))
            joblib.dump(model,modelfile) # use joblib for saving model
            #with open(modelfile,'wb') as file:
            #    pickle.dump(model,file)

    # make predictions for the validation data Xtest, create reports based on predictions and the GT-table Ytest
    predictions = model.predict(Xtest)
    matrix = confusion_matrix(Ytest,predictions)
    report = classification_report(Ytest,predictions,digits=5)

    if time: end = timer()

    if verbose: 
        print('\n\n'+10*'~'+' {}: training '.format(model)+10*'~')
        print('\nXtrain:\n{}\n{}'.format(Xtrain,Xtrain.shape))
        print('\n\nYtrain:\n{}'.format(Ytrain.value_counts()))
        if (not time): input('\n...')
        print('\n\n'+10*'~'+' {}: test '.format(model)+10*'~')
        print('\nXtest:\n{}\n{}'.format(Xtest,Xtest.shape))
        print('\n\nYtest:\n{}'.format(Ytest.value_counts()))
        if (not time): input('\n...')

    # calculate results
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
        print('\n>>> exporting results to folder: {}'.format(logfolder))
        # list of all informations we want to save for later evaluation
        evaluation = {'model':[model],'parameters':[parameters],'accuracy-score':[accuracyscore],'feature-importance':[featureimportance],'confusion-matrix':[matrix]}
        results = pd.DataFrame.from_dict(evaluation,orient='index',columns=['summary'])
        # save results
        results.to_csv(resultscsv)
        report.to_csv(reportcsv)

    if time: print('\napplyModel\n[TIME]: %.3f' % (end-start),'seconds')

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

    save = args.save
    load = args.load
    export = args.export
    model = args.model
    data = args.data

    rpi = args.rpi
    windows = args.windows
    osx = args.osx
    linux = args.linux
    findex = args.file[0] # index-position of passed file

    # name for sampled & labeled CSVs
    csvname = ["Merged.csv","Monday-WorkingHours.csv","Tuesday-WorkingHours.csv","Wednesday-WorkingHours.csv","Thursday-WorkingHours.csv","Friday-WorkingHours.csv"]

    if time: 
        start = timer() # runtime
        t = epochtime.time() # epochtime
        print('\nClassification.py\n[EPOCH, start]: {}'.format(t))

        if export: # write timestamp to csv
            if os.path.isfile(timecsv):
                with open(timecsv,'a') as csvfile:
                    csvwriter = csv.writer(csvfile, delimiter=",")
                    csvwriter.writerow([t,'Classification.py','start'])
            else:
                with open(timecsv,'w') as csvfile:
                    csvwriter = csv.writer(csvfile, delimiter=",")
                    csvwriter.writerow([t,'Classification.py','start'])

    # PATHS & VARIABLES, based on OS choice
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
        chunksize = 10**3

    # paths to processed files/folders based on sampling choice
    if flowsampling:
        # set filename for model file
        modelfolder = str(wd)+"/csv/flow-sampled/fitted/"
        if rpi: modelfile = str(modelfolder)+str(filenames[findex])+"_model_32bit.pkl"
        else: modelfile = str(modelfolder)+str(filenames[findex])+"_model_64bit.pkl"
        # set filename for pre-sampled, pre-processed datasets
        if windows: path = fpath+"\\"+csvname[findex]
        elif (linux or rpi): path = fpath+"/processed/"+filenames[findex]+"_processed.csv"
    elif packetsampling:
        modelfolder = str(wd)+"/csv/packet-sampled/fitted/"
        # set filename for model file
        if rpi: modelfile = str(modelfolder)+str(filenames[findex])+"_model_32bit.pkl"
        else: modelfile = str(modelfolder)+str(filenames[findex])+"_model_64bit.pkl"
        # set filename for pre-sampled, pre-processed datasets
        if windows: path = ppath+"\\"+csvname[findex]
        elif (linux or rpi): path = ppath+"/processed/"+filenames[findex]+"_processed.csv"

    # set filepaths & filename
    xtf = str(modelfolder)+str(filenames[findex])+"_Xtest.npy"
    ytf = str(modelfolder)+str(filenames[findex])+"_Ytest.npy"
    xtrf = str(modelfolder)+str(filenames[findex])+"_Xtrain.npy"
    ytrf = str(modelfolder)+str(filenames[findex])+"_Ytrain.npy"

    # check passed optional arguments, filepaths and forged commands
    print('\n\n'+40*' '+' FILE: {}'.format(filenames[findex]))
    print(40*'~'+' SCRIPT: Classficiation.py '+40*'~')
    print('\n'+20*'~'+' optional arguments '+20*'~')
    print("\n{}\t--verbose\n{}\t--superverbose\n{}\t--time\n{}\t--rpi\n{}\t--linux\n{}\t--osx\n{}\t--windows\n{}\t--save\n{}\t--load\n{}\t--export\n{}\t--model\n{}\t--data".format(verbose,superverbose,time,rpi,linux,osx,windows,save,load,export,model,data))
    print('\n'+20*'~'+' paths & files '+20*'~')
    print('\nlogs:\t{}'.format(logfolder))
    if export:
        print('report:\t{}'.format(reportcsv))
        print('result:\t{}\n'.format(resultscsv))
    if load or save or data:
        if load: print('model:\t{}'.format(modelfile))
        print('Xtest:\t{}'.format(xtf))
        print('Ytest:\t{}'.format(ytf))
        print('Xtrain:\t{}'.format(xtrf))
        print('Ytrain:\t{}'.format(ytrf))
    if (not time): input('\n...')

    # IMPORT: import already processed data
    if load or data:
        # importing Xtest, Ytest
        print('\n>>> importing Xtest...')
        Xtest = np.load(xtf)
        print('>>> importing Ytest:...')
        Ytest = np.load(ytf)
        # import Xtrain, Ytrain if no model is imported
        if data:
            print('>>> importing Xtrain...')
            Xtrain = np.load(xtrf)
            print('>>> importing Ytrain...')
            Ytrain = np.load(ytrf)

    # PROCESS: split, scale & PCA
    else:
        # IMPORT: pre-processed data
        chunksize = 10**3 # just for testing purpose, gets set with --rpi normally
        dataset = importCSV(path,None,verbose,chunksize)
        printdata(dataset,'pre-processed',verbose)

        # SPLIT: create split data for training and validation (test), format of returned data as list: [Xtrain,Xtest,Ytrain,Ytest]
        datasplit = splitDataframe(dataset,0.30,verbose,time)

        # SCALE: apply StandardScaler (z-score)
        datascaled = scalingDataframe(datasplit,[],verbose,time)

        # PCA (principal component analysis): apply on training data, returns dataset with n components
        n = 4
        Xpca = PCAnalysis(datascaled,n,verbose,time)

        # set variables for further processing
        Xtrain = Xpca[0]
        Xtest = Xpca[1]
        Ytrain = datasplit[2]
        Ytest = datasplit[3]

    # SAVE: save processed data
    if save and (not data) and (not load):
        print('\n>>> saving Xtest: {}'.format(xtf))
        np.save(xtf,Xtest)
        print('>>> saving Ytest: {}'.format(ytf))
        np.save(ytf,Ytest)
        print('>>> saving Xtrain: {}'.format(xtrf))
        np.save(xtrf,Xtrain)
        print('>>> saving Ytrain: {}'.format(ytrf))
        np.save(ytrf,Ytrain)

    # CLASSIFICATION
    if (model or load): # load model
        print('>>> importing model...')
        model = joblib.load(modelfile) # load model

    else: # fit model
        model = RandomForestClassifier()
        print('>>> fitting model with {}...'.format(model))
        model = model.fit(Xtrain,Ytrain)
        if save: # save model via joblib
            print('\n>>> save model: {}'.format(modelfile))
            joblib.dump(model,modelfile)

    makePredictions(model,Xtest,Ytest,export)

    if time:
        end = timer()
        t = epochtime.time()
        print('\nClassification.py\n[EPOCH, end]: {}'.format(t))
        print('[RUNTIME]: %.3f' % (end-start),'seconds')
        
        if export: # write timestamps to csv
            with open(timecsv,'a') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",")
                csvwriter.writerow([t,'Classification.py','end'])

    exit()


    #sys.stdout.close()
    
    # TODO: for comparison, use dataset without PCA & proportional scaling (Random Forest doesn't care about that)
    #applyModel(model,datasplit[0],datasplit[2],datasplit[1],datasplit[3],verbose,time)
    #cv = RepeatedStratifiedKFold(n_splits=10, n_repeats=3, random_state=1)

    '''
    # SCATTER MATRIX
    # use some random features (takes quite some time to plot)
    # should be used with features from PCA
    keep=['Source Port','Destination Port','Flow Duration','Max Packet Length','Min Packet Length','Packet Length Mean']
    saveFeatures(X_train, keep,verbose)
    scatter_matrix(X_train)
    pyplot.show()
    '''
    
    
    
    '''
    # HISTOGRAM PLOTS
    
    
    # histogram-plots for specific features
    label = 'HISTOGRAM, original'
    # features in dataset X_train
    #features = list(dataset)
    features = list(X_train)
    # bins increases number of histogram bins to 100 (default=10)
    dataset.hist(column='Flow Duration',bins=100,legend=False)
    dataset.hist(column=features,bins=100,legend=False)
    #pyplot.show()
    
    label = 'HISTOGRAM, scaled'
    # all features in X_train
    
    # bins increases number of histogram bins to 100 (default=10)
    X_train.hist(column='Flow Duration',bins=100)
    X_train.hist(column=features,bins=100)
    pyplot.show()
    
    # PLOT multiple features from the same dataset into a single histogram
    features = list(X_train)
    #pyplot.figure(figsize=(8,6))
    pyplot.hist([X_train['Flow Duration'],X_train['Active Mean'],X_train['Idle Mean']],bins=100,label=['Flow Duration','Active Mean','Idle Mean'])
    #pyplot.hist([dataset[features]],bins=100)
    #pyplot.hist(X_train['Flow Duration'],bins=100,label='X_train')
    #pyplot.savefig('Flow Duration for original and training dataset')
    pyplot.show()
    '''