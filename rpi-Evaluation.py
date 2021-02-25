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
import random
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
    def __init__(self,fullpath,file,mode,vector,steps,sampling,info,time,dstat,report,result,runtime=0,parameter=0):
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

        # chart-values

        # calculated values
        self.runtime    = runtime # runtime for preprocessing and classification in seconds
        self.parameter  = parameter # parameter including accuracy, runtime ???

    def __str__(self):
        return str(self.__class__)+': '+str(self.__dict__)
# extract information from folders, create object for each experiment containing sampling information and logs as df
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
            title_sampling    = exp[n][i].sampling
            title_steps       = exp[n][i].steps
            title_vector      = cfg.vectors[exp[n][i].vector]
            title_mode        = cfg.samplingmode[exp[n][i].mode]
            # nicer output for title
            if exp[n][i].sampling       == 'perflowsampled':    samplingtype = 'per-flow sampling'
            elif exp[n][i].sampling     == 'packetsampled':     samplingtype = 'packet sampling'

            title = '{}\n'.format(samplingtype)
            subtitle = '({}, n={})\n{}'.format(title_mode,title_steps,title_vector)

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
            title_sampling    = exp[n][i].sampling
            title_steps       = exp[n][i].steps
            title_vector      = cfg.vectors[exp[n][i].vector]
            title_mode        = cfg.samplingmode[exp[n][i].mode]
            # nicer output for title
            if exp[n][i].sampling     == 'perflowsampled':    samplingtype = 'per-flow sampling'
            elif exp[n][i].sampling   == 'packetsampled':     samplingtype = 'packet sampling'

            title = '{}\n'.format(samplingtype)
            subtitle = '({}, n={})\n{}'.format(title_mode,title_steps,title_vector)

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
            title_sampling    = exp[n][i].sampling
            title_steps       = exp[n][i].steps
            title_vector      = cfg.vectors[exp[n][i].vector]
            title_mode        = cfg.samplingmode[exp[n][i].mode]
            # nicer output for title
            if exp[n][i].sampling     == 'perflowsampled':    samplingtype = 'per-flow sampling'
            elif exp[n][i].sampling   == 'packetsampled':     samplingtype = 'packet sampling'

            title = '{}\n{} ({}, n={})'.format(title_vector,title_sampling,title_mode,title_steps)

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
    print('\t>> Using similar feature-vectors')

    for i in range(0,len(vectors)):
        print('\t\t< {}'.format(cfg.vectors[vectors[i]]))
    print('\t<< Search sampling-steps')
    for i in range(0,len(steps)):
        print('\t\t< n = {}'.format(steps[i]))

    #for n in range(0, len(compare)):
    #    tmp = []
    #    for folder in compare[n]:



    # TODO: compare same feature-vector experiments as simple starting point

    # find experiments using the same feature-vector
    print('>>> Bundle experiments for comparison')

    # palette containing different colors for random picks on comparison charts
    palette = []
    palette.append('#000000')
    palette.append('#566573')
    palette.append('#AEB6BF')
    palette.append('#52FF3A')
    palette.append('#4BE936')
    palette.append('#44D331')
    palette.append('#3FC52D')
    palette.append('#39B329')
    palette.append('#33A225')
    palette.append('#2E9121')
    palette.append('#287F1C')
    palette.append('#216918')


    compare = exp.copy() # copy all experiment data
    count = 0


    for v in vectors: # accumulate experiments with similar feature-vector
        tmp = []
        tmp_color = palette.copy()
        count += 1
        for n in range(0,len(folders)):
            for i in range (0,len(exp[n])):
                if exp[n][i].vector == v:
                    tmp.append(exp[n][i])
        print('iteration #{}:\n\nexperiments: {}\n{}'.format(count,len(tmp),tmp))

        # CREATE CHART
        # lists to accumulate values & labels for comparison
        compare_values = []
        compare_angles = []
        compare_labels  = []
        compare_colors = []

        for x in tmp: # iterate over current bundle of experiments

            # relevant values for chart creation
            CPU_max     = x.dstat['"usr"'].max()
            RAM_total   = x.dstat['"total"'].max() # total RAM available
            RAM_used    = x.dstat['"used"'].max()/RAM_total*100
            RAM_cached  = x.dstat['"cach"'].max()/RAM_total*100
            accuracy    = float(x.result['summary'][2])*100
            recall0     = x.report['recall'][0]*100
            recall1     = x.report['recall'][1]*100
            prec0       = x.report['precision'][0]*100
            prec1       = x.report['precision'][1]*100
            runtime     = x.runtime/maxruntime*100

            # nicer output for legend
            if x.sampling     == 'perflowsampled':    samplingtype = 'per-flow sampling'
            elif x.sampling   == 'packetsampled':     samplingtype = 'packet sampling'

            # forge polar-compatible values and angles
            value   = [RAM_used,RAM_cached,CPU_max,accuracy,recall0,prec0,recall1,prec1,runtime]
            N       = len(value) # number of different parameters shown in spider-chart
            value   += value[:1] # close value "circle" for sider-chart
            angles  = [n / float(N) * 2 * pi for n in range(N)]
            angles  += angles[:1] # close angle "circle" for spider-chart

            # pick random color from list
            color = random.choice(tmp_color)
            tmp_color.remove(color)

            # title & label
            title = 'comparison\n{}\n'.format(cfg.vectors[v])
            label = 'n = {}, {}'.format(x.steps,samplingtype)

            # create lists for comparison-plot
            compare_values.append(value)
            compare_angles.append(angles)
            compare_colors.append(color)
            compare_labels.append(label)

        plt.figure(figsize=(10.0,10.0))
        ax = plt.subplot(polar=True)
        width = 2

        for c in range(0,len(compare_values)): # create plots
            plt.polar(compare_angles[c],compare_values[c],linewidth=width,linestyle='dotted',label=compare_labels[c],color=compare_colors[c])

        stats = ['used RAM','cached RAM','CPU usage','Accuracy','Recall\n"0"','Precision\n"0"','Recall\n"1"','Precision\n"1"','Runtime']
        plt.xticks(compare_angles[0][:-1],stats)
        ax.set_rlabel_position(60)
        plt.yticks([0,25,50,75,100], color='grey', size=10)
        plt.ylim(0,100)
        plt.title(title,size='medium') # set title
        plt.legend()
        plt.show()



    print('\t<< Search sampling-steps')
    for i in range(0,len(steps)):
        print('\t\t< n = {}'.format(steps[i]))

    for s in steps: # accumulate experiments with similar feature-vector
        tmp = []
        tmp_color = palette.copy()
        count += 1
        for n in range(0,len(folders)):
            for i in range (0,len(exp[n])):
                if exp[n][i].steps == s:
                    tmp.append(exp[n][i])
        print('iteration #{}:\n\nexperiments: {}\n{}'.format(count,len(tmp),tmp))

        # CREATE CHART
        # lists to accumulate values & labels for comparison
        compare_values = []
        compare_angles = []
        compare_labels  = []
        compare_colors = []

        for x in tmp: # iterate over current bundle of experiments

            # relevant values for chart creation
            CPU_max     = x.dstat['"usr"'].max()
            RAM_total   = x.dstat['"total"'].max() # total RAM available
            RAM_used    = x.dstat['"used"'].max()/RAM_total*100
            RAM_cached  = x.dstat['"cach"'].max()/RAM_total*100
            accuracy    = float(x.result['summary'][2])*100
            recall0     = x.report['recall'][0]*100
            recall1     = x.report['recall'][1]*100
            prec0       = x.report['precision'][0]*100
            prec1       = x.report['precision'][1]*100
            runtime     = x.runtime/maxruntime*100

            # nicer output for legend
            if x.sampling     == 'perflowsampled':    samplingtype = 'per-flow sampling'
            elif x.sampling   == 'packetsampled':     samplingtype = 'packet sampling'

            # forge polar-compatible values and angles
            value   = [RAM_used,RAM_cached,CPU_max,accuracy,recall0,prec0,recall1,prec1,runtime]
            N       = len(value) # number of different parameters shown in spider-chart
            value   += value[:1] # close value "circle" for sider-chart
            angles  = [n / float(N) * 2 * pi for n in range(N)]
            angles  += angles[:1] # close angle "circle" for spider-chart

            # pick random color from list
            color = random.choice(tmp_color)
            tmp_color.remove(color)

            # title & label
            title = 'n = {}'.format(s)
            label = '{}\n{}\n{}\n{}'.format(x.file,cfg.vectors[x.vector],samplingtype,cfg.samplingmode[x.mode])

            # create lists for comparison-plot
            compare_values.append(value)
            compare_angles.append(angles)
            compare_colors.append(color)
            compare_labels.append(label)

        plt.figure(figsize=(15.0,10.0))
        ax = plt.subplot(polar=True)
        width = 2

        for c in range(0,len(compare_values)): # create plots
            plt.polar(compare_angles[c],compare_values[c],linewidth=width,linestyle='dotted',label=compare_labels[c],color=compare_colors[c])

        stats = ['used RAM','cached RAM','CPU usage','Accuracy','Recall\n"0"','Precision\n"0"','Recall\n"1"','Precision\n"1"','Runtime']
        plt.xticks(compare_angles[0][:-1],stats)
        ax.set_rlabel_position(60)
        plt.yticks([0,25,50,75,100], color='grey', size=10)
        plt.ylim(0,100)
        plt.title(title,size='medium') # set title
        plt.legend(loc='best')
        plt.show()

    exit()