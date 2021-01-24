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
from math import pi


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

# ARGUMENT PARSING
# command line argument passthrough for better usability
import argparse
parser = argparse.ArgumentParser(description='script for preprocessing labeled CSVs')
# optional arguments
parser.add_argument('-v','--verbose', action='store_true', help='output additional informations')
args = parser.parse_args()



if __name__ == '__main__':

    pd.set_option('display.float_format', lambda x: '%.5f' % x) # force float output for epoch time
    verbose = args.verbose



    # IMPORT TIMESTAMPS & DSTAT LOGS
    # sampling information
    info = read_csv(infocsv,delimiter=',',encoding='utf-8')
    print('\n\n'+20*'~'+' information.csv '+20*'~')
    print('\n{}\n'.format(info))
    input('...')

    # timestamps
    times = read_csv(timecsv,delimiter=',',encoding='utf-8')
    print('\n\n'+20*'~'+' times.csv '+20*'~')
    print('\n{}\n'.format(times))
    timef = list(times) # features from time.csv
    print('\n{}\n'.format(timef))
    input('...')

    # dstat system-resource logging
    dstat = read_csv(dstatcsv,delimiter='[,\t]',header=5,encoding='utf-8',engine='python')
    print('\n\n'+20*'~'+' dstat.csv '+20*'~')
    print('\n{}\n'.format(dstat))
    input('...')

    print('\n>>> unique feature-content:')
    for i in range (2,len(timef)):
        print('\n{}:\n{}'.format(timef[i],times[timef[i]].unique()))

    if verbose:
        segments = times[timef[2]].unique() # segments contained in time.csv
        print('\nsegments:\n{}\n'.format(segments))
        for segment in segments: # get df only containing specific segments
            print(segment)
            tmp = times[times['segment'] == segment]
            print(tmp)
            # get row numbers to determine start/end timestamps for segments



    # PRE-PROCESS
    # set starting time to 0
    startepoch = times['epochtime'][0]
    times['epochtime'] = times['epochtime'].subtract(startepoch) # modify times
    dstat['"epoch"'] = dstat['"epoch"'].subtract(startepoch)
   # get script-usage timestamps
    mainStart = times['epochtime'].iloc[0] # first row
    mainEnd = times['epochtime'].iloc[-1]+1 # last row, add one second to see the usage after scripts ending
    runtime = 100* (mainEnd - mainStart)/(mainEnd - mainStart) # to get value between 0 and 100 for spider chart

    # timestamps for starting segments
    importCSVstart = times['epochtime'][1]
    StandardScaler_fit_start = times['epochtime'][3]
    Split_start = times['epochtime'][5]
    StandardScaler_Transform_Xtrain_start = times['epochtime'][7]
    StandardScaler_Transform_Xtest_start = times['epochtime'][9]
    PCA_fit_transform_start = times['epochtime'][11]
    PCA_transform_Xtest_start = times['epochtime'][13]
    RandomForest_start = times['epochtime'][15]
    Predictions_start = times['epochtime'][17]

    # dump all dstat values outside of script duration
    dstat = dstat[(dstat['"epoch"'] >= mainStart) & (dstat['"epoch"'] <= mainEnd)]

    # get list of dstat features from dstat.csv
    dstatf = list(dstat)
    print('\ndstat features:\n{}'.format(dstatf))

    # example to isolate dstat values from specific segments
    importCSVdstat = dstat[(dstat['"epoch"'] >= importCSVstart) & (dstat['"epoch"'] <= StandardScaler_fit_start)]
    if verbose: print('\nimportCSV:\n{}'.format(importCSVdstat))

    # convert bytes to megabytes for better readability
    dstat['"used"'] = dstat['"used"'].divide(1024**2)
    dstat['"total"'] = dstat['"total"'].divide(1024**2)
    dstat['"cach"'] = dstat['"cach"'].divide(1024**2)
    dstat['"free"'] = dstat['"free"'].divide(1024**2)



    # IMPORT CLASSIFICATION REPORT & RESULTS
    report = read_csv(reportcsv,delimiter=',',encoding='utf-8')
    print('\nClassification-Report:\n{}'.format(report))
    result = read_csv(resultcsv,delimiter=',',encoding='utf-8')
    print('\nClassification-Results:\n{}'.format(result))
    accuracyscore = float(result['summary'][2])
    print('\nAccuracy-Score:\n{}'.format(accuracyscore))
    matrix = result['summary'][4]
    print('\nConfusion-Matrix:\n{}'.format(matrix))

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
    print('{}\n{}\n\n'.format(npmatrix,type(npmatrix)))



    # SPIDER CHART
    # get stats between 0 and 100 for all values we want to show in our spider-chart
    # for the thesis we want to e.g. take the longest runtime as 100% and show all other runtimes dependent on that value
    maxRAM = dstat['"used"'].max()
    maxCPU = dstat['"usr"'].max()
    percentRAMused = dstat['"used"'].max()/dstat['"total"'].max()*100
    percentRAMcached = dstat['"cach"'].max()/dstat['"total"'].max()*100
    percentaccuracy = accuracyscore*100

    recall0 = report['recall'][0]*100
    recall1 = report['recall'][1]*100
    precision0 = report['precision'][0]*100
    precision1 = report['precision'][1]*100

    ax = plt.subplot(polar=True)

    # forge polar-compatible values and angles
    values = [percentRAMused,percentRAMcached,maxCPU,percentaccuracy,recall0,precision0,recall1,precision1,runtime]

    N = len(values) # number of different parameters shown in spider-chart
    if verbose: print('Parameter-Values:\n{}\n'.format(values))
    values += values[:1] # close value "circle" for sider-chart

    angles = [n / float(N) * 2 * pi for n in range(N)]
    if verbose: print('Parameter-Angles:\n{}\n'.format(angles))
    angles += angles[:1] # close angle "circle" for spider-chart

    plt.polar(angles,values)

    # label parameters
    stats = ['RAM\nused','RAM\ncached','CPU\nused','Accuracy','Recall\n"0"','Precision\n"0"','Recall\n"1"','Precision\n"1"','Runtime']
    plt.xticks(angles[:-1],stats) # pass angles but last (repetition of first value)
    # label value-axis position,ticks and limit
    ax.set_rlabel_position(60)
    plt.yticks([0,25,50,75,100], color='grey', size=10)
    plt.ylim(0,100)

    plt.show()



    # SIMPLE GRAPHS
    # html color-codes from https://htmlcolorcodes.com/

    # RAM USAGE in MB, all parameters in one single diagram
    plt.plot(dstat['"epoch"'],dstat['"total"'],color = '#000000',label='total')
    plt.plot(dstat['"epoch"'],dstat['"used"'],color = '#566573',label='used')
    plt.plot(dstat['"epoch"'],dstat['"cach"'],color = '#AEB6BF',label='cached')
    plt.legend(loc='best')
    plt.show()

    # RAM USAGE, separate diagrams for every parameter
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
    plt.axvline(x=RandomForest_start,ymin=0,ymax=1,label='RandomForest fit')
    plt.axvline(x=Predictions_start,ymin=0,ymax=1,label='Predictions')
    plt.legend(loc='best')
    plt.show()

    exit()