#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 22 12:21:55 2021

@author: pjr
"""

from math import pi
from pandas import read_csv
from pathlib import Path, PureWindowsPath

from itertools import groupby

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import config as cfg

if not os.path.exists(cfg.figures): os.mkdir(cfg.figures)


# ARGUMENT PARSING
import argparse
parser = argparse.ArgumentParser(description='Script to evaluate machine-learning based anomaly detection results.')
parser.add_argument('-v','--verbose', action='store_true', help= 'output verbose information')
parser.add_argument('-p','--plot', action='store_true', help = 'output plots')
args = parser.parse_args()


# initialise empty lists
exp                 = []
flowfolder          = []
packetfolder        = []
experiments_perflow = []
experiments_packets = []

# working directory
#wd = Path.cwd()

# logs-folder
#logd = wd / 'evaluation'

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

# files
#reportcsv = logd / 'report.csv'
#resultcsv = logd / 'result.csv'
#timecsv = logd / 'time.csv'
#dstatcsv = logd / 'dstat.csv'
#infocsv = logd / 'information.csv'



# class object containing all necessary experiment data
class Experiment:
    def __init__(self,fullpath,file,mode,vector,steps,sampling,info,time,dstat,report,result,runtime=0):
        # contains info
        self.fullpath   = fullpath
        self.file       = file
        self.mode       = mode
        self.vector     = vector
        self.steps      = steps
        self.sampling   = sampling

        # contains logs
        self.info       = info
        self.time       = time
        self.dstat      = dstat
        self.report     = report
        self.result     = result

        # calculated values
        self.runtime    = runtime

    def __str__(self):
        return str(self.__class__)+': '+str(self.__dict__)
# extract information from foldername and create objects
def createExperiments(folders,verbose=False):

    for item in folders: # list of folders containing the actual experiment folders

        print('\t>> Reading sub-folders')
        for folder in item: # iterating over sub-folders

            foldername = folder.parts[-1] # returns the current foldername

            if verbose: # output current experiment folders
                print('\t\t< Fullpath:\t{}'.format(folder))
                print('\t\t< Parts:\t{}'.format(folder.parts))
                print('\t\t< Folder:\t{}'.format(foldername))
                print('\t\t< Parents:')
                for i in range(0,len(folder.parts)-1):
                    print('\t\t\t[{}]: {}'.format(i, folder.parents[i]))

            parts = foldername.split('_') # splits foldername to gather experiment data

            # set class properties
            path        = folder
            file        = parts[0]
            sampling    = parts[4]
            mode        = int(parts[1][-1])
            vector      = int(parts[2][-1])
            steps       = int(parts[3][-1])

            # CSV logs full paths
            infocsv     = folder / cfg.csv_info
            timecsv     = folder / 'logs_model-import_remote' / cfg.csv_time
            dstatcsv    = folder / 'logs_model-import_remote' / cfg.csv_dstat
            reportcsv   = folder / 'logs_model-import_remote' / cfg.report
            resultcsv   = folder / 'logs_model-import_remote' / cfg.csv_result

            # import CSV as dafaframe
            info    = read_csv(infocsv,delimiter=',',encoding='utf-8',index_col=0)
            time    = read_csv(timecsv,delimiter=',',encoding='utf-8')
            dstat   = read_csv(dstatcsv,delimiter='[,\t]',header=5,encoding='utf-8',engine='python')
            report  = read_csv(reportcsv,delimiter=',',encoding='utf-8')
            result  = read_csv(resultcsv,delimiter=',',encoding='utf-8')

            # create Experiment object
            tmp = Experiment(path,file,mode,vector,steps,sampling,info,time,dstat,report,result) # create temporary object

            if verbose: # output current experiment information
                print('\t\t< Attributes:\t{}'.format(parts))
                print('\t\t< Experiment:')
                print('\t\t\t< {}'.format(tmp.fullpath))
                print('\t\t\t< {}'.format(tmp.file))
                print('\t\t\t< {}'.format(cfg.samplingmode[tmp.mode]))
                print('\t\t\t< {}'.format(cfg.vectors[tmp.vector]))
                print('\t\t\t< n = {}'.format(tmp.steps))
                print('\t\t\t< {}\n'.format(tmp.sampling))

            # appending Experiment object to list, based on sampling method
            if tmp.sampling == 'perflowsampled': experiments_perflow.append(tmp)
            elif tmp.sampling == 'packetsampled': experiments_packets.append(tmp)

        print('\t<< Saving objects')
        #if verbose: input('...')

    # create list to return
    experiments = [experiments_perflow, experiments_packets]
    return experiments
# preprocess timestamps, ticks, labels
def preprocessData(folders,verbose=False):

    return




if __name__ == '__main__':

    pd.set_option('display.float_format', lambda x: '%.5f' % x) # force float output for epoch time
    verbose = args.verbose
    plot    = args.plot

    # accumulate folders containing experiment data
    for path in Path(cfg.flowfolder).iterdir():
        if path.is_dir(): flowfolder.append(path) # perflow sampling
    flowfolder.sort()

    for path in Path(cfg.packetfolder).iterdir():
        if path.is_dir(): packetfolder.append(path) # packet sampling
    packetfolder.sort()

    # check passed optional arguments and commands
    print('\n'+40*'~'+' SCRIPT: Evaluation.py '+40*'~')
    print('\nfolders:\n\t{}\tsub-folders: {}\n\t{}\tsub-folders: {}\n\n'.format(cfg.flowfolder,len(flowfolder),cfg.packetfolder,len(packetfolder)))
    if verbose: input('...')


    print('>>> Creating objects')
    folders = [flowfolder,packetfolder] # list for different sampling-categories
    exp = createExperiments(folders,verbose) # save returned experiment objects for further processing


    print('>>> Accumulate informations')
    vectors = []
    steps   = []
    modes   = []
    for n in range(0,len(folders)):
        for i in range (0,len(exp[n])):
            v = exp[n][i].vector
            s = exp[n][i].steps
            m = exp[n][i].mode
            if v not in vectors:    vectors.append(v)
            if s not in steps:      steps.append(s)
            if m not in modes:      modes.append(m)
    if verbose:
        print('\t<< feature-vectors:')
        for i in range(0,len(vectors)):
            print('\t\t< {}'.format(cfg.vectors[vectors[i]]))
        print('\t<< sampling-steps:')
        for i in range(0,len(steps)):
            print('\t\t< n = {}'.format(steps[i]))
        print('\t<< sampling-modes:')
        for i in range(0,len(modes)):
            print('\t\t< {}'.format(cfg.samplingmode[steps[i]]))

    print('>>> Converting timestamps, adding runtimes, adjusting logs')
    maxruntime = 0
    for n in range(0,len(folders)):
        for i in range (0,len(exp[n])):
            start   = exp[n][i].time['epochtime'].iloc[0] # start epochtime
            end     = exp[n][i].time['epochtime'].iloc[-1]+1 # end epochtime
            exp[n][i].runtime = end-start # set current experiments runtime

            # dump dstat rows outside of script execution
            exp[n][i].dstat = exp[n][i].dstat[(exp[n][i].dstat['"epoch"'] >= start) & (exp[n][i].dstat['"epoch"'] <= end)]

            # convert epoch time to relative
            exp[n][i].time['epochtime'] = exp[n][i].time['epochtime'].subtract(start)
            exp[n][i].dstat['"epoch"']  = exp[n][i].dstat['"epoch"'].subtract(start)

            # search maximum runtime of all experiments, used for spider chart generation later on
            if (end-start) > maxruntime: maxruntime = (end-start)


    print('>>> Converting memory values')
    convert = ['"used"','"total"','"cach"','"free"','"used".1','"free".1'] # features to convert (RAM, SWAP)
    for n in range(0,len(folders)):
        for i in range (0,len(exp[n])):
            rows = exp[n][i].dstat.shape[0]
            for feature in convert:
                for row in range(0,rows):
                    tmp = exp[n][i].dstat[feature][row]/1024**2
                    exp[n][i].dstat.at[row,feature]=tmp



    # CPU USAGE
    print('>>> Creating CPU-usage graphs')
    count = 0
    for n in range(0,len(folders)):
        for i in range (0,len(exp[n])):

            count += 1
            ticks   = []
            labels  = []

            png_file = 'figures/CPU-usage_figure{}.png'

            # create list of relevant timestamps
            for j in range(0,exp[n][i].time['epochtime'].shape[0]):
                ticks.append(exp[n][i].time['epochtime'][j])
                labels.append(exp[n][i].time['segment'][j])

            # create tuple containing ticks and labels
            stamps = list(zip(ticks,labels))
            stamps.sort(key=lambda x: float(x[0]),reverse=False)
            timestamps  = [stamp[0] for stamp in stamps]
            timelabels = [stamp[1] for stamp in stamps]

            # graph title & subtitle
            sampling    = exp[n][i].sampling
            steps       = exp[n][i].steps
            vector      = cfg.vectors[exp[n][i].vector]
            mode        = cfg.samplingmode[exp[n][i].mode]
            # nicer output for title
            if sampling     == 'perflowsampled':    samplingtype = 'per-flow sampling'
            elif sampling   == 'packetsampled':     samplingtype = 'packet sampling'

            title = '{}\n'.format(samplingtype)
            subtitle = '({}, n={})\n{}'.format(mode,steps,vector)

            fig = plt.figure(figsize=(21.0,9.0))
            plt.plot(exp[n][i].dstat['"epoch"'],exp[n][i].dstat['"usr"'],color = '#000000',label='CPU python')
            plt.plot(exp[n][i].dstat['"epoch"'],exp[n][i].dstat['"sys"'],color = '#566573',label='CPU system')

            # plot segments
            style = 'dotted'
            color = '#000000'
            for j in (range (1,len(labels)-1)):
                plt.axvline(x=stamps[j][0],ymin=0,ymax=1,linestyle=style,color=color) # plot vertical lines

            # plot labels
            plt.xticks(timestamps,timelabels,rotation=80) # create x-axis ticks
            plt.xlabel('segments', fontsize=14)
            plt.ylabel('memory-usage',fontsize=14)
            plt.title(title,ha='center',fontsize=18) # set title
            plt.suptitle(subtitle,x=0.515,y=0.905,ha='center',fontsize=10) # suptitle position between 0 and 1
            plt.legend(loc='best')
            plt.tight_layout() # increase space below x-axis for proper labeling

            if verbose: print('\t<< {}'.format(png_file.format(count)))
            plt.savefig(png_file.format(count)) # save plot to file

            # show/hide plots
            if (not plot): plt.close(fig) # close fig directly to not show it on script execution
            else: plt.show() # show single plot



    # RAM USAGE
    print('>>> Creating memory-usage graphs')
    count = 0
    for n in range(0,len(folders)):
        #for i in range (0,1): # test loop only one experiment
        for i in range (0,len(exp[n])):
            count += 1
            ticks   = []
            labels  = []

            png_file = 'figures/RAM-usage_figure{}.png'

            # create list of relevant timestamps
            for j in range(0,exp[n][i].time['epochtime'].shape[0]):
                ticks.append(exp[n][i].time['epochtime'][j])
                labels.append(exp[n][i].time['segment'][j])

            # create tuple containing ticks and labels
            stamps = list(zip(ticks,labels))
            stamps.sort(key=lambda x: float(x[0]),reverse=False)
            timestamps  = [stamp[0] for stamp in stamps]
            timelabels = [stamp[1] for stamp in stamps]

            # graph title & subtitle
            sampling    = exp[n][i].sampling
            steps       = exp[n][i].steps
            vector      = cfg.vectors[exp[n][i].vector]
            mode        = cfg.samplingmode[exp[n][i].mode]
            # nicer output for title
            if sampling     == 'perflowsampled':    samplingtype = 'per-flow sampling'
            elif sampling   == 'packetsampled':     samplingtype = 'packet sampling'

            title = '{}\n'.format(samplingtype)
            subtitle = '({}, n={})\n{}'.format(mode,steps,vector)

            # plot graphs
            fig = plt.figure(figsize=(21.0,9.0))
            plt.plot(exp[n][i].dstat['"epoch"'],exp[n][i].dstat['"total"'], color = '#000000',label='RAM total',linewidth=3)
            plt.plot(exp[n][i].dstat['"epoch"'],exp[n][i].dstat['"used"'],  color = '#566573',label='RAM used',linewidth=3)
            plt.plot(exp[n][i].dstat['"epoch"'],exp[n][i].dstat['"cach"'],  color = '#AEB6BF',label='RAM cached',linewidth=3)
            plt.plot(exp[n][i].dstat['"epoch"'],exp[n][i].dstat['"used".1'],color = '#566573',label='SWAP used',linewidth=3)

            # plot segments
            style = 'dotted'
            color = '#000000'
            for j in (range (1,len(labels)-1)):
                plt.axvline(x=stamps[j][0],ymin=0,ymax=1,linestyle=style,color=color) # plot vertical lines

            # plot labels
            plt.xticks(timestamps,timelabels,rotation=80) # create x-axis ticks
            plt.xlabel('segments', fontsize=14)
            plt.ylabel('memory-usage',fontsize=14)
            plt.title(title,ha='center',fontsize=18) # set title
            plt.suptitle(subtitle,x=0.515,y=0.905,ha='center',fontsize=10) # suptitle position between 0 and 1
            plt.legend(loc='best')
            plt.tight_layout() # increase space below x-axis for proper labeling

            if verbose: print('\t<< {}'.format(png_file.format(count)))
            plt.savefig(png_file.format(count)) # save plot to file

            # show/hide plots
            if (not plot): plt.close(fig) # close fig directly to not show it on script execution
            else: plt.show() # show single plot
    #if plot: plt.show() # show all plots



    # SPIDER CHART
    print('>>> Creating spider-chart graphs')
    count = 0
    for n in range(0,len(folders)):
        #for i in range (0,1): # test loop only one experiment
        for i in range (0,len(exp[n])):
            count += 1
            png_file = 'figures/spiderchart_figure{}.png'

            # relevant values for chart creation
            CPU_max     = exp[n][i].dstat['"usr"'].max()
            RAM_total   = exp[n][i].dstat['"total"'].max() # total RAM available
            RAM_used    = exp[n][i].dstat['"used"'].max()/RAM_total*100
            RAM_cached  = exp[n][i].dstat['"cach"'].max()/RAM_total*100
            accuracy    = float(exp[n][i].result['summary'][2])*100
            recall0     = exp[n][i].report['recall'][0]*100
            recall1     = exp[n][i].report['recall'][1]*100
            prec0       = exp[n][i].report['precision'][0]*100
            prec1       = exp[n][i].report['precision'][1]*100
            runtime     = exp[n][i].runtime/maxruntime*100

            # graph title & subtitle
            sampling    = exp[n][i].sampling
            steps       = exp[n][i].steps
            vector      = cfg.vectors[exp[n][i].vector]
            mode        = cfg.samplingmode[exp[n][i].mode]
            # nicer output for title
            if sampling     == 'perflowsampled':    samplingtype = 'per-flow sampling'
            elif sampling   == 'packetsampled':     samplingtype = 'packet sampling'

            title = '{}\n{} ({}, n={})'.format(vector,sampling,mode,steps)

            # forge polar-compatible values and angles
            value   = [RAM_used,RAM_cached,CPU_max,accuracy,recall0,prec0,recall1,prec1,runtime]
            N       = len(value) # number of different parameters shown in spider-chart
            value   += value[:1] # close value "circle" for sider-chart
            angles  = [n / float(N) * 2 * pi for n in range(N)]
            angles  += angles[:1] # close angle "circle" for spider-chart

            fig = plt.figure(figsize=(10.0,10.0))
            ax  = plt.subplot(polar=True)
            plt.polar(angles,value, linewidth=2, color='#566573')

            # label parameters
            stats = ['used RAM\n({}%)'.format(int(RAM_used)),'cached RAM\n({}%)'.format(int(RAM_cached)),'CPU usage\n({}%)'.format(int(CPU_max)),'Accuracy','Recall\n"0"','Precision\n"0"','Recall\n"1"','Precision\n"1"','Runtime']
            plt.xticks(angles[:-1],stats) # pass angles but last (repetition of first value)

            if verbose: print('\t<< {}'.format(png_file.format(count)))
            plt.savefig(png_file.format(count)) # save plot to file

            # show/hide plots
            if (not plot): plt.close(fig) # close fig directly to not show it on script execution
            else: plt.show() # show single plot
            plt.show()



    # SPIDER CHART COMPARISONS
    print('>>> Prepare spider-chart comparisons')

    # TODO: compare same feature-vector experiments as simple starting point



    exit()



















    # how to read basic experiment infos
    print('\nsampling-categories: {}\n'.format(len(exp)))
    print('perflow-experiments: {}\n{}\n'.format(len(exp[0]),exp[0]))
    print('packet-experiments: {}\n{}\n'.format(len(exp[1]),exp[1]))


    for i in range(0,len(exp[0])):
        print('information:\n{}'.format(exp[0][i].info))
        print('time:\n{}'.format(exp[0][i].time))
        print('dstat:\n{}'.format(exp[0][i].dstat))
        print('result:\n{}'.format(exp[0][i].result))
        print('report:\n{}'.format(exp[0][i].report))
        input('...')


    print('>>> Importing logs')
    # TODO impelement code already created for importing dstat.csv, time.csv, information.csv, results.csv,report.csv
    # create charts based on imports and grouping


    exit() # implement below code in current folderstructure










# OLD CODE BELOW


    for path in Path(logd).iterdir(): # get all folder-paths for evaluation
        if path.is_dir(): evaluationd.append(path)

    print('\n>>> evaluation-data:')
    for i in range(0,len(evaluationd)):
        print('\t[{}]: {}'.format(i,evaluationd[i]))

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
        samplingtypes.append(samplingtype) # per-flow/packet-sampling?

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
    # get timestamps for script-segments
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


    # RAM usage
    for i in range(0,len(evaluationd)):

        # initialise empty list to create x-axis labels 
        ticks = []
        labels = []
        plt.figure(figsize=(21.0,9.0)) # set base canvas size in inch to get large *.png files

        # timestamps and labels have to be in the same list-position for correct tuple creation
        # timestamps
        ticks.append(csvimports[i])
        ticks.append(scalersfit[i])
        ticks.append(filesplits[i])
        ticks.append(scalersxtrain[i])
        ticks.append(scalersxtest[i])
        ticks.append(pcasfit[i])
        ticks.append(pcasxtest[i])
        ticks.append(modelsimport[i])
        ticks.append(predictions[i])
        # matching labels
        labels.append('import CSV')
        labels.append('fit scaler')
        labels.append('split files')
        labels.append('scale Xtrain')
        labels.append('scale Xtest')
        labels.append('fit PCA')
        labels.append('PCA Xtest')
        labels.append('import model')
        labels.append('predictions')

        # create a tuple combining ticks and labels
        ticktuple = list(zip(ticks,labels))
        # just in case for further additions, sort tuple by its timestamp (not necessary for creating xticks)
        ticktuple.sort(key = lambda x: float(x[0]),reverse=False)

        # create list of timestamps and labels
        timestamps = [time[0] for time in ticktuple]
        timelabels = [time[1] for time in ticktuple]
        # create graph title and subtitle
        #title = '{}\n({}, n={})\n{}'.format(samplingtypes[i],samplingmodes[i],samplingsteps[i],featurevectors[i])
        title = '{}\n'.format(samplingtypes[i])
        subtitle = '({}, n={})\n{}'.format(samplingmodes[i],samplingsteps[i],featurevectors[i])
        # plot graphs
        plt.plot(dstats[i]['"epoch"'],dstats[i]['"total"'],color = '#000000',label='RAM total',linewidth=3)
        plt.plot(dstats[i]['"epoch"'],dstats[i]['"used"'],color = '#566573',label='RAM used', linewidth=2)
        plt.plot(dstats[i]['"epoch"'],dstats[i]['"cach"'],color = '#AEB6BF',label='RAM cached', linewidth=2)

        style = 'dotted' # vertical lines style
        color = '#000000' # vertical lines color
        plt.axvline(x=predictions[i],ymin=0,ymax=1,linestyle=style,color=color)
        plt.axvline(x=modelsimport[i],ymin=0,ymax=1,linestyle=style,color=color)
        plt.axvline(x=pcasxtest[i],ymin=0,ymax=1,linestyle=style,color=color)
        plt.axvline(x=pcasfit[i],ymin=0,ymax=1,linestyle=style,color=color)
        plt.axvline(x=scalersxtest[i],ymin=0,ymax=1,linestyle=style,color=color)
        plt.axvline(x=scalersxtrain[i],ymin=0,ymax=1,linestyle=style,color=color)
        plt.axvline(x=filesplits[i],ymin=0,ymax=1,linestyle=style,color=color)
        plt.axvline(x=scalersfit[i],ymin=0,ymax=1,linestyle=style,color=color)
        plt.axvline(x=csvimports[i],ymin=0,ymax=1,linestyle=style,color=color)

        plt.xticks(timestamps,timelabels,rotation='vertical') # create x-axis ticks
        plt.xlabel('segments',fontsize=14) # label x-axis
        plt.ylabel('memory-usage (MB)',fontsize=14) # label y-axis
        plt.title(title,ha='center',fontsize=18) # set title
        plt.suptitle(subtitle,x=0.515,y=0.905,ha='center',fontsize=10) # suptitle position between 0 and 1
        plt.legend(loc='best')
        plt.tight_layout() # increase space below x-axis for proper labeling
        #plt.savefig('test.png') # save plot to disk
        plt.show()



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

        plt.figure(figsize=(10.0,10.0)) # set base canvas size in inch to get large *.png files

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
        plt.polar(angles,values[i], linewidth=2, color='#566573')

        # label parameters
        stats = ['used RAM\n({}%)'.format(int(percentRAMsused[i])),'cached RAM\n({}%)'.format(int(percentRAMscached[i])),'CPU usage\n({}%)'.format(int(maxCPUs[i])),'Accuracy','Recall\n"0"','Precision\n"0"','Recall\n"1"','Precision\n"1"','Runtime']
        plt.xticks(angles[:-1],stats) # pass angles but last (repetition of first value)
        # label value-axis position,ticks and limit
        ax.set_rlabel_position(60)
        plt.yticks([0,25,50,75,100], color='grey', size=10)
        plt.ylim(0,100)
        plt.title(title)

        plt.show() # print current spider-chart

    # SPIDER CHART COMPARISON PLOT

    plt.figure(figsize=(10.0,10.0)) # set base canvas size in inch to get large *.png files
    ax = plt.subplot(polar=True)

    # for now, manually pick models that should be compared
    width = 2
    plt.polar(angles,values[3],linewidth=width,color = '#566573',label='n=5 (per-flow sampling)')
    plt.polar(angles,values[1],linewidth=width,linestyle='dotted',color = '#566573',label='n=5 (packet sampling)')

    plt.polar(angles,values[0],linewidth=width,color = '#AEB6BF',label='n=10 (per-flow sampling)')
    plt.polar(angles,values[2],linewidth=width,linestyle='dotted',color = '#AEB6BF',label='n=10 (packet sampling)')


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


    # CPU USAGE
    for i in range(0,len(evaluationd)):
        title = '{}\n{} ({}, n={})'.format(featurevectors[i],samplingtypes[i],samplingmodes[i],samplingsteps[i])
        plt.plot(dstats[i]['"epoch"'],dstats[i]['"usr"'],color = '#000000',label='CPU python')
        #plt.plot(dstats[i]['"epoch"'],dstats[i]['"sys"'],color = '#566573',label='CPU system')
        #plt.plot(dstats[i]['"epoch"'],dstats[i]['"idl"'],color = '#AEB6BF',label='CPU idle')

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

    exit()