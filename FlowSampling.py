# -*- coding: utf-8 -*-
"""
Created on Fri Sep 11 09:25:55 2020

@author: Patrick
"""

from pandas import read_csv
from timeit import default_timer as timer

import numpy as np
import pandas as pd

import subprocess
import os
import re
import sys

# ARGUMENT PARSING
# command line argument passthrough for better usability
import argparse
parser = argparse.ArgumentParser(description='script for sampling PCAP files via go-flows (flow-based sampling), output is CSV')

parser.add_argument('--verbose', action='store_true', help='output additional informations')
parser.add_argument('--superverbose', action='store_true', help='output additional informations, including loop iteration output')
parser.add_argument('--time', action='store_true', help='measure function-runtimes')
parser.add_argument('--windows', action='store_true', help='use windows paths')
parser.add_argument('--osx', action='store_true', help='use MacOS paths')
parser.add_argument('--check', action='store_true', help='check if number of sampled packets is correct')

parser.add_argument('mode', metavar = 'mode', type=int,nargs=1,help='choose sampling mode 1-4' )
parser.add_argument('file', metavar = 'file', type=int,nargs=1,help='choose integer 0 - 4 for PCAPs from Monday to Friday' )
parser.add_argument('n', metavar='n', type=int,nargs=1,help='integer used to determine sampling steps')

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
def importCSV(csvpath,csvusecols=None,verbose=False,encoding='utf-8'):
    if verbose:
        print('\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION: importCSV, path: {} ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'.format(csvpath))
        print('\n>>> importing CSV...')
        
    csvdata = read_csv(csvpath,usecols=csvusecols,skipinitialspace=True,encoding=encoding)
    return csvdata


# OUTPUT INFORMATIONS from DataFrames
# outputs additional informations only shown in verbose mode
def verboseprint(dataset):
    print('\nDataset, Shape:\n',dataset.shape)
    print('\nDataset, Columns:\n',dataset.columns)
    print('\n\nDataFrame, Info:')
    dataset.info(max_cols=10)
    return

