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
logd = wd / 'evaluation'

# initialise empty lists
evaluationd = []
reports = []
results = []
dstats = []
infos = []
times = []
accuracyscores = []
matrices = []
runtimes = []
samplingtypes = []
samplingmodes = []
samplingsteps = []
featurevectors = []

for path in Path(logd).iterdir(): # get all folder-paths for evaluation
    if path.is_dir(): evaluationd.append(path)

print('\n>>> evaluation-data:')
for i in range(0,len(evaluationd)):
    print('\t[{}]: {}'.format(i,evaluationd[i]))

input('...')


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

    # IMPORT TIMESTAMPS & DSTAT LOGS: read different logs into lists
    # sampling information
    for i in range(0,len(evaluationd)):
        infocsv = evaluationd[i] / 'information.csv'
        info = read_csv(infocsv,delimiter=',',encoding='utf-8',index_col=0)
        print('\n\n'+20*'~'+' information.csv '+20*'~')
        print('\n{}\n'.format(info))
        infos.append(info)
    input('...')

    # get informations to label graphs later
    for i in range(0,len(evaluationd)):
        features = infos[i].index.values
        samplingtype = features[1]
        samplingtypes.append(samplingtype) # flow/packet-sampling

        samplingmode = infos[i]['0'][2]
        samplingmodes.append(samplingmode)

        samplingstep = infos[i]['0'][3]
        samplingsteps.append(samplingstep)

        featurevector = infos[i]['0'][4]
        featurevectors.append(featurevector)


    # timestamps
    for i in range(0,len(evaluationd)):
        timecsv = evaluationd[i] / 'logs' / 'time.csv'
        time = read_csv(timecsv,delimiter=',',encoding='utf-8')
        print('\n\n'+20*'~'+' time.csv '+20*'~')
        print('\n{}\n'.format(time))
        timef = list(time) # features from time.csv
        #print('\n{}\n'.format(timef))
        times.append(time)
    input('...')

    # dstat system-resource logging
    for i in range(0,len(evaluationd)):
        dstatcsv = evaluationd[i] / 'logs' / 'dstat.csv'
        dstat = read_csv(dstatcsv,delimiter='[,\t]',header=5,encoding='utf-8',engine='python')
        print('\n\n'+20*'~'+' dstat.csv '+20*'~')
        print('\n{}\n'.format(dstat))
        dstats.append(dstat)
    input('...')

    # time features & segments are the same in all logs to evaluate
    # just take first element in times-list
    print('\n>>> unique feature-content:')
    for i in range (2,len(timef)):
        print('\n{}:\n{}'.format(timef[i],times[0][timef[i]].unique()))

    if verbose:
        segments = times[0][timef[2]].unique() # all segments contained in time.csv
        #print('\nsegments:\n{}\n'.format(segments))
        for segment in segments: # get df only containing specific segments
            print(segment)
            tmp = times[0][times[0]['segment'] == segment]
            print(tmp)
            # get row numbers to determine start/end timestamps for segments


    csvimports = []
    scalersfit = []
    filesplits = []
    scalersxtrain = []
    scalersxtest = []
    pcasfit = []
    pcasxtest = []
    modelsimport = []
    predictions = []

    # PRE-PROCESS
    for i in range(0,len(evaluationd)):
        # set starting time to 0
        startepoch = times[i]['epochtime'][0]
        times[i]['epochtime'] = times[i]['epochtime'].subtract(startepoch) # modify times
        dstats[i]['"epoch"'] = dstats[i]['"epoch"'].subtract(startepoch)

        # get script-usage timestamps
        mainStart = times[i]['epochtime'].iloc[0] # first row
        mainEnd = times[i]['epochtime'].iloc[-1]+1 # last row, add one second to see the usage after scripts ending
        runtime = (mainEnd - mainStart) # to get value between 0 and 100 for spider chart
        runtimes.append(runtime)

        csvimport = times[i].loc[(times[i].segment == 'importCSV') & (times[i].status == 'start')].epochtime.values[0]
        csvimports.append(csvimport)

        scalerfit = times[i].loc[(times[i].segment == 'Standardscaler-fit') & (times[i].status == 'start')].epochtime.values[0]
        scalersfit.append(scalerfit)

        filesplit = times[i].loc[(times[i].segment == 'Split') & (times[i].status == 'start')].epochtime.values[0]
        filesplits.append(filesplit)

        scalerxtrain = times[i].loc[(times[i].segment == 'Scaler-transform-Xtrain') & (times[i].status == 'start')].epochtime.values[0]
        scalersxtrain.append(scalerxtrain)

        scalerxtest = times[i].loc[(times[i].segment == 'Scaler-transform-Xtest') & (times[i].status == 'start')].epochtime.values[0]
        scalersxtest.append(scalerxtest)

        pcafit = times[i].loc[(times[i].segment == 'PCA-fit/transform-Xtrain') & (times[i].status == 'start')].epochtime.values[0]
        pcasfit.append(pcafit)

        pcaxtest = times[i].loc[(times[i].segment == 'PCA-transform-Xtest') & (times[i].status == 'start')].epochtime.values[0]
        pcasxtest.append(pcaxtest)

        modelimport = times[i].loc[(times[i].segment == 'importRandomForest') & (times[i].status == 'start')].epochtime.values[0]
        modelsimport.append(modelimport)

        prediction = times[i].loc[(times[i].segment == 'makePredictions') & (times[i].status == 'start')].epochtime.values[0]
        predictions.append(prediction)





        #print(predictionstart)
        #print(type(predictionstart))
        #input('blbajlkbaj')


        # dump all dstat values outside of script duration
        dstats[i] = dstats[i][(dstats[i]['"epoch"'] >= mainStart) & (dstats[i]['"epoch"'] <= mainEnd)]

    # get list of dstat features from dstat.csv
    dstatf = list(dstats[0])
    print('\ndstat features:\n{}'.format(dstatf))

    # calculate runtimes percentage, based on highest runtime within given data
    maxruntime = max(runtimes)
    percentageruntimes = [100 * x / maxruntime for x in runtimes]

    # convert RAM sizes, bytes to MB
    cfeatures = ['"used"','"total"','"cach"','"free"'] # features to convert
    for i in range(0,len(evaluationd)):
        rows = dstats[i].shape[0] # get number of rows for given df
        for feature in cfeatures: # cycle through list of features
            for row in range(0,rows):
                tmp = dstats[i][feature][row]/1024**2
                dstats[i].at[row,feature] = tmp


    # IMPORT CLASSIFICATION REPORT & RESULTS
    for i in range(0,len(evaluationd)):
        reportcsv = evaluationd[i] / 'logs' / 'report.csv'
        report = read_csv(reportcsv,delimiter=',',encoding='utf-8')
        reports.append(report)
        print('\nClassification-Report:\n{}'.format(reports[i]))

        resultcsv = evaluationd[i] / 'logs' / 'result.csv'
        result = read_csv(resultcsv,delimiter=',',encoding='utf-8')
        results.append(result)
        print('\nClassification-Results:\n{}'.format(results[i]))

        accuracyscore = float(results[i]['summary'][2])
        accuracyscores.append(accuracyscore)
        print('\nAccuracy-Score:\n{}'.format(accuracyscores[i]))

        matrix = result['summary'][4]
        matrices.append(matrix)
        print('\nConfusion-Matrix:\n{}'.format(matrices[i]))

    '''
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
    '''


    # SPIDER CHART
    # get stats between 0 and 100 for all values we want to show in our spider-chart
    # for the thesis we want to e.g. take the longest runtime as 100% and show all other runtimes dependent on that value

    # initialise empty lists for spider-charts generation
    maxRAMs = []
    maxCPUs = []
    percentRAMsused = []
    percentRAMscached = []
    percentaccuracies = []
    recalls0 = []
    recalls1 = []
    precisions0 = []
    precisions1 = []
    values = []

    # SPIDER CHART PLOTS
    for i in range(0,len(evaluationd)):

        # get values from given data
        maxRAM = dstats[i]['"used"'].max()
        maxRAMs.append(maxRAM)

        maxCPU = dstats[i]['"usr"'].max()
        maxCPUs.append(maxCPU)

        percentRAMused = dstats[i]['"used"'].max()/dstats[i]['"total"'].max()*100
        percentRAMsused.append(percentRAMused)

        percentRAMcached = dstats[i]['"cach"'].max()/dstats[i]['"total"'].max()*100
        percentRAMscached.append(percentRAMcached)

        percentaccuracy = accuracyscores[i]*100
        percentaccuracies.append(percentaccuracy)

        recall0 = reports[i]['recall'][0]*100
        recalls0.append(recall0)

        recall1 = reports[i]['recall'][1]*100
        recalls1.append(recall1)

        precision0 = reports[i]['precision'][0]*100
        precisions0.append(precision0)

        precision1 = reports[i]['precision'][1]*100
        precisions1.append(precision1)

        # forge chart-label
        title = '{}\n{} ({}, n={})'.format(featurevectors[i],samplingtypes[i],samplingmodes[i],samplingsteps[i])

        # forge polar-compatible values and angles
        value = [percentRAMsused[i],percentRAMscached[i],maxCPUs[i],percentaccuracies[i],recalls0[i],precisions0[i],recalls1[i],precisions1[i],percentageruntimes[i]]
        N = len(value) # number of different parameters shown in spider-chart
        value += value[:1] # close value "circle" for sider-chart
        values.append(value)
        angles = [n / float(N) * 2 * pi for n in range(N)]
        angles += angles[:1] # close angle "circle" for spider-chart

        ax = plt.subplot(polar=True)
        plt.polar(angles,values[i])

        # label parameters
        stats = ['used RAM\n({}%)'.format(int(percentRAMsused[i])),'cached RAM\n({}%)'.format(int(percentRAMscached[i])),'CPU usage\n({}%)'.format(int(maxCPUs[i])),'Accuracy','Recall\n"0"','Precision\n"0"','Recall\n"1"','Precision\n"1"','Runtime']
        plt.xticks(angles[:-1],stats) # pass angles but last (repetition of first value)
        # label value-axis position,ticks and limit
        ax.set_rlabel_position(60)
        plt.yticks([0,25,50,75,100], color='grey', size=10)
        plt.ylim(0,100)
        plt.title(title)

        plt.show() # print current spider-chart




    # SPIDER CHART COMPARISONS

    ax = plt.subplot(polar=True)
    # for now, manually pick values that should be compared
    plt.polar(angles,values[1],color = '#566573',label='n=5 (packetsampling)')
    plt.polar(angles,values[2],color = '#AEB6BF',label='n=5 (flowsampling)')

    stats = ['used RAM','cached RAM','CPU usage','Accuracy','Recall\n"0"','Precision\n"0"','Recall\n"1"','Precision\n"1"','Runtime']
    plt.xticks(angles[:-1],stats) # pass angles but last (repetition of first value)

    ax.set_rlabel_position(60)
    plt.yticks([0,25,50,75,100], color='grey', size=10)
    plt.ylim(0,100)

    plt.title('every n-th packet\nload model', size='medium')
    plt.legend() # print legend specified as label in plt.polar(...)

    plt.show() # print merged spider chart




    # SIMPLE GRAPHS
    # html color-codes from https://htmlcolorcodes.com/

    '''
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
    '''

    # plot all RAM graphs into single diagram
    for i in range(0,len(evaluationd)):
        title = '{}\n{} ({}, n={})'.format(featurevectors[i],samplingtypes[i],samplingmodes[i],samplingsteps[i])
        plt.plot(dstats[i]['"epoch"'],dstats[i]['"total"'],color = '#000000',label='RAM total')
        plt.plot(dstats[i]['"epoch"'],dstats[i]['"used"'],color = '#566573',label='RAM used')
        plt.plot(dstats[i]['"epoch"'],dstats[i]['"cach"'],color = '#AEB6BF',label='RAM cached')


        plt.axvline(x=predictions[i],ymin=0,ymax=1,label='make Predictions',color='#52FF3A')
        plt.axvline(x=modelsimport[i],ymin=0,ymax=1,label='import Model',color='#4BE936')
        plt.axvline(x=pcasxtest[i],ymin=0,ymax=1,label='PCA transform Xtest',color='#44D331')
        plt.axvline(x=pcasfit[i],ymin=0,ymax=1,label='PCA fit/transform Xtrain',color='#3FC52D')
        plt.axvline(x=scalersxtest[i],ymin=0,ymax=1,label='StandardScaler transform Xtest',color='#39B329')
        plt.axvline(x=scalersxtrain[i],ymin=0,ymax=1,label='StandardScaler transform Xtrain',color='#33A225')
        plt.axvline(x=filesplits[i],ymin=0,ymax=1,label='split files',color='#2E9121')
        plt.axvline(x=scalersfit[i],ymin=0,ymax=1,label='StandardScaler fit Xtrain',color='#287F1C')
        plt.axvline(x=csvimports[i],ymin=0,ymax=1,label='import CSV',color='#216918')


        plt.title(title)
        plt.legend(loc='best')
        plt.show()


    # CPU USAGE
    plt.plot(dstat['"epoch"'],dstat['"usr"'],color = '#000000',label='CPU user')
    #plt.plot(dstat['"epoch"'],dstat['"sys"'],color = '#566573',label='CPU sys')
    #plt.plot(dstat['"epoch"'],dstat['"idl"'],color = '#AEB6BF',label='CPU idle')
    '''
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
    '''
    plt.legend(loc='best')
    plt.show()

    exit()