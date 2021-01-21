#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 21 13:24:18 2021

@author: pjr
"""

from pandas import read_csv
from pathlib import Path, PureWindowsPath

import pandas as pd
import numpy as np


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


# working directory
wd = Path.cwd()
# logs
logd = wd / 'logs'
#logd = wd / 'rpi-logs'
reportcsv = logd / 'report.csv'
resultcsv = logd / 'result.csv'
timecsv = logd / 'time.csv'
dstatcsv = logd / 'dstat.csv'

if __name__ == '__main__':

    pd.set_option('display.float_format', lambda x: '%.5f' % x) # force float output for epoch time

    # IMPORT
    timestamps = read_csv(timecsv,delimiter=',',encoding='utf-8')
    print(timestamps)
    
    dstat = read_csv(dstatcsv,delimiter=r'[,\t]',header=5,encoding='utf-8')
    print(dstat)

    report = read_csv(reportcsv,delimiter=',',encoding='utf-8')
    print(report)

    result = read_csv(resultcsv,delimiter=',',encoding='utf-8')
    print(result)

    accuracyscore = float(result['summary'][2])
    print('\n{}'.format(accuracyscore))
    print(type(accuracyscore))

    matrix = result['summary'][4]
    print('\n\n{}\n'.format(matrix))

    # get actual numbers from saved confusion-matrix
    matrix = matrix.replace('\n',r'').replace('[',r'').replace(']',r'') # remove unnecessary characters

    s=''
    npmatrix = np.empty(shape=[0,4])
    index = 0
    for string in matrix.split():
    	index += 1
    	for character in string:
    		if character.isdecimal():
    			s += character
    	#print('{}: {} {}'.format(index,type(s),s))
    	if s.isdigit(): 
    		i = int(s)
    		npmatrix = np.append(matrix,i,axis=1)
    		#print('{}: {} {}'.format(index,type(i),i))
    	s = ''

    print(npmatrix)
    exit()