# outputs basic datset informations
def printdata(dataset,heading,verbose=False):
    print('\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION: printdata,',heading,'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    #print('\nDataset:\n',dataset.head(10))
    print('\nDataset:\n',dataset)
    print(dataset.describe())
    if verbose:
        verboseprint(dataset)
    #input('press ENTER to continue...\n')
    return

# dataset description and grouped summary for 'Label'
def summary(dataset):
    #poptions()
    print('\nDataset, Description:\n\n',dataset.describe())
    print('\nLabel, Summary:\n\n',dataset.groupby('Label').size())
    #resetpoptions()
    return


# CLEAN FEATURES, determine cells/features containing NaNs, Infs or Strings 
# clean Infinite values with replacement
def cleanInf(dataset,verbose=False,time=False):
      
    if not (verbose or time): print('\n...applying function cleanInf\n')
    if time: start = timer()
 
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

    # cycles through features containing infinite values
    # variable i to adress numpy elements
    i = -1
    for column in linf:
        i = i+1
        
        if (not time and verbose):
            # checks infinite values and returns table containing True or False for each feature
            Inftable = np.isinf(dataset[column])
            print('\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION: cleanInf, feature:',column,' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
            print('\nColumn:\n', column)
            print('\nInfinite, table:\n',Inftable)
            print('\nInfinite, table length:\n',len(Inftable))
            if (not time): input('\n{VERBOSE} press ENTER to continue...\n')   
        
        if (verbose and not time): print('\n{LOOP OUTPUT} feature:',column,'\nrow-numbers matching Infinite:')
        # cycling through all rows
        for j in range(0,dataset.shape[0]):
            if dataset[column][j] == float('inf'):
                iindex.append(j)
                if (verbose and not time):
                    print(j)
        # create temporary array from index list
        tmp = np.array(iindex)
        infRows.append(tmp)
        # reset index list
        iindex=[]
    
    # replace cells containing Infinite values with e.g. mean values of that feature
    if iinf:
        i=-1
        for column in linf:
            i = i+1
            # use when you want to calculate mean, std or any value based on the non-infinite cells of the feature
            #tmp = removeCells(dataset,column,infRows[i],verbose,False)
            #replace = tmp.mean()
            replace = 0
            writeCells(dataset,column,infRows[i],replace,verbose,time)
            if verbose:
                print('\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION: cleanInf, replaced feature:',column,' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
                print('\n Replacement:',replace,'\n\n')
                if (verbose and not time): print('\n{LOOP OUTPUT} feature:',column,'\nreplacement-values of each row:')
                for j in infRows[i]:
                    print(dataset[column][j])
                print('\nTotal:',len(infRows[i]))
                if (not time): input('\n{VERBOSE} press ENTER to continue...\n')
        
    else: 
        print('\n{INFO} no infinite values found!\n\n')
        return
    
    if time: end = timer()
         
    if verbose:
        print('\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION: cleanInf, summary ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        #poptions()
        #print('\n\nMaximum, type:\n',type(vmax))
        #print('\nMaximum, values:\n',vmax)
        #resetpoptions()
                
        if iinf:
            i=-1
            for column in linf:
                i = i +1
                print('\n\n',column)
                print('\nRows:\n', infRows[i])
                print('\nTotal:\n', len(infRows[i]))
            if (not time): input('\n{VERBOSE} press ENTER to continue...\n')
  
    if time: print('\ncleanInf\n{TIME}: %.3f' % (end-start),'seconds')
  
    # return whatever needed for method to clean specific cells or drop features    
    return

# clean NaN values with replacement
def cleanNaN(dataset,verbose=False,time=False):
    
    if not (verbose or time): print('\n...applying function cleanNaN\n')
    
    if time: start = timer()
    
    # get summary for NaN values
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
    
    # get row-number for NaN values
    # initialise empty list
    iindex=[]   
    # empty list to fill with numpy arrays containing the row numbers for infinite values
    NaNRows=[]
    NaNtable=[]

    # cycles through features containing NaN values
    # variable i to adress index-elements
    i = -1
    for column in lNaN:
        i = i+1
        # iterates through all rows of columns containing NaNs, returns table with 'True' or 'False' per row per feature
        NaNtable = dataset[column].isnull()
        
        if (verbose and not time):
            # checks infinite values and returns table containing True or False for each feature
            print('\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION: cleanNaN, feature:',column,' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
            print('\nColumn:\n', column)
            print('\nNaN, table:\n',NaNtable)
            print('\nNaN, table length:\n',len(NaNtable))
            if (not time): input('\n{VERBOSE} press ENTER to continue...\n')   
        
        if (verbose and not time): print('\n{LOOP OUTPUT} feature:',column,'\nrow-numbers matching NaN:')
        # cycling through all rows
        for i in range(0,dataset.shape[0]):
            if NaNtable[i] == True:
                iindex.append(i)
                if (verbose and not time):
                    print(i)
        # create temporary array from index list
        tmp = np.array(iindex)
        NaNRows.append(tmp)
        # resed index list
        iindex=[]
    
    # replace cells containing NaN values with e.g. mean values of that feature
    if iNaN:
        i=-1
        for column in lNaN:
            i = i+1
    
            replacement = 0
            
            # alternative, get features cells without NaN values for further calculation or replacement
            #tmp = removeCells(dataset,column,NaNRows[i],verbose,False)
            #replacement = tmp.mean()
            
            writeCells(dataset,column,NaNRows[i],replacement,False,time)
            if verbose:
                print('\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION: cleanNaN, replaced feature:',column,' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
                print('\n Replacement:',0,'\n\n')
                if (verbose and not time): print('\n{LOOP OUTPUT} feature:',column,'\nreplacement-values of each row:')
                for j in NaNRows[i]:
                    print(dataset[column][j])
                print('\nTotal:',len(NaNRows[i]))
                if (not time): input('\n{VERBOSE} press ENTER to continue...\n')
    else: 
        print('\n{INFO} no NaN values found!\n\n')
        return
    
    if time: end = timer()
    
    if verbose:
        print('\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION: cleanNaN, summary ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        #poptions()
        print('\n\nNaN, type:\n',type(vNaN))
        print('\nNaN, values:\n',vNaN)
        #resetpoptions()
        i=-1
        for column in lNaN:
            i = i +1
            print('\n\n',column)
            print('\nRows:\n', NaNRows[i])
            print('\nTotal:\n', len(NaNRows[i]))
        if (not time): input('\n{VERBOSE} press ENTER to continue...\n')
    
    if time: print('\ncleanNaN\n{TIME}: %.3f' % (end-start),'seconds')
      
    return

# drop rows containing only NaNs
def cleanNaNrows(dataset,verbose=False,time=False):
    
    return

# clean String values
def cleanString(dataset,verbose=False,time=False):

    if not (verbose or time): print('\n...applying function cleanString\n')
    if time: start = timer()

    # get table containgin object-types per feature
    stype = dataset.dtypes
    
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
    
    if (not istr):
        print('\n{INFO} no Strings found!\n\n')
        return
        
    # remove features containing string from dataset
    # maybe extract before doing that
    removeFeatures(dataset,lstr,verbose,time)
    
    if time:
        end = timer()
    
    if verbose:
        print('\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION: cleanString, summary ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')    
        print('\nTable:', stype)
        print('\nIndex:\n',istr)
        print('Features:\n',lstr)
        print('Total:\n',len(istr))
        if (not time): input('\n{VERBOSE} press ENTER to continue...\n')
    
    
    if time: print('\ncleanString\n{TIME}: %.3f' % (end-start),'seconds')
    
    return

# clean single-value-features since they gain no information to any model
def cleanSingleValue(dataset,verbose=False,time=False):
    
    if not (verbose or time): print('\n...applying function cleanSinglevalue\n')
    if time: start = timer()
    
    ldrop = []
    counts = dataset.nunique()
    labels = dataset.columns.values
    
    if verbose: 
        print('\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION: cleanSingleValue ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print('\n{LOOP OUTPUT} features containing single unique value:')
    for i in range(0,len(counts)):
        if counts[i] == 1:
            if (verbose and not time): print(i,labels[i])
            ldrop.append(labels[i])
    
    if ldrop:
        removeFeatures(dataset,ldrop,verbose,time)
    else:
        print('\n{INFO} no features with a single unique value found!\n\n')
        return
    
    if time: end = timer()
        
    
    if verbose:
        poptions()
        print('\nCounts:\n',counts)
        resetpoptions()
        print(counts.shape)
        if (not time): input('\n{VERBOSE} press ENTER to continue...\n') 
    
    if time: print('\ncleanSingleValue\n{TIME}: %.3f' % (end-start),'seconds')
    
    return


# REMOVE/EXTRACT FEATURES based on given list
# save features from given list, drop everything else
def saveFeatures(dataset,features,verbose=False,time=False):
    
    if not (verbose or time): print('\napplying function saveFeatures\n')
    
    if time: start = timer()
    
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
    
    # create list of indexes from features to save
    isave = index.copy()
    isave.reverse()
    
    # remove features to save from drop (labels & index)
    for x in isave:
        ldrop = np.delete(ldrop, x)
        idrop = np.delete(idrop, x)
    # drop features from dataset
    dataset.drop(axis=1,labels=ldrop,inplace=True)    
    
    '''
    #convert numpy array to list, to be able to use with df.drop()
    idroplist = idrop.tolist()
    '''
    
    if time: end = timer()
    
    if verbose:
        print('\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION: saveFeatures, save ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print('\nTotal:\n', len(features))
        print('\nLabels:\n', features)
        if index: print('\nIndexes:\n', index)
        else: 
            if not time: input('\n{INFO} features not found!\n')
            return
        
        print('\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION: saveFeatures, remove ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print("\nTotal:\n", len(ldrop))
        #print("\nColumns, Element:\n",columns.item(2))
        print("\nLabels:\n", ldrop)
        print('\nIndexes:\n', idrop)
        
        '''
        print('\nKeep, Labels:\n',keep)
        print('\nKeep, Indexes:\n',indexes)
        print('\nDrop, Type:\n',type(columns))
        print('\nDrop, Labels:\n',columns)
        '''
        if (not time): input('\n{VERBOSE} press ENTER to continue...\n')
        printdata(dataset,'FUNCTION: saveFeatures, cleaned',verbose)
    
    if time: print('\nsaveFeatures\n{TIME}: %.3f' % (end-start),'seconds')        
        
    return

# remove features from given list of feature-labels
def removeFeatures(dataset,features,verbose=False,time=False):
    
    if not (verbose or time): print('\n...applying function removeFeatures\n')
    
    if time: start = timer()
    
    # drop features to remove directly from dataset
    dataset.drop(axis=1,columns=features,inplace=True)
    
    if time: end = timer()
    
    if verbose:
        print('\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION: removeFeatures, remove ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print('\nTotal:\n', len(features))
        print('\nLabels:\n', features)
        if not time: input('\n{VERBOSE} press ENTER to continue...\n')
        '''
        print('\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION: removeFeatures, cleaned ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print('\nType:',type(dataset))
        print('\nShape:',dataset.shape)
        '''
        if dataset.empty: print('\n{INFO} empty dataset!\n')
    
    if time: print('\nremoveFeatures\n{TIME}: %.3f' % (end-start),'seconds')

    return    

# move given list of features into new dataframe
def extractFeatures(dataset,features,verbose=False,time=False):
    
    if not (verbose or time): print('\n...applying function extractFeatures\n')
    
    if time: start = timer()
    
    # create a new datframe from given dataset and list of features to extract
    # original dataset still keeps those features, use removeFeatures to delete those if necessary
    new=dataset[features].copy()
    
    if time: end = timer()
    
    if verbose:
        print('\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION: extractFeatures, extract ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        # if single string is passed len(features) returns number of characters, so check if features is a list
        if type(features) is list: print('\nTotal:\n', len(features))
        print('\nLabels:\n',features,'\n')
        print('\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION: extractFeatures, summary ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print('\nOriginal, type:\n',type(dataset))
        print('\nOriginal:\n',dataset)
        print('\nExtracted, type:\n',type(new))
        print('\nExtracted:\n',new)
        if (not time): input('\n{VERBOSE} press ENTER to continue...\n')
    
    if time: print('\nextractFeatures\n{TIME}: %.3f' % (end-start),'seconds')
    
    return new


# REMOVE/MANIPULATE CELLS 
# manipulate content of specific cells based on list of features and row numbers
def writeCells(dataset,feature,cells,content,verbose=False,time=False):
    
    if not (verbose or time): print('\n...applying function writeCell\n')
    if time: start = timer()
    
    for j in cells:
        dataset.at[j,feature] = content
    
    if time: end = timer()
    
    if verbose:
        #i = -1
        #for column in features:
        #i = i +1
        print('\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION: writeCell, feature:',feature,' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print('\nReplacement:\n',content,'\n')
        # output content of every features/cells given as argument
        if (verbose and not time): print('\n{LOOP OUTPUT} feature:',feature,'\nrow-numbers for replacement:')
        for j in range(0,len(cells)):
            #print('Row:', cells[j],'Value:',dataset[feature][cells[j]])
            print(cells[j])
        print('\nTotal:', len(cells))
        if (not time): input('\n{VERBOSE} press ENTER to continue...\n')
    
    if time: 
        print('\nwriteCells\n{TIME}: %.3f' % (end-start),'seconds')
    
    return

# remove given cells from feature and return this features remaining cells for further calulations
def removeCells(dataset,feature,cells,verbose=False,time=False):
    
    if not (verbose or time): print('\n...applying function removeCells\n')
    
    # copy extracted features into new dataframe
    tmp = extractFeatures(dataset,feature,False)
    
    if verbose:
        print('\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION: removeCells, feature:',feature,' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print('\nInput:\n')
        #print(type(tmp))
        #print(tmp.shape[0])
        print(tmp.describe())
    
    # drop cells
    tmp.drop(axis=0,index=cells,inplace=True)
    
    if verbose:
        print('\nOutput:\n')
        #print(type(tmp))
        #print(tmp.shape[0])
        print(tmp.describe())
        print('\nRemoved cells:', len(cells),'\n')
        if (not time): input('\n{VERBOSE} press ENTER to continue...\n')
       
    return tmp


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


# PROCESS FLOWS
# returns list of features that contains multiple packet-values based on feature-keyword
def perpacketFeatures(dataset,keyword,verbose=False,time=False):
    
    # get all features from given dataset
    features = dataset.columns
    # temporary list of features that match given keyword
    tmp = []
    
    if verbose:
        print('\n'+40*'~'+' FUNCTION: perpacketFeatures, all features '+40*'~')
        print('\n',features)
    
    print('\n'+40*'~'+' FUNCTION: perpacketFeatures, comparison '+40*'~')
    for feature in features:
        print(feature)
        if feature[0:len(keyword)] == keyword:
            print('MATCH\n')
            tmp.append(feature)
        else:
            print('...discarded\n')
    
    if verbose:
        print('\n'+40*'~'+' FUNCTION: perpacketFeatures, summary '+40*'~')
        print('\nper-packet features:\n', tmp)
        if (not time): input('\n{VERBOSE} press ENTER to continue.')
            
    return tmp

# TODO: improve speed? pretty slow
# convert single string or single integer (given with go-flows accumulate function or after NaN cleaning) into list of integers
# necessary to get the values as list of integers for sampling and calculations
def convertToList(dataset,features,verbose=False,time=False):
    
    for feature in features:
        
        if verbose and not superverbose:
            print('\n\n'+40*'~'+' FUNCTION: convertToList: {} '.format(feature)+40*'~')
            print('>>> processing...')  
        
        for i in range(0,len(dataset.index)):
            if superverbose:
                print('\n'+20*'~'+' FUNCTION: convertToList: {}, row: {}/{} '.format(feature,(i+1),len(dataset.index))+20*'~')
                print('original:\n', dataset[feature][i])
                print('type:\n', type(dataset[feature][i]))
            
            # remove first and last character of the string (basically the brackets)
            if type(dataset[feature][i])==str: 
                dataset.at[i,feature] = dataset[feature][i][1:len(dataset[feature][i])-1]
                # convert strings to integers, use whitespace as separator, saves as list
                dataset.at[i,feature] = [int(s) for s in dataset[feature][i].split(' ')]
            # consider single integers (like replacements for NaNs)
            elif type(dataset[feature][i]==int):
                # store value as list-element
                dataset.at[i,feature] = [dataset[feature][i]]
            # output warning for other cases
            else:
                print('\n[WARNING] feature {} has wrong data-type!'.format(feature))
                if (not time): input('\n{PAUSE} press ENTER to continue.')
            
            if superverbose:
                print('transformed:\n', dataset[feature][i])
                print('type:\n', type(dataset[feature][i]))
        
    
    if verbose and (not time): input('\n{VERBOSE} press ENTER to continue.')
            
    return

# sample first and every n-th package afterwards from given list of features
def flowSampling(dataset,n,features,mode=0,verbose=False,time=False):
    
    samplingmode = {0: 'every {}-th packet'.format(n), 1: 'sample & skip {} packets'.format(n), 2: 'sample first {} packets of a flow'.format(n), 3: 'sample n, skip n-1, sample n-2 ... (n={})'.format(n)}
    
    # temporary list for sampling
    tmp = [] 
    
    # iterate over list of given features
    for feature in features:
        
        if verbose and not superverbose:
            print('\n'+40*' '+' SAMPLING: {} '.format(samplingmode[mode]))  
            print(40*'~'+' FUNCTION: flowSampling: {} '.format(feature)+40*'~')
            print('>>> processing...')
        
        # iterate over every single row of the feature
        for i in range(0,len(dataset.index)):
            # list to collect packets to sample, has to be reset for every row iteration
            psample = []
            
            if superverbose:
                print('\n\n'+40*' '+' SAMPLING: {} '.format(samplingmode[mode]))
                print(40*'~'+' FUNCTION: flowSampling: {}, row: {}/{} '.format(feature,(i+1),len(dataset.index))+40*'~')
                print('\nOriginal:')
                print(len(dataset[feature][i]))
                print(dataset[feature][i])

            # mode 0: sample every n-th packet of the flow (including first packet)
            if mode == 0:
                dataset.at[i,feature] = dataset[feature][i][0::n]
                
                if superverbose:
                        print('\nSampled:')
                        print(len(dataset[feature][i]))
                        print(dataset[feature][i])
                        input('\n{SUPERVERBOSE} press ENTER to continue.')
            
            # mode 1: sample n packets, skip n packets...
            elif mode == 1:
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
            elif mode == 2:
                dataset.at[i,feature] = dataset[feature][i][0:n]
                
                if verbose:
                        print('\nSampled:')
                        print(len(dataset[feature][i]))
                        print(dataset[feature][i])
        
            # mode 3: sample n, skip n-1, sample n-2, skip n-3... packets of the flow
            elif mode == 3:
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
            input('\n{SUPERVERBOSE} press ENTER to continue.')
    
    if verbose and (not superverbose) and (not time):
        input('\n{VERBOSE} press ENTER to continue.')
    
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
        print('\n\n\n'+40*'~'+' FUNCTION: packetOutput '+40*'~')
        print('\npacket-list, length:\n{}'.format(len(plist)))
        print('\npacket-list, content:\n{}'.format(plist))
        print('\npacket-list, formatted:\n{}'.format(tmp))
        if not time: input('\n{VERBOSE} press ENTER to continue.')
    
    return tmp


if __name__ == '__main__':
    
    global verbose 
    global time
    global check
    
    #sys.stdout = open("FlowSamplingOutput.txt","w")
    
    verbose = args.verbose
    superverbose = args.superverbose
    if superverbose:
        verbose = True
    time = args.time   
    
    mode = args.mode[0]
    findex = args.file[0]
    n = args.n[0]
    
    windows = args.windows
    osx = args.osx
    check = args.check
    
    # get working directory
    wd = os.getcwd()
    
    if time: start = timer()
    
    # TODO: make list for all necessary PCAP files from dataset
    # TODO: use argument parsing to select sampling-mode from command line
    # TODO: save flow-based sampled CSV into folder csvpath for further classification
    
    # IMPORT PCAP
    
    # OSX
    if osx:
        # paths to pcap & CSV files
        pcap = "/Users/drone/shared/Patrick/BSc/sample.pcap"
        # path to sample pcap file for editcap (copy of original pcap file, created in function packetSampling)
        epcap = "/Users/drone/shared/Patrick/BSc/editsample.pcap"
        # path to JSON configuration file
        json = "/Users/drone/shared/Patrick/BSc/go-flows/examples/custom_accumulate.json"
        # path to extracted flows CSV creatd with go-flows
        path = "/Users/drone/shared/Patrick/BSc/output_accumulate.csv"
        # path to extracted flows CSV creatd with go-flows
        epath = "/Users/drone/shared/Patrick/BSc/eoutput_accumulate.csv"
    
    
        # commands to execute go-flows, capinfos and editcap
        # capinfo command to obtain total packet count
        capinfos = "capinfos -M -c editsample.pcap | grep packets | awk '{print $4}'"
        # editcap command
        editcap = "editcap editsample.pcap tmp.pcap "
        # path to go-flows with arguments to run go-flows within the python script
        goflows = "/Users/drone/shared/Patrick/BSc/go-flows/go-flows run features /Users/drone/shared/Patrick/BsC/go-flows/examples/custom_accumulate.json export csv output_accumulate.csv source libpcap sample.pcap"
        # path to go flows with argument to run for packet-sampled pcap
        egoflows = "/Users/drone/shared/Patrick/BSc/go-flows/go-flows run features /Users/drone/shared/Patrick/BsC/go-flows/examples/custom_accumulate.json export csv eoutput_accumulate.csv source libpcap editsample.pcap"
    
    # Windows 10
    if windows:
        # PATH TO FOLDERS
        # https://www.unb.ca/cic/datasets/ids-2017.html
        # folder containing unedited capture files of used dataset
        fpath = r"D:\CIC-IDS2017\PCAP"
        # list of PCAP files in above folder:
        fname = ["Monday-WorkingHours.pcap","Tuesday-WorkingHours.pcap","Wednesday-WorkingHours.pcap","Thursday-WorkingHours.pcap","Friday-WorkingHours.pcap"]
        # list of PCAP files after dropping payload
        snapname = ["Monday-WorkingHours.pcap","Tuesday-WorkingHours.pcap","Wednesday-WorkingHours.pcap","Thursday-WorkingHours.pcap","Friday-WorkingHours.pcap"]
        # folder containing split capture files
        splitpath = r"D:\CIC-IDS2017\PCAP\splitPCAP"
        # folder containing PCAPS with dropped payload
        snappath = r"D:\CIC-IDS2017\PCAP\snapPCAP"
        # folder containtin splits
        splitpath = r"D:\CIC-IDS2017\PCAP\splitPCAP"
        # folder containting sampled pcaps
        samplepath = r"D:\CIC-IDS2017\PCAP\sampledPCAP"
        # folder containing unlabeled CSV
        csvpath = r"D:\CIC-IDS2017\PCAP\flow-sampledCSV"
        # name for splitted files
        splitname = ["Monday-WorkingHours_split.pcap","Tuesday-WorkingHours_split.pcap","Wednesday-WorkingHours_split.pcap","Thursday-WorkingHours_split.pcap","Friday-WorkingHours_split.pcap"]
        # name for sampled files
        samplename = ["Monday-WorkingHours_sampled.pcap","Tuesday-WorkingHours_sampled.pcap","Wednesday-WorkingHours_sampled.pcap","Thursday-WorkingHours_sampled.pcap","Friday-WorkingHours_sampled.pcap"]
        # name for sampled, unlabeled CSVs
        csvname = ["Monday-WorkingHours_unlabeled.csv","Tuesday-WorkingHours_unlabeled.csv","Wednesday-WorkingHours_unlabeled.csv","Thursday-WorkingHours_unlabeled.csv","Friday-WorkingHours_unlabeled.csv"]
        # filename used for labeling.py
        labelingname = ["Monday-WorkingHours","Tuesday-WorkingHours","Wednesday-WorkingHours","Thursday-WorkingHours","Friday-WorkingHours"]
        
        # PATH TO TOOLS
        # capinfos path
        capinfospath = r'"C:\Program Files\Wireshark\capinfos.exe"'
        # editcap command
        editcappath = r'"C:\Program Files\Wireshark\editcap.exe"'
        # mergecap
        mergecappath = r'"C:\Program Files\Wireshark\mergecap.exe"'
        # goflows
        goflowspath = r"D:\go-flows-master\go-flows.exe"
        # go flow JSON configuration file
        # https://github.com/CN-TU/Datasets-preprocessing/blob/master/CIC-IDS-2017/flow_specifications/CAIA.json
        goflowsconf = "{}".format(wd)+"\\go-flows-configurations\CAIA_flowSampling.json"
        # labeling.py script
        labelingpath = r"labeling.py"
    
    
    # forged file-paths  
    pcap = fpath+"\\"+fname[findex]
    unlabeledcsv = fpath+"\\"+csvname[findex]
    sampledcsv = "{}".format(csvpath)+"\\"+csvname[findex]
    labeledcsv = "{}".format(csvpath)+"\\"+labelingname[findex]+".csv"
    
    # forged command to convert sampled PCAP into (per-packet) CSV for Classification
    goflowscmd = "{}".format(goflowspath)+" run features "+"{}".format(goflowsconf)+" export csv "+"{}".format(fpath)+"\\"+"{}".format(csvname[findex])+" source libpcap "+"{}".format(fpath)+"\\"+"{}".format(fname[findex])
    labelingcmd = "python "+"{}".format(labelingpath)+" "+"{}".format(csvpath)+"\\"+labelingname[findex]+" 5tuple"
    
    # check passed optional arguments, filepaths and forged commands
    if verbose:
        print('\n\n'+40*'~'+' SCRIPT: FlowSampling, optional arguments '+40*'~')
        print("\n{}\t--verbose\n{}\t--superverbose\n{}\t--time\n{}\t--osx\n{}\t--windows".format(verbose,superverbose,time,osx,windows))
        print('\n'+20*'~'+' paths & commands, file: {} '.format(pcap)+20*'~')
        print('\nJSON: {}'.format(goflowsconf))
        print('\nCSV (flows): {}'.format(unlabeledcsv)) 
        print('CSV (sampled): {}'.format(sampledcsv))
        print('CSV (labeled): {}'.format(labeledcsv))
        
        print("\n\ngo-flows command: {}".format(goflowscmd))
        print("labeling command: {}".format(labelingcmd))
        if not time: input('\n[VERBOSE] press ENTER to continue.') 

    
    # FLOW-CREATION & LABELING
    
    # execute go-flows to process passed PCAP file
    print("\n>>> create flow-CSV from PCAP with go-flows...")
    os.system(goflowscmd)
    
    # import output CSV from go-flows
    #poptions()
    dataset = importCSV(unlabeledcsv,None,verbose)
    
    if verbose:
        printdata(dataset,'go-flows CSV',verbose)
        if not time: input('\n[VERBOSE] press ENTER to continue.') 
    
    
    # SAMPLING (flow-based)
        
    # get list of all features contained in dataset
    features = dataset.columns
    # get list of accumulated perpacket-features that have to be sampled
    features = perpacketFeatures(dataset,'apply(accumulate',verbose,time)
    # convert content of perpacket-features into an actual list for further processing
    convertToList(dataset,features,verbose,time)
    # sample perpacket-features
    flowSampling(dataset,n,features,mode,verbose,time)
    
    # CALCULATIONS
    # TODO: should do more than this, e.g. min, max, stdev...
    # calculate mean of remaining packet values after sampling
    
    if verbose: 
        print('\n\n'+20*'~'+' Calculation, mean '+20*'~')
        
    for feature in features:
        for i in range(0,len(dataset.index)):
            dataset.at[i,feature] = sum(dataset[feature][i])/len(dataset[feature][i])
            
        if verbose: 
            print('\n')
            print(dataset[feature])
            if not time: input('\n[VERBOSE] press ENTER to continue.') 
        
    if verbose:
        printdata(dataset,'SAMPLED',verbose)
        if not time: input('\n[VERBOSE] press ENTER to continue.')
    
    # save dataframe as CSV for further preprocessing & classification
    print("\n>>> save data to CSV...")
    dataset.to_csv(sampledcsv, index=False)
    
    # label flow-based sampled CSV as last step of preparation for further classification
    print("\n>>> label flow-CSV...")
    os.system(labelingcmd)
    
    if time: 
        end = timer()
        print('\n[TOTAL TIME, FlowSampling.py]: %.3f' % (end-start),'seconds')
    
    if (not time): input('\n[QUIT] press ENTER to quit.')  
    exit()
    
    #sys.stdout.close()
    
    
    
    
    
    
    
     
    
    

    
    
   
    
   
    