#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 17 13:24:01 2020

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

    if time: start = timer()

    # informational output
    print('\n\n'+40*'~'+' FUNCTION: importCSV (chunksize: {}) '.format(chunksize)+40*'~')
    print('\n>>> importing CSV: {}'.format(csvpath))

    chunksize = 10**9

    csvdata = pd.DataFrame() # initialise empty dataframe

    # if no chunksize is given, read CSV in one step, otherwise read in chunks
    if chunksize == None:
        csvdata = read_csv(csvpath,usecols=csvusecols,skipinitialspace=True,encoding=encoding)
    # chunksize determines numbers of rows per chunk
    else:
        for chunk in read_csv(csvpath,usecols=csvusecols,skipinitialspace=True,encoding=encoding,chunksize=chunksize):
            csvdata = csvdata.append(chunk)

    printdata(csvdata,'chunked')
    input('blub')

    if verbose:
        print('\n{}'.format(csvdata.groupby('Label').size()))
        print('\n{}'.format(csvdata.groupby('Attack').size()))
        if (not time): input('\n...')

    if time: 
        end = timer()
        print('\nimportCSV\n[TIME]: %.3f' % (end-start),'seconds')

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
    return
# outputs basic datset informations
def printdata(dataset,heading,verbose=False):
    print('\n\n'+40*'~'+' FUNCTION: printdata, {} '.format(heading)+40*'~')
    print('\n{}\n'.format(dataset))
    if not rpi: print('\n{}\n'.format(dataset.describe())) # skip for rpi

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

# CLEANING FEATURES 
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
def cleanNaN_original(dataset,mode,verbose=False,time=False):
    
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
def cleanNaN(dataset,replacement,verbose=False,time=False):

    if time: start = timer()

    # informational output
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
        print('>>> replacing NaNs: {}'.format(column))
        dataset[column] = dataset[column].replace(np.nan, replacement)

    if time:
        end = timer()
        print('\ncleanNaN\n[TIME]: %.3f' % (end-start),'seconds')

    return
# remove features containing strings from given df
def cleanString(dataset,verbose=False,time=False):

    if time: start = timer()

    # informational output
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
        if time: print('\ncleanSingleValue\n[TIME]: %.3f' % (end-start),'seconds')
        return

    else: 
        if time: end = timer()
        print('\ncleanSingleValue\n[TIME]: %.3f' % (end-start),'seconds')
        return

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
    for i in range(0,len(feature)):
        print('>>> removing feature: {}'.format(feature[i]))

    # drop features to remove directly from dataset
    dataset.drop(axis=1,columns=feature,inplace=True)

    if time:
        end = timer()
        print('\nremoveFeatures\n[TIME]: %.3f' % (end-start),'seconds')

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
# TODO: implement replacements via numpy.vectorize
def writeCellsVectorized(dataset,feature,cells,content,verbose=False,time=False):

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
        chunksize = 10**3
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
    # output basic dataset informations
    printdata(dataset,'original',verbose)


    # PREPROCESSING
    # manually dropping feature 'flowStartMilliseconds'
    # TODO: should be done directly in FLowSampling.py instead?
    dropfeature = []
    dropfeature.append('flowStartMilliseconds')
    removeFeatures(dataset,dropfeature,verbose,time)
    # REMOVE NaNs, INF, STRINGS
    # get rid of NaNs, Inf & Str objects within the DataFrame
    cleanSingleValue(dataset,verbose,time)
    cleanString(dataset,verbose,time)
    # mode 0: replace with value (0 per default, can be changed within the functions)
    cleanInf(dataset,0,verbose,time)
    cleanNaN(dataset,0,verbose,time)
    # output basic informations of cleaned dataset
    printdata(dataset,'cleaned',verbose)


    # SAVE
    # save preprocessed dataset to CSV
    filesave = str(savepath)+"/"+str(filenames[findex])+"_processed.csv"
    print('\n>>> save preprocessed data to CSV: {}'.format(filesave))
    dataset.to_csv(str(filesave), index = False,encoding='utf-8-sig')

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