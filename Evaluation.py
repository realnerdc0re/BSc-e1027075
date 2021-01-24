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
import matplotlib.pyplot as plt


# working directory
wd = Path.cwd()

# logs-folder
logd = wd / 'logs'
#logd = wd / 'logs-rpi'

# files
reportcsv = logd / 'report.csv'
resultcsv = logd / 'result.csv'
timecsv = logd / 'time.csv'
dstatcsv = logd / 'dstat.csv'
infocsv = logd / 'information.csv'

if __name__ == '__main__':

    pd.set_option('display.float_format', lambda x: '%.5f' % x) # force float output for epoch time


    # IMPORTS 
    # sampling information
    info = read_csv(infocsv,delimiter=',',encoding='utf-8')
    print('\n\n'+20*'~'+' information.csv '+20*'~')
    print('\n{}\n'.format(info))
    input('...')


    # times containing following feature-labels: epochtime, scriptname, segment, status
    times = read_csv(timecsv,delimiter=',',encoding='utf-8')
    print('\n\n'+20*'~'+' times.csv '+20*'~')
    print('\n{}\n'.format(times))
    input('...')

    # dstat system-resource logging
    dstat = read_csv(dstatcsv,delimiter='[,\t]',header=5,encoding='utf-8',engine='python')
    print('\n\n'+20*'~'+' dstat.csv '+20*'~')
    print('\n{}\n'.format(dstat))
    input('...')


    timef = list(times) # features from time.csv
    print(timef)

    print('\n>>> content of features:\n')
    for i in range (2,len(timef)):
    	print('\n{}:\n{}\n'.format(timef[i],times[timef[i]].unique()))

    segments = times[timef[2]].unique() # segments
    print('\nsegments:\n{}\n'.format(segments))


    # get df only containing specific segments
    for segment in segments:

    	print(segment)
    	tmp = times[times['segment'] == segment]
    	print(tmp)
    	# get row numbers to determine start/end timestamps for segments


    # set starting time to 0
    startepoch = times['epochtime'][0]
    #importCSVstart = times['epochtime'][1]
    #importCSVstop = times['epochtime'][2]
    times['epochtime'] = times['epochtime'].subtract(startepoch) # modify times
    dstat['"epoch"'][1] = dstat['"epoch"'].subtract(startepoch)


   # get script-usage timestamps
    mainStart = times['epochtime'].iloc[0] # first row
    mainEnd = times['epochtime'].iloc[-1]+1 # last row, add one second to see the usage after scripts ending


    # get CSV import timestamps
    importCSVstart = times['epochtime'][1]
    importCSVstop = times['epochtime'][2]

    # output timestamps
    print(importCSVstart)
    print(importCSVstop)
    print(mainStart)
    print(mainEnd)

    StandardScaler_fit_start = times['epochtime'][3]
    Split_start = times['epochtime'][5]
    StandardScaler_Transform_Xtrain_start = times['epochtime'][7]
    StandardScaler_Transform_Xtest_start = times['epochtime'][9]
    PCA_fit_transform_start = times['epochtime'][11]
    PCA_transform_Xtest_start = times['epochtime'][13]
    RandomForest_start = times['epochtime'][15]


    # dump all dstat data not within mainStart and mainEnd
    dstat = dstat[(dstat['"epoch"'] >= mainStart) & (dstat['"epoch"'] <= mainEnd)]
    dstatf = list(dstat) # features from time.csv
    print(dstatf)


    importCSVdstat = dstat[(dstat['"epoch"'] >= importCSVstart) & (dstat['"epoch"'] <= importCSVstop)]
    print(importCSVdstat)







    # PLOTS (dstat)

    # convert bytes to megabytes
    dstat['"used"'] = dstat['"used"'].divide(1024**2)
    dstat['"total"'] = dstat['"total"'].divide(1024**2)
    dstat['"cach"'] = dstat['"cach"'].divide(1024**2)
    dstat['"free"'] = dstat['"free"'].divide(1024**2)
    #print(dstat['"used"'])

    # COMPLETE PLOTS FROM DSTAT
    # show memory stats in one single plot
    # html color codes from https://htmlcolorcodes.com/


    # RAM USAGE
    plt.plot(dstat['"epoch"'],dstat['"total"'],color = '#000000',label='total')
    plt.plot(dstat['"epoch"'],dstat['"used"'],color = '#566573',label='used')
    plt.plot(dstat['"epoch"'],dstat['"cach"'],color = '#AEB6BF',label='cached')
    plt.legend(loc='best')
    #plt.show()

    '''
    # show memory stats separated
    #dstat.plot(x='"epoch"',y='"cach"','g-',label='cached')
    plt.plot(dstat['"epoch"'],dstat['"used"'],color = '#566573',label='used')
    plt.legend(loc='best')
    plt.show()
    plt.plot(dstat['"epoch"'],dstat['"cach"'],color = '#AEB6BF',label='cached')
    plt.legend(loc='best')
    plt.show()
    #input('plot_all')
    '''

    # plot different windows at once
    dstat.plot(x='"epoch"',y='"used"',color = '#566573',label='used')
    dstat.plot(x='"epoch"',y='"cach"',color = '#AEB6BF',label='cached')
    dstat.plot(x='"epoch"',y='"free"',color = '#D5D8DC',label='free')
    plt.show()


    # CPU USAGE
    plt.plot(dstat['"epoch"'],dstat['"usr"'],color = '#000000',label='CPU user')
    plt.plot(dstat['"epoch"'],dstat['"sys"'],color = '#566573',label='CPU sys')
    plt.plot(dstat['"epoch"'],dstat['"idl"'],color = '#AEB6BF',label='CPU idle')

    # markers for starting time of different script-segments
    plt.axvline(x=importCSVstart,ymin=0,ymax=1,label='CSV import')
    plt.axvline(x=StandardScaler_fit_start,ymin=0,ymax=1,label='Scaler fit')
    plt.axvline(x=Split_start,ymin=0,ymax=1,label='split')
    plt.axvline(x=StandardScaler_Transform_Xtrain_start,ymin=0,ymax=1,label='Scaler transform Xtrain')
    plt.axvline(x=StandardScaler_Transform_Xtest_start,ymin=0,ymax=1,label='Scaler transform Xtest')
    plt.axvline(x=PCA_fit_transform_start,ymin=0,ymax=1,label='PCA fit/transform')
    plt.axvline(x=PCA_transform_Xtest_start,ymin=0,ymax=1,label='PCA transform Xtest')
    plt.axvline(x=RandomForest_start,ymin=0,ymax=1,label='RandomForest fit/predict')

    plt.legend(loc='best')
    plt.show()

    '''
    plt.figure(1)
    plt.subplot(100)
    plt.plot(x=dstat['"epoch"'],y=dstat['"sys"'])
    plt.show()
    '''



    # REPORT & RESULTS

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
    tmp = matrix.replace('\n',r'').replace('[',r'').replace(']',r'') # remove unnecessary characters
    s=''
    npmatrix = np.empty(shape=[0,4]) # initialise empty np array
    index = 0
    for string in tmp.split():
    	index += 1
    	for character in string:
    		if character.isdecimal():
    			s += character
    	if s.isdigit(): 
    		i = int(s)
    		npmatrix = np.append(npmatrix,i)
    	s = ''
    del tmp

    print('{}\n{}'.format(npmatrix,type(npmatrix)))
    exit()