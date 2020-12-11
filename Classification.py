# -*- coding: utf-8 -*-
"""
Created on Fri Sep 11 09:25:55 2020

@author: Patrick Resch
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



# capture files, https://www.unb.ca/cic/datasets/ids-2017.html
filenames = {1:'Monday-WorkingHours',2:'Tuesday-WorkingHours',3:'Wednesday-WorkingHours',4:'Thursday-WorkingHours',5:'Friday-WorkingHours'}

# ARGUMENT PARSING

# command line argument passthrough for better usability
import argparse
parser = argparse.ArgumentParser(description='script for cleaning dataframes imported from CSV files')
# positional arguments
parser.add_argument('file', metavar='file', type=int,nargs=1,help='select file to process: {}'.format(filenames))
# optional arguments
parser.add_argument('-v','--verbose', action='store_true', help='output additional informations')
parser.add_argument('--superverbose', action='store_true', help='output additional informations')
parser.add_argument('-t','--time', action='store_true', help='measure function-runtimes')
# force sampling choice
samplegroup = parser.add_mutually_exclusive_group(required=True)
samplegroup.add_argument('--flowsampling', action='store_true', help='use flow-sampled CSV files')
samplegroup.add_argument('--packetsampling', action='store_true', help='use per-packet sampled CSV files')
# force OS choice, https://docs.python.org/3/library/argparse.html#mutual-exclusion
osgroup = parser.add_mutually_exclusive_group(required=True)
osgroup.add_argument('--linux', action='store_true', help='use Linux paths')
osgroup.add_argument('--osx', action='store_true', help='use MacOS paths')
osgroup.add_argument('--windows', action='store_true', help='use windows paths')



args = parser.parse_args()


# DEFINITIONS

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
#@profile
def importCSV(csvpath,csvusecols=None,verbose=False,encoding='utf-8'):  
    # informational output
    print('\n\n'+40*'~'+' FUNCTION: importCSV '+40*'~')
    print('\n>>> importing CSV: {}'.format(csvpath))
    csvdata = read_csv(csvpath,usecols=csvusecols,skipinitialspace=True,encoding=encoding)
    if verbose:
        print('\n{}'.format(csvdata.groupby('Label').size()))
        print('\n{}'.format(csvdata.groupby('Attack').size()))
        if (not time): input('\n...')
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


# INFORMATIONAL OUTPUT

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
    print('\n{}'.format(dataset.describe()))
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


# PREPROCESSING

# CLEAN FEATURES 
# function to create a feature containing pseudo-random values
def createRandom(dataset,feature,verbose=False,time=False):
    import random
    for i in range(0,len(dataset)):
        dataset.at[i,feature]=random.randint(0,1000000)
    return

# clean given df from any infinite values by replacement
def cleanInf(dataset,mode,verbose=False,time=False):
    
    if time: start = timer()
    
    modename = {0: 'value', 1: 'mean', 2: 'min', 3: 'max', 4: 'std'}
    
    # informational output
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
            
            print('\n>>> replacing Infinite values: {}'.format(column))
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

# clean given df from any NaN values by replacement
def cleanNaN(dataset,mode,verbose=False,time=False):
    
    if time: start = timer()
    
    modename = {0: 'value', 1: 'mean', 2: 'min', 3: 'max', 4: 'std'}
    
    # informational output
    print('\n\n'+40*'~'+' FUNCTION: cleanNaN '+40*'~')
    print('\n>>> searching NaNs...')
    
    # summary for NaN values
    vNaN = dataset.isnull().sum()

    # get features (index & label) containing NaN values
    # feature (column)-index
    iNaN = []
    # feature (column)-label
    lNaN = []
    i = -1
    for x in vNaN:
        i=i+1
        # if there is at least one NaN value in the summary
        if(x > 0):
            iNaN.append(i)
            lNaN.append(vNaN.index[i])
    
    if (not iNaN): return
    
    # get row-number for NaN values
    # initialise empty lists 
    NaNindex=[]
    # empty list to fill with numpy arrays containing the row numbers for infinite values
    NaNRows=[]
    NaNtable=[]
    
    # output table containing features with NaN counts
    if verbose: 
        print('\n{}'.format(vNaN))
            
    # cycles through features containing NaN values
    # variable i to adress index-elements
    i = -1
    for column in lNaN:
        i = i+1
        # iterates through all rows of columns containing NaNs, returns table with 'True' or 'False' per row per feature
        NaNtable = dataset[column].isnull()
        
        # cycling through NaNtable, identifying features containing NaNs
        for i in range(0,dataset.shape[0]):
            if NaNtable[i] == True:
                NaNindex.append(i)
                
        # create temporary array from index list
        tmp = np.array(NaNindex)
        NaNRows.append(tmp)
        # reset index-list before next iteration
        NaNindex=[]
    if verbose and (not time): input('\n...') 
    
    # replace cells containing NaN values with e.g. mean values of that feature
    if iNaN:
        i=-1
        for column in lNaN:
            i = i+1
            # get total number of contained NaNs
            NaNcount = len(NaNRows[i])
            
            # create series with removed NaN values
            tmp = removeCells(dataset,column,NaNRows[i],False,False)
            # calculate specific feature values for further replacement of NaNs
            tmean = tmp.mean()
            tmax = tmp.max()
            tmin = tmp.min()
            tstd = tmp.std()
            
            if verbose:
                print('\n'+20*'~'+' replacement: {} '.format(column)+20*'~')
                print('\nmean: {}\nstd: {}\nmin: {}\nmax: {}'.format(tmean,tstd,tmin,tmax))
            
                print('\nmode: {}'.format(modename[mode]))
                print('cells: {}'.format(NaNcount))
            
            # replacement-modes
            if mode == 0: value = 0
            elif mode == 1: value = tmean
            elif mode == 2: value = tmin
            elif mode == 3: value = tmax
            elif mode == 4: value = tstd
                
            print('\n>>> replacing NaNs: {}'.format(column))
            writeCells(dataset,column,NaNRows[i],value,verbose,False)
                
    if verbose:
        # display NaN summary after replacement
        vNaN = dataset.isnull().sum()
        print('\n\n'+20*'~'+' cleaned '+20*'~')
        print('\n{}'.format(vNaN))
        
        if (not time): input('\n...')
        
    if time: end = timer()
    
    if time: print('\ncleanNaN\n[TIME]: %.3f' % (end-start),'seconds')
      
    return

# remove features containing strings from given df
def cleanString(dataset,verbose=False,time=False):
    
    if time: start = timer()
    
    # get table containgin object-types per feature
    stype = dataset.dtypes
    
    # informational output
    print('\n\n'+40*'~'+' FUNCTION: cleanString '+40*'~')
    print('\n>>> searching strings...')
    
    # get features (index & label) containing Strings
    # feature (column)-index
    istr=[]
    # feature (colum)-label
    lstr=[]
    
    # cycle through all features
    for i in range(0,len(stype)):
        if stype[i]=='object':
            istr.append(i)
            lstr.append(stype.index[i])
    
    if (not istr): return
    
    if verbose:
        print('\n{}\n\n'.format(stype))
        
    # remove features containing string from dataset
    # maybe extract before doing that
    removeFeatures(dataset,lstr,verbose,time)
    
    if time:
        end = timer()
    
    stype = dataset.dtypes
    
    if verbose:
        print('\n'+20*'~'+' cleaned '+20*'~')
        print('\n{}'.format(stype))
        if (not time): input('\n...')
    
    if time: print('\ncleanString\n[TIME]: %.3f' % (end-start),'seconds')
    
    return

# TODO: FYI if dataset contains no attacks, both features "Label" and "Attack" would get removed
# remove single-value-features from given df, since these contain no informations
def cleanSingleValue(dataset,verbose=False,time=False):
    
    if time: start = timer()
    
    # informational output
    print('\n\n'+40*'~'+' FUNCTION: cleanSingleValue '+40*'~')
    print('\n>>> searching single-unique-value features...')
    
    ldrop = []
    # contains number of unique values contained (per feature)
    counts = dataset.nunique()
    # list of features contained in dataset
    labels = dataset.columns.values
    
    # iterates over all features
    for i in range(0,len(counts)):
        # check for features containing a single unique value
        if counts[i] == 1:
            # add such feature to droplist
            ldrop.append(labels[i])

    # if single-value features in list, drop from dataset
    if ldrop: 
        if verbose: print('\n{}\n\n'.format(counts))
        removeFeatures(dataset,ldrop,verbose,time)
    else: return
    
    if time: end = timer()
        
    if verbose:
        counts = dataset.nunique()
        print('\n\n'+20*'~'+' cleaned '+20*'~')
        print('\n{}'.format(counts))
        if (not time): input('\n...') 
    
    if time: print('\ncleanSingleValue\n[TIME]: %.3f' % (end-start),'seconds')
    
    return


# TODO: gather new features from existing features (e.g. total packets from forward and backward packets)    
# TODO: create new column on specific position within the dataset
# REMOVE/EXTRACT FEATURES
# save features of given df from given list, drop everything else
def saveFeatures(dataset,features,verbose=False,time=False):
    
    if time: start = timer()
    
    # informational output
    print('\n>>> saving features...')
    print('\n\t{}'.format(features))
    
    # list of all features from given dataset
    ldrop = dataset.columns.values
    
    # index numbers for features
    index = []
    isave = []
    idrop = [i for i in range(0,len(ldrop))]
    
    for i in range(0,len(ldrop)):
        for j in features:
            if j == ldrop.item(i):
                index.append(i)
    
    if (not index):
        print('[WARNING] features not found. Abort.')
        return
        
    
    # create list of indexes from features to save
    isave = index.copy()
    isave.reverse()
    
    # remove features to save from drop (labels & index)
    for x in isave:
        ldrop = np.delete(ldrop, x)
        idrop = np.delete(idrop, x)
    # drop features from dataset
    dataset.drop(axis=1,labels=ldrop,inplace=True)    
    
    if time: end = timer()
    
    if verbose:
        print('\n'+10*'~'+' save '+10*'~')
        print('\n{}'.format(features))
        print('\n{}'.format(len(features)))

        print('\n'+10*'~'+' remove '+10*'~')
        print('\n{}'.format(ldrop))
        print('\n{}'.format(len(ldrop)))
        
        if (not time): input('\n...')
    
    if time: print('\nsaveFeatures\n[TIME]: %.3f' % (end-start),'seconds')        
        
    return

# remove given feature from given df
def removeFeatures(dataset,feature,verbose=False,time=False):
    
    if time: start = timer()
    
    # informational output
    print('>>> removing features...')
    
    # drop features to remove directly from dataset
    dataset.drop(axis=1,columns=feature,inplace=True)
    
    if time: end = timer()
    
    if verbose: 
        print('\n\t{}'.format(feature))
        if (not time): input('\n...')
        
    if time: print('\nremoveFeatures\n[TIME]: %.3f' % (end-start),'seconds')
        
    return    

# copy given feature into new dataframe for further manipulation, without affecting original df
def extractFeatures(dataset,feature,verbose=False,time=False):
    
    if time: start = timer()
    
    # informational output
    if verbose:
        print('\n>>> extracting features...')
        print('\n\t{}'.format(feature))
    
    # create a new df containing given feature as copy of the original df
    new = dataset[feature].copy()
    
    if time: 
        end = timer()
        print('\nextractFeatures\n[TIME]: %.3f' % (end-start),'seconds')
    
    # return extracted features for further processing
    return new


# REMOVE/MANIPULATE CELLS 
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

# remove given cells from a copy of the given dataframe feature, return the manipulated copy for further calculations
def removeCells(dataset,feature,cells,verbose=False,time=False):
    
    if time: start = timer()
    
    # informational output
    if verbose:
        print('\n'+10*'~'+' removeCells '+10*'~')
        print('\n>>> removing cells from features...')
    
    # copy extracted features into new dataframe
    tmp = extractFeatures(dataset,feature,verbose)
    
    if verbose:
        print('\n'+10*'~'+' removeCells, feature: {}, cells: {} '.format(feature,len(cells))+10*'~')
        print('\n{}'.format(tmp.describe()))
    
    # drop cells from df copy containing given feature
    tmp.drop(axis=0,index=cells,inplace=True)
    
    if time: end = timer()
    
    if verbose:
        print('\n'+10*'~'+' removeCells, result '+10*'~')
        print('\n{}'.format(tmp.describe()))
        if (not time): input('\n...')
     
    if time: print('\nremoveCells\n[TIME]: %.3f' % (end-start),'seconds')
    
    # return manipulated copy of the feature for further processing
    return tmp


# CLASSIFICATION

# SPLIT & SCALE DATASET
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
    
    # splitting up the data into training & validation datasets into 80% training & 20% validation
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
    tmp[features] = scaler.fit_transform(tmp[features])
    tmpscaled.append(tmp)
       
    # TEST (transform)
    # transform Xtest    
    tmp = datasets[1]
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

# PCA & RANDOM FOREST

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

# apply ML model
def applyModel(model,Xtrain,Ytrain,Xtest,Ytest,verbose=False,time=False):
    
    if time: start = timer()
    
    # informational output
    print('\n\n'+40*'~'+' FUNCTION: applyModel '+40*'~')
    print('\n>>> fitting model with {}...'.format(model))
    
    # fit model to Xtrain & Ytrain
    model.fit(Xtrain,Ytrain)
    
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
    
    # output final results
    print('\n\n'+10*'~'+' {}: results '.format(model)+10*'~')
    print('\nModel-Parameters:\n{}'.format(model.get_params(deep=True)))
    print('\n\nAccuracy-Score: %.5f' % (accuracy_score(Ytest,predictions)))
    print('\n\nFeature-Importance:\n{}'.format(model.feature_importances_))
    print('\n\nConfusion-Matrix:\n')
    print('t       p r e d i c t')
    print('r         "0"    "1"')
    print('u  "0":',matrix[0])
    print('e  "1":',matrix[1])
    print('\n\nClassification-Report:\n\n',report)
    
    if time: print('\napplyModel\n[TIME]: %.3f' % (end-start),'seconds')
    
    return

if __name__ == '__main__':
    
    global verbose 
    global time
    global dataset
    
    #sys.stdout = open("ClassificationOutput.txt","w")
    
    verbose = args.verbose
    superverbose = args.superverbose
    if superverbose: verbose = True
    time = args.time  
    flowsampling = args.flowsampling
    packetsampling = args.packetsampling
    
    windows = args.windows
    osx = args.osx
    linux = args.linux


    # index-position of chosen file
    findex = args.file[0]-1
    
    if time: 
        start = timer()
        # save epochtime
        t = epochtime.time()
        print('\nClassification.py\n[EPOCH, start]: {}'.format(t))

        # write timestamp to csv
        with open('/home/noooberino/timestamps.csv','a') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=",")
            csvwriter.writerow([t,'Classification.py','start'])
    
    # IMPORT CSV
    
    # WINDOWS
    # path to CSV files based on OS choice
    if windows: fpath = r"D:\CIC-IDS2017\PCAP\flow-sampledCSV"
    elif linux: fpath = r"/mnt/data/CIC-IDS2017/PCAP/flow-sampledCSV"
    
    if windows: ppath = r"D:\CIC-IDS2017\PCAP\packet-sampledCSV"
    elif linux: ppath = r"/mnt/data/CIC-IDS2017/PCAP/packet-sampledCSV"
    
    # name for sampled, unlabeled CSVs
    csvname = ["Monday-WorkingHours.csv","Tuesday-WorkingHours.csv","Wednesday-WorkingHours.csv","Thursday-WorkingHours.csv","Friday-WorkingHours.csv"]
    
    # set path to sampeld CSV based on optional arguments
    if flowsampling:
    	# windows folder separator
        if windows: path = fpath+"\\"+csvname[findex]
        elif linux: path = fpath+"/"+csvname[findex] 
    elif packetsampling:
    	# windows folder separator5
        if windows: path = ppath+"\\"+csvname[findex]
        elif linux: path = ppath+"/"+csvname[findex]
    
    # check passed optional arguments, filepaths and forged commands
    print('\n\n'+40*'~'+' SCRIPT: Classification.py '+40*'~')
    print('\n'+20*'~'+' optional arguments '+20*'~')
    print("\n{}\t--verbose\n{}\t--superverbose\n{}\t--time\n{}\t--flowsampling\n{}\t--packetsampling".format(verbose,superverbose,time,flowsampling,packetsampling))
    print('\n\n{}'.format(path))
    if (not time): input('\n...')
        
    # IMPORT
    dataset = importCSV(path,None,verbose)
    # output dataset informations
    printdata(dataset,'original',verbose)

    # EXT2NUM via mapping  
    # change strings BENIGN and DDoS contained within the feature 'Label' to numerical values according to given mapping
    #mapping = {'BENIGN':0,'DDoS':1,'PortScan':1,'Bot':1,'FTP-Patator':1,'SSH-Patator':1,'Infiltration':1,'Web Attack – Brute Force':1,'Web Attack – Sql Injection':1,'Web Attack – XSS':1}
    #ext2num(dataset,mapping,verbose)
    
    # drop feature 'flowStartMilliseconds'
    # TODO: should be done directly in FLowSampling.py instead?
    dropfeature = []
    dropfeature.append('flowStartMilliseconds')    
    removeFeatures(dataset,dropfeature,verbose,time)
    
    
    # PREPROCESSING
    # REMOVE NaNs, INF, STRINGS
    # get rid of NaNs, Inf & Str objects within the DataFrame
    cleanSingleValue(dataset,verbose,time)
    cleanString(dataset,verbose,time)
    # TODO: add replacement value as function argument?
    cleanInf(dataset,0,verbose,time)
    cleanNaN(dataset,1,verbose,time)
    
    printdata(dataset,'cleaned',verbose)
    

    # CLASSIFICATION
    # get split data for training and validation, format of returned data as list: [Xtrain,Xtest,Ytrain,Ytest]
    # accessing data for further Classification via datasplit[i], splitting training:test in ration 70:30
    datasplit = splitDataframe(dataset,0.30,verbose,time)

    # CREATING COPY OF DATA TO SCALE
    # create copy of splitdata to apply scaling to, to not overwrite original values
    # TODO: for improved memory efficiency just use original data, skipping this block
    scaleinput = []        
    scaleinput = copyDfList(datasplit,scaleinput,verbose,time)  
    
    # SCALING DATA
    # MinMax proportional scaling
    # TODO: apply scaling on original split-dataframe for less memory consumption
    #datascaled = scalingDataframe(datasplit,[],verbose,time)
    datascaled = scalingDataframe(scaleinput,[],verbose,time)
    
    # PCA (principal component analysis)
    # apply PCA on training data, returns dataset wtih n components
    n = 4
    Xpca = PCAnalysis(datascaled,n,verbose,time)
    
    # RANDOM FOREST (training)
    # choose Random Forest classifier as model
    model = RandomForestClassifier()
    # Xpca[0] = Xtrain, datasplit[2] = Ytrain
    applyModel(model,Xpca[0],datasplit[2],Xpca[1],datasplit[3],verbose,time)
    
    
    # TODO: for comparison, use dataset without PCA & proportional scaling (Random Forest doesn't care about that)
    #applyModel(model,datasplit[0],datasplit[2],datasplit[1],datasplit[3],verbose,time)
    #cv = RepeatedStratifiedKFold(n_splits=10, n_repeats=3, random_state=1)

    
    if time:
        end = timer()
        t = epochtime.time()
        print('\nClassification.py\n[EPOCH, end]: {}'.format(t))
        print('[RUNTIME]: %.3f' % (end-start),'seconds')
        # write timestamp to csv
        with open('/home/noooberino/timestamps.csv','a') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=",")
            csvwriter.writerow([t,'Classification.py','end'])
    
    if (not time): input('\n...')
    
    #sys.stdout.close()
    
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