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
from matplotlib.lines import Line2D


import os
import random

import pandas as pd
import numpy as np
import config as cfg
import matplotlib.pyplot as plt

# create figures folder if necessary
if not os.path.exists(cfg.figures): os.mkdir(cfg.figures)

# disable figure warning
plt.rcParams.update({'figure.max_open_warning': 0})

# dict to create roman letter numbers
IDroman = {
1:'I',
2:'II',
3:'III',
4:'IV',
5:'V',
6:'VI',
7:'VII',
8:'VIII',
9:'IX',
10:'X',
11:'XI',
12:'XII',
13:'XIII',
14:'XIV',
15:'XV',
16:'XVI',
17:'XVII',
18:'XVIII',
19:'XIX',
20:'XX',
21:'XXI',
22:'XXII',
23:'XXIII',
24:'XXIV',
25:'XXV',
26:'XXVI'
}


# ARGUMENT PARSING
import argparse
parser = argparse.ArgumentParser(description='Script to evaluate machine-learning based anomaly detection results.')
parser.add_argument('-v','--verbose', action='store_true', help= 'output verbose information')
parser.add_argument('-p','--plot', action='store_true', help = 'output plots')
args = parser.parse_args()

# vector label used for plot titles
vector = {
1:'AGM10s',
2:'AGM60s', # unused
3:'AGM3600s', # unused
4:'CAIA',
5:'CAIA',
6:'AGM10s'
}

# initialise empty lists
exp                   = []
flowfolder            = []
packetfolder          = []
experiments_perflow   = []
experiments_packets   = []
experiments_unsampled = []


# class object containing all necessary experiment data
class Experiment:
    def __init__(self,fullpath,file,mode,vector,steps,sampling,info,time,dstat,report,result,style='solid',modelsize=0,idnumber=0,runtime=0,classtime=0,classspeed=0,instances=0,parameter=0,parameter2=0,parameter3=0,parameter4=0,maxram=0,trees=0,maxleaves=0,maxdepth=0,pca_n=0,pca_var=0):
        # info
        self.fullpath   = fullpath
        self.file       = file
        self.mode       = mode
        self.vector     = vector
        self.steps      = steps
        self.sampling   = sampling
        self.idnumber   = idnumber

        # logs
        self.info       = info
        self.time       = time
        self.dstat      = dstat
        self.report     = report
        self.result     = result

        # charts
        self.style      = style # linestyle in graph plots

        # parameters
        self.runtime    = runtime # runtime for preprocessing and classification in seconds
        self.classtime  = classtime # runtime for classification in seconds
        self.classspeed = classspeed # classification speed in classifications per second
        self.instances  = instances # number of instances to classify
        self.parameter  = parameter # parameter
        self.parameter2 = parameter2
        self.parameter3 = parameter3
        self.parameter4 = parameter4
        self.maxram     = maxram # maximum value for used RAM
        self.trees      = trees # number of generated RF trees
        self.maxleaves  = maxleaves # maximum number of leaves
        self.maxdepth   = maxdepth # maximum tree depth
        self.modelsize  = modelsize # size of the pickle model used for classification
        self.pca_n      = pca_n # number of PCA components to reach explained variance
        self.pca_var    = pca_var

    def __str__(self):
        return str(self.__class__)+': '+str(self.__dict__)

    def update(self, property, value):
        setattr(self, property, value)


# extract information from folders, create object for each experiment containing sampling information and logs as df
def createExperiments(folders,verbose=False):

    idnumber = 0 # number used for experiment ID
    for item in folders: # list of folders containing the actual experiment folders

        print('\t>> Reading sub-folders')
        for folder in item: # iterating over sub-folders
            idnumber += 1

            foldername = folder.parts[-1] # returns the current foldername


            if verbose: # output current experiment folders
                print('\t\t< Fullpath:\t{}'.format(folder))
                print('\t\t< Parts:\t{}'.format(folder.parts))
                print('\t\t< Folder:\t{}'.format(foldername))
                print('\t\t< Parents:')
                for i in range(0,len(folder.parts)-1):
                    print('\t\t\t[{}]: {}'.format(i, folder.parents[i]))

            parts = foldername.split('_') # splits foldername to gather experiment data
            #print(parts)
            #input('...')
            # set class properties based on foldername
            path        = folder
            file        = parts[0]
            sampling    = parts[4]
            # can only be read this way for single digit options
            #print(int(parts[4][-1]))
            mode        = int(parts[1][-1])
            #print(mode)
            #input(...)
            vector      = int(parts[2][-1])
            #steps       = int(parts[3][-1])
            # set plot style based on sampling technique
            # https://matplotlib.org/stable/gallery/lines_bars_and_markers/linestyles.html
            if sampling == 'flowbased': style='dotted'
            elif sampling == 'packetbased': style='solid'

            # CSV logs full paths
            infocsv     = folder / cfg.csv_info
            timecsv     = folder / 'logs_model-import_remote' / cfg.csv_time
            dstatcsv    = folder / 'logs_model-import_remote' / cfg.csv_dstat
            reportcsv   = folder / 'logs_model-import_remote' / cfg.csv_report
            resultcsv   = folder / 'logs_model-import_remote' / cfg.csv_result
            # model
            model       = folder / 'model' / 'Merged_model_remote.pkl'
            modelsize   = os.path.getsize(model)/1000**2

            # import CSV as dafaframe
            info    = read_csv(infocsv,delimiter=',',encoding='utf-8',index_col=0)
            time    = read_csv(timecsv,delimiter=',',encoding='utf-8')
            dstat   = read_csv(dstatcsv,delimiter='[,\t]',header=5,encoding='utf-8',engine='python')
            report  = read_csv(reportcsv,delimiter=',',encoding='utf-8')
            result  = read_csv(resultcsv,delimiter=',',encoding='utf-8')

            # get sampling-steps from imported info
            steps     = int(info['0'].iloc[3])

            #print(parts)
            #print(mode)
            #print(vector)
            #print(steps)
            #input('...')

            # create Experiment object
            tmp = Experiment(path,file,mode,vector,steps,sampling,info,time,dstat,report,result,style,modelsize,idnumber) # create temporary object

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
            if tmp.sampling   == 'flowbased': experiments_perflow.append(tmp)
            elif tmp.sampling == 'packetbased': experiments_packets.append(tmp)

            # save unsampled experiments for later comparison chart creation
            if tmp.steps == 0: experiments_unsampled.append(tmp)

        print('\t\t< Saving objects')
        #if verbose: input('...')

    # create list to return
    experiments = [experiments_perflow, experiments_packets]
    return experiments

# creates experiment ID numbers according to the order of comparison.csv
def createIDs(folders):

    AGMexp  = []
    CAIAexp = []

    for n in range(0,len(folders)):
        for i in range (0,len(exp[n])):
            if exp[n][i].vector == 1 or exp[n][i].vector == 6:
                AGMexp.append(exp[n][i])
            elif exp[n][i].vector == 4 or exp[n][i].vector == 5:
                CAIAexp.append(exp[n][i])

    tmpid = 0
    print('>>> Creating experiment ID numbers.')
    for experiment in AGMexp:
        tmpid += 1
        experiment.update('idnumber',tmpid)
        if verbose: print('\t>> {}:\n\t\ttechnique: {}\n\t\tmode:{}\n\t\tsteps: {}\n\t\t< ID: {}'.format(cfg.vectors[experiment.vector][0:7],experiment.sampling,cfg.samplingmode[experiment.mode],experiment.steps,tmpid))
    for experiment in CAIAexp:
        tmpid += 1
        experiment.update('idnumber',tmpid)
        if verbose: print('\t>> {}:\n\t\ttechnique: {}\n\t\tmode:{}\n\t\tsteps: {}\n\t\t< ID: {}'.format(cfg.vectors[experiment.vector][0:4],experiment.sampling,cfg.samplingmode[experiment.mode],experiment.steps,tmpid))

    return

if __name__ == '__main__':

    pd.set_option('display.float_format', lambda x: '%.5f' % x) # force float output for epoch time
    verbose = args.verbose
    plot    = args.plot

    # ACCUMULATE EXPERIMENT DATA
    for path in Path(cfg.eflowfolder).iterdir():
        if path.is_dir(): flowfolder.append(path) # add folder to flow-based experiments
    flowfolder.sort()

    for path in Path(cfg.epacketfolder).iterdir():
        if path.is_dir(): packetfolder.append(path) # add folder to packet-based experiments
    packetfolder.sort()


    # check passed optional arguments and commands
    print('\n'+40*'~'+' SCRIPT: Evaluation.py '+40*'~')
    print('\nfolders:\n\t{}\tsub-folders: {}\n\t{}\tsub-folders: {}\n\n'.format(cfg.eflowfolder,len(flowfolder),cfg.epacketfolder,len(packetfolder)))

    # clean figures directory
    print('>>> Clear directory: {}'.format(cfg.figures))
    for filetype in cfg.types:
        for file in sorted(Path(cfg.figures).glob(filetype)): # iterates over list of files, sorted by name
            Path.unlink(file)
            if verbose: print('\t<< {}'.format(file))

    # create Experiments based on given folders
    print('>>> Creating objects')
    folders = [flowfolder,packetfolder] # list for different sampling-categories
    exp = createExperiments(folders,verbose) # save returned experiment objects for further processing


    createIDs(folders)

    # extract basic information for all experiments
    print('>>> Accumulate informations')
    vectors = []
    steps   = []
    modes   = []


    for n in range(0,len(folders)):
        for i in range (0,len(exp[n])):
            #print('ID: {}\nVector: {}\nMode: \nSteps: {}\n'.format(exp[n][i].idnumber,exp[n][i].vector,exp[n][i].mode,exp[n][i].steps))
            #input('...')
            v = exp[n][i].vector
            s = exp[n][i].steps
            m = exp[n][i].mode
            if v not in vectors: vectors.append(v)
            if s not in steps:   steps.append(s)
            if m not in modes:   modes.append(m)
    vectors.sort()
    steps.sort()
    modes.sort()

    if verbose:
        print('\t<< feature-vectors:')
        for i in range(0,len(vectors)):
            print('\t\t< {}'.format(cfg.vectors[vectors[i]]))
        print('\t<< sampling-steps:')
        for i in range(0,len(steps)):
            print('\t\t< n = {}'.format(steps[i]))
        print('\t<< sampling-modes:')
        for i in modes:
            print('\t\t< {}'.format(cfg.samplingmode[i]))

    # EXTRACT & CALCULATE METRICS for every experiment
    print('>>> Converting timestamps, adding runtimes, adjusting logs')
    maxruntime    = 0 # initialize
    totalmaxram   = 0 # initialize
    maxclassspeed = 0
    maxinstances  = 0
    maxmodelsize  = 0

    maxf11 = 0
    maxrecall1 = 0

    minruntime    = 10**8
    totalminram   = 10**12
    minclassspeed = 10**8
    mininstances  = 10**8
    minmodelsize  = 10**8

    minf11 = 10**8
    minrecall1 = 10**8

    maxf11AGM = 0
    maxrecall1AGM = 0
    maxf11CAIA = 0
    maxrecall1CAIA = 0
    maxinstancesAGM = 0
    maxinstancesCAIA = 0
    minf11AGM = 10**8
    minrecall1AGM = 10**8
    minf11CAIA = 10**8
    minrecall1CAIA = 10**8
    mininstancesAGM = 10**8
    mininstancesCAIA = 10**8

    # ITERATE THROUGH ALL EXPERIMENTS
    for n in range(0,len(folders)):
        for i in range (0,len(exp[n])):
            start   = exp[n][i].time['epochtime'].iloc[0] # start epochtime
            end     = exp[n][i].time['epochtime'].iloc[-1]+1 # end epochtime plus 1 second
            exp[n][i].runtime = end-start # set current experiments runtime
            exp[n][i].classtime = exp[n][i].time['epochtime'].iloc[-1] - exp[n][i].time['epochtime'].iloc[-2] # classification time
            exp[n][i].instances = exp[n][i].report['support'][4]
            #print('{}'.format(exp[n][i].instances))
            exp[n][i].classspeed = exp[n][i].instances/exp[n][i].classtime # classifications per second
            # dump dstat rows outside of script execution
            exp[n][i].dstat = exp[n][i].dstat[(exp[n][i].dstat['"epoch"'] >= start) & (exp[n][i].dstat['"epoch"'] <= end)]
            # convert epoch time to relative
            exp[n][i].time['epochtime'] = exp[n][i].time['epochtime'].subtract(start) # apply on exported timestamps
            exp[n][i].dstat['"epoch"']  = exp[n][i].dstat['"epoch"'].subtract(start) # apply on dstat table
            # get maximum used RAM
            exp[n][i].maxram = exp[n][i].dstat['"used"'].max()/1000**2
            # get maximum tree depth and maximum leaves in Random Forest
            tmp = exp[n][i].result['summary'][7]
            exp[n][i].maxdepth = np.fromstring(tmp[1:len(tmp)-1],dtype=int, sep=",").max()
            tmp = exp[n][i].result['summary'][8]
            exp[n][i].maxleaves = np.fromstring(tmp[1:len(tmp)-1],dtype=int, sep=",").max()
            # PCA component number & explained variance
            exp[n][i].pca_n = int(exp[n][i].info['0'][6])
            exp[n][i].pca_var = float(exp[n][i].info['0'][5])

            # calculate various maximum values
            if (end-start) > maxruntime: maxruntime = (end-start)
            if exp[n][i].dstat['"used"'].max()/1000**2 > totalmaxram: totalmaxram = exp[n][i].dstat['"used"'].max()/1000**2
            if exp[n][i].classspeed > maxclassspeed: maxclassspeed = exp[n][i].classspeed
            if exp[n][i].instances > maxinstances: maxinstances = exp[n][i].instances
            if exp[n][i].modelsize > maxmodelsize: maxmodelsize = exp[n][i].modelsize

            # calculate various maximum values
            if (end-start) < minruntime: minruntime = (end-start)
            if exp[n][i].classspeed < minclassspeed: minclassspeed = exp[n][i].classspeed
            if exp[n][i].instances < mininstances: mininstances = exp[n][i].instances
            if exp[n][i].modelsize < minmodelsize: minmodelsize = exp[n][i].modelsize

            if exp[n][i].report['f1-score'][1] < minf11: minf11 = exp[n][i].report['f1-score'][1]
            if exp[n][i].report['recall'][1] < minrecall1: minrecall1 = exp[n][i].report['recall'][1]

            if exp[n][i].report['f1-score'][1] > maxf11: maxf11 = exp[n][i].report['f1-score'][1]
            if exp[n][i].report['recall'][1] > maxrecall1: maxrecall1 = exp[n][i].report['recall'][1]

            if exp[n][i].instances < mininstancesCAIA and vector[exp[n][i].vector][0:3] == 'CAI': mininstancesCAIA = exp[n][i].instances
            if exp[n][i].instances > maxinstancesCAIA and vector[exp[n][i].vector][0:3] == 'CAI': maxinstancesCAIA = exp[n][i].instances
            if exp[n][i].instances < mininstancesAGM and vector[exp[n][i].vector][0:3] == 'AGM': mininstancesAGM = exp[n][i].instances
            if exp[n][i].instances > maxinstancesAGM and vector[exp[n][i].vector][0:3] == 'AGM': maxinstancesAGM = exp[n][i].instances


            if exp[n][i].report['f1-score'][1] > maxf11AGM and vector[exp[n][i].vector][0:3] == 'AGM': maxf11AGM = exp[n][i].report['f1-score'][1]
            if exp[n][i].report['f1-score'][1] < minf11AGM and vector[exp[n][i].vector][0:3] == 'AGM': minf11AGM = exp[n][i].report['f1-score'][1]
            if exp[n][i].report['recall'][1] > maxrecall1AGM and vector[exp[n][i].vector][0:3] == 'AGM': maxrecall1AGM = exp[n][i].report['recall'][1]
            if exp[n][i].report['recall'][1] < minrecall1AGM and vector[exp[n][i].vector][0:3] == 'AGM': minrecall1AGM = exp[n][i].report['recall'][1]

            if exp[n][i].report['f1-score'][1] > maxf11CAIA and vector[exp[n][i].vector][0:3] == 'CAI': maxf11CAIA = exp[n][i].report['f1-score'][1]
            if exp[n][i].report['f1-score'][1] < minf11CAIA and vector[exp[n][i].vector][0:3] == 'CAI': minf11CAIA = exp[n][i].report['f1-score'][1]
            if exp[n][i].report['recall'][1] > maxrecall1CAIA and vector[exp[n][i].vector][0:3] == 'CAI': maxrecall1CAIA = exp[n][i].report['recall'][1]
            if exp[n][i].report['recall'][1] < minrecall1CAIA and vector[exp[n][i].vector][0:3] == 'CAI': minrecall1CAIA = exp[n][i].report['recall'][1]

    for n in range(0,len(folders)):
        for i in range (0,len(exp[n])):
            if exp[n][i].dstat['"used"'].max()/1000**2 < totalminram: totalminram = exp[n][i].dstat['"used"'].max()/1000**2


    print('>>> Sort experiments by parameter for later comparison plot')
    experiments_sorted = []
    currentparameter = 0
    # calculate parameter
    for n in range(0,len(folders)):
        for i in range (0,len(exp[n])):

            accuracyscore   = float(exp[n][i].result['summary'][2])
            recall0         = exp[n][i].report['recall'][0]
            recall1         = exp[n][i].report['recall'][1]
            precision0      = exp[n][i].report['precision'][0]
            precision1      = exp[n][i].report['precision'][1]
            F10             = exp[n][i].report['f1-score'][0]
            F11             = exp[n][i].report['f1-score'][1]
            runtime         = exp[n][i].runtime
            classtime       = exp[n][i].classtime
            instances       = exp[n][i].report['support'][4]
            classspeed      = exp[n][i].classspeed
            maxram          = exp[n][i].maxram
            file            = exp[n][i].file
            sampling        = exp[n][i].sampling
            trees           = exp[n][i].result['summary'][6]
            maxdepth        = exp[n][i].maxdepth
            maxleaves       = exp[n][i].maxleaves
            modelsize       = exp[n][i].modelsize
            pca_n           = exp[n][i].pca_n
            pca_var         = exp[n][i].pca_var

            #if vector[exp[n][i].vector][0:3] == 'AGM':
            #    minf11 = minf11AGM
            #    maxf11 = maxf11AGM
            #    minrecall1 = minrecall1AGM
            #    maxrecall1 = maxrecall1AGM
            #elif vector[exp[n][i].vector][0:3] == 'CAI':
            #    minf11 = minf11CAIA
            #    maxf11 = maxf11CAIA
            #    minrecall1 = minrecall1CAIA
            #    maxrecall1 = maxrecall1CAIA

            # min/max scaled values
            F11scaled           = (F11-minf11)/(maxf11-minf11)
            recall1scaled       = (recall1-minrecall1)/(maxrecall1-minrecall1)
            runtimescaled       = (runtime-minruntime)/(maxruntime-minruntime)
            classspeedscaled    = (classspeed-minclassspeed)/(maxclassspeed-minclassspeed)
            ramscaled           = (maxram-totalminram)/(totalmaxram-totalminram)
            instancesscaled     = (instances-mininstances)/(maxinstances-mininstances)

            #exp[n][i].parameter = (F11 + recall1)/((runtime-minruntime)/(maxruntime-minruntime) + (classspeed-minclassspeed)/(maxclassspeed-minclassspeed) + (maxram-totalminram)/(totalmaxram-totalminram))*instances/maxinstances
            #exp[n][i].parameter = (F11 + recall1)/((runtime-minruntime)/(maxruntime-minruntime) + (classspeed-minclassspeed)/(maxclassspeed-minclassspeed) + (maxram-totalminram)/(totalmaxram-totalminram))*(instances/maxinstances)
            #exp[n][i].parameter = ((F11-minf11)/(maxf11-minf11) + (recall1-minrecall1)/(maxrecall1-minrecall1))/((runtime-minruntime)/(maxruntime-minruntime) + (classspeed-minclassspeed)/(maxclassspeed-minclassspeed) + (maxram-totalminram)/(totalmaxram-totalminram))*(instances/maxinstances)


            # calculate feature-vector specific min/max scaled values for alternative parameters
            if vector[exp[n][i].vector][0:3] == 'AGM':
                F11scaled2           = (F11-minf11AGM)/(maxf11AGM-minf11AGM)
                recall1scaled2       = (recall1-minrecall1AGM)/(maxrecall1AGM-minrecall1AGM)
                instancesscaled2     = (instances-mininstancesAGM)/(maxinstancesAGM-mininstancesAGM)
            elif vector[exp[n][i].vector][0:3] == 'CAI':
                F11scaled2           = (F11-minf11CAIA)/(maxf11CAIA-minf11CAIA)
                recall1scaled2       = (recall1-minrecall1CAIA)/(maxrecall1CAIA-minrecall1CAIA)
                instancesscaled2     = (instances-mininstancesCAIA)/(maxinstancesCAIA-mininstancesCAIA)


            exp[n][i].parameter  = (F11scaled + recall1scaled)/(runtimescaled + classspeedscaled + ramscaled)
            exp[n][i].parameter2 = (F11scaled + recall1scaled)/(runtimescaled + classspeedscaled + ramscaled)*instancesscaled2
            exp[n][i].parameter3 = (F11scaled2 + recall1scaled2)/(runtimescaled + classspeedscaled + ramscaled)*instancesscaled2
            exp[n][i].parameter4 = (F11scaled2 + recall1scaled2 + instancesscaled2)/(runtimescaled + classspeedscaled + ramscaled)

            #exp[n][i].parameter = (F11 + recall1)/(runtimescaled + classspeedscaled + ramscaled)

            #parameter      = (F11 + recall1)/((runtime-minruntime)/(maxruntime-minruntime) + (classspeed-minclassspeed)/(maxclassspeed-minclassspeed) + (maxram-totalminram)/(totalmaxram-totalminram))*instances/maxinstances
            #exp[n][i].parameter  = (exp[n][i].report['f1-score'][1]*exp[n][i].report['recall'][1])/(exp[n][i].runtime/maxruntime*exp[n][i].classspeed/maxclassspeed*exp[n][i].maxram/totalmaxram)*exp[n][i].instances/maxinstances

            experiments_sorted.append(exp[n][i])

    print('\n\tF11 max: {}\n\tF11 min: {}\n\n\tRecall1 max: {}\n\tRecall1 min: {}\n\n\tRun-time max: {}\n\tRun-time min: {}\n\n\tClass-speed max: {}\n\tClass-speed min: {}\n\n\tRAM max: {}\n\tRAM min: {}\n'.format(maxf11,minf11,maxrecall1,minrecall1,maxruntime,minruntime,maxclassspeed,minclassspeed,totalmaxram,totalminram))
    print('\nAGM:\n\tF11 min: {}\n\tF11 max: {}\n\tRecall1 min: {}\n\tRecall1 max: {}\n\tInstances min: {}\n\tInstances max: {}\n'.format(minf11AGM,maxf11AGM,minrecall1AGM,maxrecall1AGM,mininstancesAGM,maxinstancesAGM))
    print('\nCAIA:\n\tF11 min: {}\n\tF11 max: {}\n\tRecall1 min: {}\n\tRecall1 max: {}\n\tInstances min: {}\n\tInstances max: {}\n'.format(minf11CAIA,maxf11CAIA,minrecall1CAIA,maxrecall1CAIA,mininstancesCAIA,maxinstancesCAIA))


    #print('{}'.format(experiments_sorted))
    #for x in experiments_sorted:
    #    print('{}'.format(x.parameter))
    #input('...')
    experiments_sorted.sort(key=lambda x: x.parameter3,reverse=True)
    #print('{}'.format(experiments_sorted))
    #for x in experiments_sorted:
    #    print('{}'.format(x.parameter))
    #input('...')


    print('>>> Converting memory-usage values')
    convert = ['"used"','"total"','"cach"','"free"','"used".1','"free".1'] # features to convert (RAM, SWAP)

    for n in range(0,len(folders)):
        for i in range (0,len(exp[n])):
            rows = exp[n][i].dstat.shape[0]
            for feature in convert:
                for row in range(0,rows):
                    tmp = exp[n][i].dstat[feature][row]/1000**2
                    exp[n][i].dstat.at[row,feature]=tmp

    # CREATE MEMORY USAGE PLOTS
    print('>>> Creating graphs memory-usage')
    count = 0
    for n in range(0,len(folders)):
        #for i in range (0,1): # test loop only one experiment
        for i in range (0,len(exp[n])):
            count += 1
            ticks   = []
            labels  = []

            #png_file = 'figures/RAM-usage_{}_{}_{}_steps{}.png' # template for PNG filename
            png_file = 'figures/RAM-usage_{}_{}_{}_steps{}.pdf' # template for PDF filename (PDF is easier to include in LaTeX!)


            # create list of relevant timestamps and labels
            for j in range(1,exp[n][i].time['epochtime'].shape[0]-1): # excluding start & end timestamps
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
            title_vector      = vector[exp[n][i].vector]
            title_mode        = cfg.samplingmode[exp[n][i].mode]
            # nicer output for plot titles
            if exp[n][i].sampling     == 'flowbased':   samplingtype = 'flow-based'
            elif exp[n][i].sampling   == 'packetbased': samplingtype = 'packet-based'

            title = '{}, {}\n'.format(title_vector,samplingtype)

            if title_steps == 0: subtitle = '(unsampled)'
            else:                subtitle = '({}, n={})'.format(title_mode,title_steps)

            # plot graphs
            fig = plt.figure(figsize=(21.0,9.0))
            plt.plot(exp[n][i].dstat['"epoch"'],exp[n][i].dstat['"total"'], color = '#000000',label='RAM total',linewidth=3)
            plt.plot(exp[n][i].dstat['"epoch"'],exp[n][i].dstat['"used"'],  color = '#9191AA',label='RAM used',linewidth=2)
            #plt.plot(exp[n][i].dstat['"epoch"'],exp[n][i].dstat['"cach"'],  color = '#AEB6BF',label='RAM cached',linewidth=2)
            #plt.plot(exp[n][i].dstat['"epoch"'],exp[n][i].dstat['"used".1'],color = '#566573',label='SWAP used',linewidth=2)

            # plot segments
            style = 'dotted'
            color = '#000000'
            #for j in (range (1,len(labels)-1)):
            for j in (range (0,len(labels))): # excludes start/end timestamps
                plt.axvline(x=stamps[j][0],ymin=0,ymax=1,linestyle=style,color=color) # plot vertical lines

            # plot labels
            plt.xticks(timestamps,timelabels,rotation=80,fontsize=16) # create x-axis ticks
            #plt.xlabel('segments', fontsize=14)
            #plt.ylabel('memory-usage',fontsize=14)
            #plt.title(title,ha='center',fontsize=16) # set title
            #plt.suptitle(subtitle,x=0.515,y=0.925,ha='center',fontsize=10) # suptitle position between 0 and 1
            plt.legend(loc='best')
            plt.tight_layout() # increase space below x-axis for proper labeling

            if verbose: print('\t<< {}'.format(png_file.format(title_vector,title_sampling,title_mode,title_steps)))
            plt.savefig(png_file.format(title_vector,title_sampling,title_mode,title_steps)) # save plot to file

            # show/hide plots
            if (not plot): plt.close(fig) # close fig directly to not show it on script execution
            else: plt.show() # show single plot


    # CREATE SINGLE SPIDER CHARTS
    print('>>> Creating graphs spider-chart')
    count = 0
    for n in range(0,len(folders)):
        #for i in range (0,1): # test loop only one experiment
        for i in range (0,len(exp[n])):
            count += 1
            #png_file = 'figures/Spiderchart_{}_{}_{}_steps{}.png'
            png_file = 'figures/Spiderchart_{}_{}_{}_steps{}.pdf'


            # set plot parameters
            plt.rcParams['xtick.major.pad']=30 # move labes a bit outside of outer circle
            #plt.rcParams['axes.titlepad']=-5
            #plt.rcParams['xtick.labelsize']=15

            # relevant values for chart creation
            CPU_max     = exp[n][i].dstat['"usr"'].max()
            RAM_total   = exp[n][i].dstat['"total"'].max() # total RAM available
            RAM_used    = exp[n][i].maxram/totalmaxram*100
            RAM_cached  = exp[n][i].dstat['"cach"'].max()/RAM_total*100
            accuracy    = float(exp[n][i].result['summary'][2])*100
            recall0     = exp[n][i].report['recall'][0]*100
            recall1     = exp[n][i].report['recall'][1]*100
            prec0       = exp[n][i].report['precision'][0]*100
            prec1       = exp[n][i].report['precision'][1]*100
            f10         = exp[n][i].report['f1-score'][0]*100
            f11         = exp[n][i].report['f1-score'][1]*100
            runtime     = exp[n][i].runtime/maxruntime*100
            speed       = exp[n][i].classspeed/maxclassspeed*100
            style       = 'solid'
            modelsize   = exp[n][i].modelsize/maxmodelsize*100

            # use maximum obtainable instances based on experiments feature-vector
            if vector[exp[n][i].vector][0:3] == 'AGM':
                instances   = exp[n][i].report['support'][4]/maxinstancesAGM*100
            elif vector[exp[n][i].vector][0:3] == 'CAI':
                instances   = exp[n][i].report['support'][4]/maxinstancesCAIA*100

            # graph title & subtitle
            title_sampling    = exp[n][i].sampling
            title_steps       = exp[n][i].steps
            title_vector      = vector[exp[n][i].vector]
            title_mode        = cfg.samplingmode[exp[n][i].mode]
            # nicer output for title
            if exp[n][i].sampling     == 'flowbased':   samplingtype = 'flow-based'
            elif exp[n][i].sampling   == 'packetbased': samplingtype = 'packet-based'

            #title = '{}, {}\n\n'.format(title_vector,samplingtype)
            title = IDroman[exp[n][i].idnumber]
            if title_steps == 0: subtitle = 'unsampled'
            else:                subtitle = '{}, n={}'.format(title_mode,title_steps)

            # VALUES AND LABELS
            # forge polar-compatible values and angles
            value   = [
                #speed,
                #instances,
                modelsize,
                RAM_used,
                #accuracy,
                #f10,
                #recall0,
                #prec0,
                f11,
                recall1,
                prec1,
                runtime
                ]

            # label parameters
            #tmptr = '$_{(38.562\%)}$'
            #rt = str(runtime)
            #tmptr = f"${{_{str(runtime)}\%}}$"ma
            labels = [
                #'Speed\n({}%)'.format(format(speed,".2f")),
                #'Inst.\n{}%'.format(format(instances,".1f")),
                'model\n{}%'.format(format(modelsize,".1f")),
                'mem\n{}%'.format(format(RAM_used,".1f")),
                #'Accuracy\n({}%)'.format(format(accuracy,".2f")),
                #'F1-score "0"\n({}%)'.format(format(f10,".2f")),
                #'Recall "0"\n({}%)'.format(format(recall0,".2f")),
                #'Precision "0"\n({}%)'.format(format(prec0,".2f")),
                '$F_1$\n{}%'.format(format(f11,".1f")),
                '$Rec_1$\n{}%'.format(format(recall1,".1f")),
                '$Prec_1$\n{}%'.format(format(prec1,".1f")),
                #'Runtime\n({}%)'.format(format(runtime,".2f"))
                '$t_R$\n{}%'.format(format(runtime,".1f"))
                #'$t_R$\n{}'.format(format(tmptr))


                ]

            N       = len(value) # number of different parameters to be displayed
            value   += value[:1] # close value "circle" for sider-chart
            angles  = [n / float(N) * 2 * pi for n in range(N)]
            angles  += angles[:1] # close angle "circle" for spider-chart

            fig = plt.figure(figsize=(10.5,11.5))

            ax  = plt.subplot(polar=True)
            ax.set_ylim(0,100) # limit y-values to 100% for similar plots
            ax.set_rlabel_position(49)

            plt.yticks([0,25,50,60,70,80,90,100], color='grey', size=12)
            #plt.polar(angles,value,linestyle=style,linewidth=3, color='#9191AA')
            plt.polar(angles,value,linestyle=style,linewidth=5, color='#000000')
            plt.xticks(angles[:-1],labels,fontsize=22) # pass all angles except last (its the repetition of the first value)

            # maniupulate outer 100% linewidth
            gridlines = ax.yaxis.get_gridlines()
            gridlines[7].set_color('black')
            gridlines[7].set_linewidth(2.5)

            plt.title(title,ha='center',fontsize=64) # set title
            #plt.suptitle(subtitle,x=0.515,y=0.965,ha='center',fontsize=11) # suptitle position between 0 and 1

            # shrink chart box to enable legend positioning blow plot
            #box = ax.get_position()
            #ax.set_position([box.x0, box.y0,box.width, box.height])
            if verbose: 
                #print('\t<< {}'.format(png_file.format(vector[exp[n][i].vector],samplingtype)))
                print('\t<< {}'.format(png_file.format(vector[exp[n][i].vector],samplingtype,cfg.samplingmode[exp[n][i].mode],exp[n][i].steps)))
                print('\t\t< ID: {}'.format(exp[n][i].idnumber))
            plt.savefig(png_file.format(vector[exp[n][i].vector],samplingtype,cfg.samplingmode[exp[n][i].mode],exp[n][i].steps)) # save plot to file

            # show/hide plots
            if (not plot): plt.close(fig) # close fig directly to not show it on script execution
            else: plt.show() # show single plot


    # COMPARISON SPIDER CHART PLOTS
    print('>>> Creating graphs for comparison, bundle experiments')

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

    # https://coolors.co/ffae03-e67f0d-fe4e00-e9190f-ff0f80 ORANGE PALETTE
    paletteorange = []
    paletteorange.append('#FF0F80')
    paletteorange.append('#F41448')
    paletteorange.append('#FE4E00')
    paletteorange.append('#E67F0D')
    paletteorange.append('#FFAE03')
    paletteorange = list(reversed(paletteorange))

    # https://coolors.co/000505-3b3355-5d5d81-bfcde0-fefcfd BLUE PALETTE
    paletteblue = []
    paletteblue.append('#1D1D28')
    paletteblue.append('#37374C')
    paletteblue.append('#9191AA')
    paletteblue.append('#C5C5DB')
    paletteblue = list(reversed(paletteblue)) # plot light colors first

    # https://coolors.co/52d1dc-475b5a-8d8e8e-a3a9aa-bbbbbf GRAY PALETTE
    palettegray = []
    palettegray.append('#4F4F5A')
    #palettegray.append('#5F5F67')
    palettegray.append('#6E6E74')
    #palettegray.append('#7E7E81')
    palettegray.append('#8D8D8E')
    #palettegray.append('#99999C')
    #palettegray.append('#A5A5A9')
    #palettegray.append('#B0B0B4')
    palettegray.append('#BBBBBE')

    # https://coolors.co/eef0f2-c6c7c4-a2999e-846a6a-353b3c GRAY PALETTE 2
    # https://coolors.co/8bc95f-44fc54-6cd426-2f911d-346617 GREEN PALETTE



    # FEATURE-VECTORS COMPARISON PLOTS
    print('\t<< feature-vectors')
    for i in range(0,len(vectors)):
        print('\t\t< {}'.format(cfg.vectors[vectors[i]]))

    count = 0
    compare = exp.copy() # copy all experiment data
    for v in vectors: # iterate experiments with similar feature-vector
        for m in modes: # iterate modes
            tmp = []

            tmp_color = palette.copy()
            tmpgray = palettegray.copy()
            tmpblue = paletteblue.copy()
            tmporange = paletteorange.copy()

            plt.rcParams['xtick.major.pad'] = 15 # move labes a bit outside of outer 100% circle

            count += 1
            #png_file = 'figures/Spiderchart-Comparison_{}_{}_{}.png'
            png_file = 'figures/Spiderchart-Comparison_{}_{}_{}.pdf'


            for n in range(0,len(folders)): # iterate folders
                for i in range (0,len(exp[n])):
                    if exp[n][i].vector == v and exp[n][i].mode == m and exp[n][i].steps > 0:
                        tmp.append(exp[n][i])
                    comparemode = exp[n][i].sampling

            for tmpunsampled in experiments_unsampled: # search appropriate unsampled comparison
                if tmpunsampled.vector == v and len(tmp)>0:
                    tmp.append(tmpunsampled)
                    break

            # lists to accumulate values & labels for plots
            compare_values = []
            compare_angles = []
            compare_labels  = []
            compare_colors = []
            compare_sampling = []
            compare_style = []
            compare_width = []

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
                f11         = x.report['f1-score'][1]*100
                speed       = x.classspeed/maxclassspeed*100
                modelsize   = x.modelsize/maxmodelsize*100

                # set specific style for unsampled experiments
                if x.steps==0 and x.sampling=='flowbased': style = 'solid'
                elif x.steps==0 and x.sampling=='packetbased': style = 'solid'
                else: style       = x.style # plot-style

                # nicer output for legend
                if x.sampling     == 'flowbased':   samplingtype = 'flow-based'
                elif x.sampling   == 'packetbased': samplingtype = 'packet-based'

                # forge polar-compatible values and angles
                #value   = [RAM_used,RAM_cached,CPU_max,accuracy,recall0,prec0,recall1,prec1,runtime]
                #value   = [RAM_used,accuracy,recall0,prec0,recall1,prec1,runtime]
                value   = [
                    #speed,
                    modelsize,
                    RAM_used,
                    #accuracy,
                    #f10,
                    #recall0,
                    #prec0,
                    f11,
                    recall1,
                    prec1,
                    runtime
                ]

                N       = len(value) # number of different parameters shown in spider-chart
                value   += value[:1] # close value "circle" for sider-chart
                angles  = [n / float(N) * 2 * pi for n in range(N)]
                angles  += angles[:1] # close angle "circle" for spider-chart

                # pick (random) color from list
                if x.steps == 0: color = 'black'
                else:
                    #color = random.choice(tmp_color)
                    #tmp_color.remove(color)
                    for c in tmpblue:
                        color = c
                        tmpblue.remove(color)
                        break

                # title & label
                title = '{}, {}\n\n'.format(vector[x.vector],samplingtype)
                if x.steps > 0: title_mode        = cfg.samplingmode[x.mode]
                #print(title_mode)
                #input('title.mode')
                subtitle = '{}'.format(title_mode)
                if x.steps == 0:
                    label = 'unsampled'
                    #style = (0,(3,1,1,1))
                    style = (0,(1,1)) # densely dotted

                else:
                    label = 'n = {}'.format(x.steps)
                    style = 'solid'
                #else: label = 'n = {}, {}'.format(x.steps,cfg.samplingmode[x.mode])

                if x.steps == 0: width = 3.5
                else: width = 2

                # create lists for comparison-plot
                compare_values.append(value)
                compare_angles.append(angles)
                compare_colors.append(color)
                compare_labels.append(label)
                compare_style.append(style)
                compare_width.append(width)

                plt.figure(figsize=(10.0,10.0))
                ax = plt.subplot(polar=True)


                for c in range(0,len(compare_values)): # create plots
                    plt.polar(compare_angles[c],compare_values[c],linewidth=compare_width[c],linestyle=compare_style[c],label=compare_labels[c],color=compare_colors[c])
                    #plt.polar(compare_angles[c],compare_values[c],linewidth=compare_width[c],linestyle='solid',label=compare_labels[c],color=compare_colors[c])

                stats = [
                        #'Speed',
                        'Model\nSize',
                        '\nRAM',
                        #'Accuracy\n({}%)'.format(format(accuracy,".2f")),
                        #'F1-score "0"\n({}%)'.format(format(f10,".2f")),
                        #'Recall "0"\n({}%)'.format(format(recall0,".2f")),
                        #'Precision "0"\n({}%)'.format(format(prec0,".2f")),
                        'F1-score "1"',
                        'Recall "1"',
                        'Precision "1"',
                        'Runtime'
                    ]

                plt.xticks(compare_angles[0][:-1],stats)
                ax.set_rlabel_position(58)
                plt.yticks([0,25,50,65,75,85,95], color='grey', size=9)
                plt.ylim(0,100)
                plt.title(title,ha='center',fontsize=16) # set title
                plt.suptitle(subtitle,x=0.515,y=0.925,ha='center',fontsize=11) # suptitle position between 0 and 1


                # shrink chart box to enable legend positioning below plot
                box = ax.get_position()
                ax.set_position([box.x0, box.y0 + box.height * 0.15,box.width, box.height * 0.85])

                # bottom legend
                bottomlegend = plt.legend(bbox_to_anchor=(0., -0.15, 1, .102), loc='lower left',ncol=2, mode="expand", borderaxespad=0.)
                ax = plt.gca().add_artist(bottomlegend)

                if verbose: print('\t\t\t< {}'.format(png_file.format(vector[x.vector],samplingtype,title_mode)))
                plt.savefig(png_file.format(vector[x.vector],samplingtype,title_mode)) # save plot to file

                # show/hide plots
                if (not plot): plt.close(fig) # close fig directly to not show it on script execution
                else: plt.show() # show single plot

    compare_values = []
    compare_angles = []
    compare_labels  = []
    compare_colors = []
    compare_style = []
    compare_width = []

    tmp_color = palette.copy()
    tmpgray = palettegray.copy()
    tmpblue = paletteblue.copy()
    tmporange = paletteorange.copy()

    print('\t<< Parameter ranking')
    i = 0
    for x in experiments_sorted:
        i +=1
        if i == 7: break

        print('\t\t< {}'.format(format(x.parameter3,".2f")))

        plt.rcParams['xtick.major.pad'] = 15 # move labes a bit outside of outer 100% circle
        #png_file = 'figures/Spiderchart-Comparison_Parameter-Ranking.png'
        png_file = 'figures/Spiderchart-Comparison_Parameter-Ranking.pdf'


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
        f11         = x.report['f1-score'][1]*100
        speed       = x.classspeed/maxclassspeed*100
        modelsize   = x.modelsize/maxmodelsize*100

        # set specific style for unsampled experiments
        if x.sampling=='flowbased': style = 'solid'
        elif x.sampling=='packetbased': style = 'dotted'

        # nicer output for legend
        if x.sampling     == 'flowbased':   samplingtype = 'flow-based'
        elif x.sampling   == 'packetbased': samplingtype = 'packet-based'

        # forge polar-compatible values and angles
        #value   = [RAM_used,RAM_cached,CPU_max,accuracy,recall0,prec0,recall1,prec1,runtime]
        #value   = [RAM_used,accuracy,recall0,prec0,recall1,prec1,runtime]
        value   = [
            #speed,
            modelsize,
            RAM_used,
            #accuracy,
            #f10,
            #recall0,
            #prec0,
            f11,
            recall1,
            prec1,
            runtime
        ]

        N       = len(value) # number of different parameters shown in spider-chart
        value   += value[:1] # close value "circle" for sider-chart
        angles  = [n / float(N) * 2 * pi for n in range(N)]
        angles  += angles[:1] # close angle "circle" for spider-chart

        # pick (random) color from list
        if x.steps == 0: color = 'black'
        else:
            for c in tmporange:
                color = c
                tmporange.remove(color)
                break

        # title & label
        title = 'Parameter Ranking\n'
        label = '#{}: {}'.format(i,IDroman[x.idnumber])

        #if x.steps > 0: label = '#{}: {}, {}, n={}'.format(i,vector[x.vector],cfg.samplingmode[x.mode],x.steps)
        #else: label = '#{}: {}, unsampled'.format(i,vector[x.vector])


        if x.steps == 0: width = 2
        else: width = 2

        if i == 1: width = 3
        elif i ==2: width = 2.5
        elif i == 3: width = 2
        else: width = 1.5

        # create lists for comparison-plot
        compare_values.append(value)
        compare_angles.append(angles)
        compare_colors.append(color)
        compare_labels.append(label)
        compare_style.append(style)
        compare_width.append(width)

    plt.figure(figsize=(10.0,10.0))
    ax = plt.subplot(polar=True)

    for c in range(0,len(compare_values)): # create plots
        plt.polar(compare_angles[c],compare_values[c],linewidth=compare_width[c],linestyle=compare_style[c],label=compare_labels[c],color=compare_colors[c])
        #plt.polar(compare_angles[c],compare_values[c],linewidth=compare_width[c],linestyle='solid',label=compare_labels[c],color=compare_colors[c])

    stats = [
            #'Speed',
            'Model\nSize',
            '\nmem',
            #'Accuracy\n({}%)'.format(format(accuracy,".2f")),
            #'F1-score "0"\n({}%)'.format(format(f10,".2f")),
            #'Recall "0"\n({}%)'.format(format(recall0,".2f")),
            #'Precision "0"\n({}%)'.format(format(prec0,".2f")),
            'F1-score "1"',
            'Recall "1"',
            'Precision "1"',
            'Runtime'
        ]

    plt.xticks(compare_angles[0][:-1],stats)
    ax.set_rlabel_position(58)
    plt.yticks([0,25,50,60,75,85,95], color='grey', size=9)
    plt.ylim(0,100)
    plt.title(title,ha='center',fontsize=16) # set title
    #plt.suptitle(subtitle,x=0.515,y=0.925,ha='center',fontsize=11) # suptitle position between 0 and 1


    # shrink chart box to enable legend positioning below plot
    box = ax.get_position()
    ax.set_position([box.x0, box.y0 + box.height * 0.15,box.width, box.height * 0.85])

    # actual legend
    #legend = plt.legend(loc='best')
    #ax = plt.gca().add_artist(legend)

    # forge top legend to display different linestyles for flow-based and packet-based sampling
    flowbased_legend   = Line2D([0],[0], label='flow-based',color='k',linestyle='-')
    packetbased_legend = Line2D([0],[0], label='packet-based',color='k',linestyle=':')
    handles, labels = plt.gca().get_legend_handles_labels()
    handles.extend([flowbased_legend,packetbased_legend])

    # https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.legend.html
    # top legend
    toplegend = plt.legend(bbox_to_anchor=(0., 1.05, 1, .102), loc='upper left',ncol=2, mode="expand", borderaxespad=0., handles=[flowbased_legend,packetbased_legend])
    ax = plt.gca().add_artist(toplegend)

    # bottom legend
    bottomlegend = plt.legend(bbox_to_anchor=(0., -0.15, 1, .102), loc='lower left',ncol=2, mode="expand", borderaxespad=0.)
    ax = plt.gca().add_artist(bottomlegend)

    if verbose: print('\t\t\t< {}'.format(png_file))
    plt.savefig(png_file) # save plot to file

    # show/hide plots
    if (not plot): plt.close(fig) # close fig directly to not show it on script execution
    else: plt.show() # show single plot


    # CREATE TABLE
    # first column contains different sampling/techniques, vectors & steps
    columns_list = [
        'parameter',
        'parameter2',
        'parameter3',
        'parameter4',
        #'parameter5',
        'sampling',
        'vector',
        'pattern',
        'experiment',
        'accuracy-score',
        'recall 0',
        'recall 1',
        'precision0',
        'precision1',
        'F1 0',
        'F1 1',
        'run-time\n(s)',
        'class-time\n(s)',
        'instances',
        'class-speed\n(instances/s)',
        'maxRAM\n(MB)',
        'trees',
        'maxdepth',
        'maxleaves',
        'modelsize\n(MB)',
        'PCA_n',
        'PCA_var',
        'experiment-configuration'
        ]

    # initialize empty dataframe with given columns
    chart = pd.DataFrame(columns=columns_list)

    # fill chart with data, therefore cycle through experiment configurations
    print('>>> Creating comparison table')
    count = 0
    for n in range(0,len(folders)):
        for i in range (0,len(exp[n])):
            tmp = exp[n][i] # current experiment

            title = '{}'.format(cfg.samplingmode[tmp.mode])
            if tmp.steps == 0: steps = 'unsampled'
            else:              steps = 'n = {}'.format(tmp.steps)
            featurevector   = vector[tmp.vector]
            accuracyscore   = float(tmp.result['summary'][2])
            recall0         = tmp.report['recall'][0]
            recall1         = tmp.report['recall'][1]
            precision0      = tmp.report['precision'][0]
            precision1      = tmp.report['precision'][1]
            F10             = tmp.report['f1-score'][0]
            F11             = tmp.report['f1-score'][1]
            runtime         = tmp.runtime
            classtime       = tmp.classtime
            instances       = tmp.report['support'][4]
            classspeed      = tmp.classspeed
            maxram          = tmp.maxram
            file            = tmp.file
            sampling        = tmp.sampling
            trees           = tmp.result['summary'][6]
            maxdepth        = tmp.maxdepth
            maxleaves       = tmp.maxleaves
            modelsize       = tmp.modelsize
            pca_n           = tmp.pca_n
            pca_var         = tmp.pca_var
            # various parameters
            #parameter       = (F11*recall1)/(runtime/maxruntime*classspeed/maxclassspeed*maxram/totalmaxram)*instances/maxinstances
            #parameter      = (F11 + recall1)/((runtime-minruntime)/(maxruntime-minruntime) + (classspeed-minclassspeed)/(maxclassspeed-minclassspeed) + (maxram-totalminram)/(totalmaxram-totalminram))*instances/maxinstances
            parameter       = tmp.parameter
            #parameter2      = (F11 + recall1)/(runtime/maxruntime + classspeed/maxclassspeed + maxram/totalmaxram)
            #parameter2      = (F11 + recall1)/((runtime-minruntime)/(maxruntime-minruntime) + (classspeed-minclassspeed)/(maxclassspeed-minclassspeed) + (maxram-totalminram)/(totalmaxram-totalminram))
            parameter2      = tmp.parameter2
            parameter3      = tmp.parameter3
            parameter4      = tmp.parameter4

            #parameter3      = (F11 + recall1)/(runtime/maxruntime + classspeed/maxclassspeed + maxram/totalmaxram)*instances/maxinstances
            #parameter4      = (F11+recall1+precision1)/(runtime/maxruntime + classspeed/maxclassspeed + maxram/totalmaxram)*instances/maxinstances
            #parameter5      = (F11*recall1)/(runtime/maxruntime + classspeed/maxclassspeed + maxram/totalmaxram)*instances/maxinstances # maybe add normalized model filesize?

            experimentconf = '{}, {}: {}, {}'.format(sampling,featurevector,title,steps)

            # filename of saved table
            savecsv         = 'figures/comparison.csv'

            # better wording for final table
            if sampling     == 'flowbased':   samplingtype = 'flow-based'
            elif sampling   == 'packetbased': samplingtype = 'packet-based'

            # increase readability for comparison.csv
            runtime         = format(tmp.runtime,".2f")
            classtime       = format(tmp.classtime,".2f")
            classspeed      = format(tmp.classspeed,".2f")
            instances       = int(tmp.report['support'][4])
            maxram          = format(tmp.maxram,".2f")
            modelsize       = format(tmp.modelsize,".2f")
            parameter       = format(parameter,".2f")
            parameter2      = format(parameter2,".2f")
            parameter4      = format(parameter4,".2f")
            pca_var         = format(tmp.pca_var,".2f")


            # create dataframe with current experiments values
            tmpdf = pd.DataFrame([[parameter,parameter2,parameter3,parameter4,samplingtype,featurevector,steps,title,accuracyscore,recall0,recall1,precision0,precision1,F10,F11,runtime,classtime,instances,classspeed,maxram,trees,maxdepth,maxleaves,modelsize,pca_n,pca_var,experimentconf]],columns=columns_list)
            #if tmp.steps > 0: chart = chart.append(tmpdf) # append current experiment data to final table
            chart = chart.append(tmpdf) # append current experiment data to final table


    # sort table based on samplingtype and 'experiments'
    chart = chart.sort_values(by=['vector','sampling'])
    print('>>> Saving comparison table: {}'.format(savecsv))
    chart.to_csv(savecsv)
    if verbose: print('\t<< {}\n{}\n'.format(savecsv,chart))

    exit()



























    print('\t<< Sampling-steps')
    for i in range(0,len(steps)):
        print('\t\t< n = {}'.format(steps[i]))

    count = 0
    for s in steps: # accumulate experiments with similar sampling steps
        tmp = []
        tmp_color = palette.copy()
        count += 1
        png_file = 'figures/Spiderchart-Comparison_steps_figure{}.png'

        for n in range(0,len(folders)):
            for i in range (0,len(exp[n])):
                if exp[n][i].steps == s:
                    tmp.append(exp[n][i])

        # create lists for comparison-plot
        compare_values = []
        compare_angles = []
        compare_labels  = []
        compare_colors = []
        compare_style = []

        # SORT EXPERIMENTS FOR INCREASED LEGEND READABILITY
        tmp = sorted(tmp, key=lambda x: (x.sampling,x.vector))

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
            style       = x.style # plot-style
            speed       = x.classspeed/maxclassspeed*100

            # nicer output for legend
            if x.sampling     == 'flowbased':   samplingtype = 'flow-based'
            elif x.sampling   == 'packetbased': samplingtype = 'packet-based'

            # forge polar-compatible values and angles
            #value   = [RAM_used,RAM_cached,CPU_max,accuracy,recall0,prec0,recall1,prec1,runtime]
            value   = [RAM_used,accuracy,recall0,prec0,recall1,prec1,runtime]

            N       = len(value) # number of different parameters shown in spider-chart
            value   += value[:1] # close value "circle" for sider-chart
            angles  = [n / float(N) * 2 * pi for n in range(N)]
            angles  += angles[:1] # close angle "circle" for spider-chart

            # pick random color from list
            color = random.choice(tmp_color)
            tmp_color.remove(color)

            # title & label
            if s == 0: title = 'unsampled'
            else:      title = 'n = {}'.format(s)
            #label = '{}, {}, {}'.format(vector[x.vector],samplingtype,cfg.samplingmode[x.mode])
            label = '{}, {}'.format(vector[x.vector],cfg.samplingmode[x.mode])


            # create lists for comparison-plot
            compare_values.append(value)
            compare_angles.append(angles)
            compare_colors.append(color)
            compare_labels.append(label)
            compare_style.append(style)

        plt.figure(figsize=(12.0,12.0))
        ax = plt.subplot(polar=True)
        width = 2

        for c in range(0,len(compare_values)): # create plots
            plt.polar(compare_angles[c],compare_values[c],linewidth=width,linestyle=compare_style[c],label=compare_labels[c],color=compare_colors[c])

        #stats = ['used RAM','cached RAM','CPU usage','Accuracy','Recall\n"0"','Precision\n"0"','Recall\n"1"','Precision\n"1"','Runtime']
        stats = ['used RAM','Accuracy','Recall\n"0"','Precision\n"0"','Recall\n"1"','Precision\n"1"','Runtime']
        plt.xticks(compare_angles[0][:-1],stats)
        ax.set_rlabel_position(58)
        plt.yticks([0,25,50,75,100], color='grey', size=10)
        plt.ylim(0,100)
        plt.title(title,ha='center',fontsize=16) # set title

        # shrink chart box to enable legend positioning below plot
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.15,box.width, box.height * 0.85])

        # actual legend
        #legend = plt.legend(loc='best')
        #ax = plt.gca().add_artist(legend)

        # forge top legend to display different linestyles for flow-based and packet-based sampling
        flowbased_legend   = Line2D([0],[0], label='flow-based sampling',color='k',linestyle=':')
        packetbased_legend = Line2D([0],[0], label='packet-based sampling',color='k',linestyle='-')
        handles, labels = plt.gca().get_legend_handles_labels()
        handles.extend([flowbased_legend,packetbased_legend])

        # https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.legend.html
        # top legend
        toplegend = plt.legend(bbox_to_anchor=(0., 1.05, 1, .102), loc='upper left',ncol=2, mode="expand", borderaxespad=0., handles=[flowbased_legend,packetbased_legend])
        ax = plt.gca().add_artist(toplegend)

        # bottom legend
        bottomlegend = plt.legend(bbox_to_anchor=(0., -0.15, 1, .102), loc='lower left',ncol=2, mode="expand", borderaxespad=0.)
        ax = plt.gca().add_artist(bottomlegend)

        #plt.legend(loc='best',handles=handles)

        if verbose: print('\t\t\t< {}'.format(png_file.format(count)))
        plt.savefig(png_file.format(count)) # save plot to file

        # show/hide plots
        if (not plot): plt.close(fig) # close fig directly to not show it on script execution
        else: plt.show() # show single plot













    # FEATURE-VECTORS BUNDLE
    print('\t<< feature-vectors')
    for i in range(0,len(vectors)):
        print('\t\t< {}'.format(cfg.vectors[vectors[i]]))

    count = 0
    compare = exp.copy() # copy all experiment data
    for v in vectors: # accumulate experiments with similar feature-vector
        tmp = []

        tmp_color = palette.copy()
        tmpgray = palettegray.copy()
        tmpblue = paletteblue.copy()
        tmporange = paletteorange.copy()

        count += 1
        png_file = 'figures/Spiderchart-Comparison_vectors_figure{}.png'

        for n in range(0,len(folders)): # iterate folders
            for i in range (0,len(exp[n])):
                if exp[n][i].vector == v:
                    tmp.append(exp[n][i])

        # lists to accumulate values & labels for plots
        compare_values = []
        compare_angles = []
        compare_labels  = []
        compare_colors = []
        compare_sampling = []
        compare_style = []
        compare_width = []

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
            # set specific style for unsampled experiments
            if x.steps==0 and x.sampling=='flowbased': style = 'solid'
            elif x.steps==0 and x.sampling=='packetbased': style = 'solid'
            else: style       = x.style # plot-style

            # nicer output for legend
            if x.sampling     == 'flowbased':   samplingtype = 'flow-based'
            elif x.sampling   == 'packetbased': samplingtype = 'packet-based'

            # forge polar-compatible values and angles
            #value   = [RAM_used,RAM_cached,CPU_max,accuracy,recall0,prec0,recall1,prec1,runtime]
            #value   = [RAM_used,accuracy,recall0,prec0,recall1,prec1,runtime]
            value   = [
                speed,
                RAM_used,
                #accuracy,
                #f10,
                #recall0,
                #prec0,
                f11,
                recall1,
                prec1,
                runtime
            ]

            N       = len(value) # number of different parameters shown in spider-chart
            value   += value[:1] # close value "circle" for sider-chart
            angles  = [n / float(N) * 2 * pi for n in range(N)]
            angles  += angles[:1] # close angle "circle" for spider-chart

            # pick (random) color from list
            if x.steps == 0: color = 'black'
            else:
                color = random.choice(tmp_color)
                tmp_color.remove(color)
                if cfg.vectors[v][0:3] == 'AGM' and x.sampling == 'flowbased':
                    if cfg.samplingmode[x.mode][0:5] == 'every':
                        color = random.choice(tmporange)
                        tmporange.remove(color)
                    elif cfg.samplingmode[x.mode][0:8] == 'sample n':
                        color = random.choice(tmpblue)
                        tmpblue.remove(color)
                    else:
                        color = random.choice(tmpgray)
                        tmpgray.remove(color)
                        style = 'solid'
                elif cfg.vectors[v][0:3] == 'AGM' and x.sampling == 'packetbased':
                    if cfg.samplingmode[x.mode][0:5] == 'every':
                        color = random.choice(tmpblue)
                        tmpblue.remove(color)
                    else:
                        color = random.choice(tmpgray)
                        tmpgray.remove(color)
                        style = 'solid'
                elif cfg.vectors[v][0:4] == 'CAIA' and x.sampling == 'packetbased':
                    if cfg.samplingmode[x.mode][0:5] == 'every':
                        color = random.choice(tmporange)
                        tmporange.remove(color)
                    else:
                        color = random.choice(tmpgray)
                        tmpgray.remove(color)
                        style = 'solid'
                elif cfg.vectors[v][0:3] == 'AGM' and x.sampling == 'flowbased':
                    if cfg.samplingmode[x.mode][0:5] == 'every':
                        color = random.choice(tmpblue)
                        tmpblue.remove(color)
                    else:
                        color = random.choice(tmpgray)
                        tmpgray.remove(color)
                        style = 'solid'


            # title & label
            title = '{}, {}\n'.format(vector[x.vector],samplingtype)
            #subtitle = '({}, n={})'.format(title_mode,title_steps)
            if x.steps == 0: label = 'unsampled'
            else: label = 'n = {}, {}'.format(x.steps,cfg.samplingmode[x.mode])

            if x.steps == 0: width = 3.5
            else: width = 2

            # create lists for comparison-plot
            compare_values.append(value)
            compare_angles.append(angles)
            compare_colors.append(color)
            compare_labels.append(label)
            compare_style.append(style)
            compare_width.append(width)


        plt.figure(figsize=(10.0,10.0))
        ax = plt.subplot(polar=True)


        for c in range(0,len(compare_values)): # create plots
            #plt.polar(compare_angles[c],compare_values[c],linewidth=compare_width[c],linestyle=compare_style[c],label=compare_labels[c],color=compare_colors[c])
            plt.polar(compare_angles[c],compare_values[c],linewidth=compare_width[c],linestyle='solid',label=compare_labels[c],color=compare_colors[c])

        #stats = ['used RAM','cached RAM','CPU usage','Accuracy','Recall\n"0"','Precision\n"0"','Recall\n"1"','Precision\n"1"','Runtime']
        #stats = ['used RAM','Accuracy','Recall\n"0"','Precision\n"0"','Recall\n"1"','Precision\n"1"','Runtime']

        stats = [
                'Speed',
                'RAM',
                #'Accuracy\n({}%)'.format(format(accuracy,".2f")),
                #'F1-score "0"\n({}%)'.format(format(f10,".2f")),
                #'Recall "0"\n({}%)'.format(format(recall0,".2f")),
                #'Precision "0"\n({}%)'.format(format(prec0,".2f")),
                'F1-score "1"',
                'Recall "1"',
                'Precision "1"',
                'Runtime'
            ]

        plt.xticks(compare_angles[0][:-1],stats)
        ax.set_rlabel_position(60)
        plt.yticks([0,25,50,75,100], color='grey', size=10)
        plt.ylim(0,100)
        plt.title(title,ha='center',fontsize=16) # set title

        #plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left',ncol=2, mode="expand", borderaxespad=0.)
        #plt.legend(loc='best')

        # shrink chart box to enable legend positioning below plot
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.15,box.width, box.height * 0.85])

        # actual legend
        #legend = plt.legend(loc='best')
        #ax = plt.gca().add_artist(legend)

        # forge top legend to display different linestyles for flow-based and packet-based sampling
        #flowbased_legend   = Line2D([0],[0], label='flow-based sampling',color='k',linestyle=':')
        #packetbased_legend = Line2D([0],[0], label='packet-based sampling',color='k',linestyle='-')
        #handles, labels = plt.gca().get_legend_handles_labels()
        #handles.extend([flowbased_legend,packetbased_legend])

        # https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.legend.html
        # top legend
        #toplegend = plt.legend(bbox_to_anchor=(0., 1.05, 1, .102), loc='upper left',ncol=2, mode="expand", borderaxespad=0., handles=[flowbased_legend,packetbased_legend])
        #ax = plt.gca().add_artist(toplegend)

        # bottom legend
        bottomlegend = plt.legend(bbox_to_anchor=(0., -0.15, 1, .102), loc='lower left',ncol=2, mode="expand", borderaxespad=0.)
        ax = plt.gca().add_artist(bottomlegend)



        if verbose: print('\t\t\t< {}'.format(png_file.format(count)))
        plt.savefig(png_file.format(count)) # save plot to file

        # show/hide plots
        if (not plot): plt.close(fig) # close fig directly to not show it on script execution
        else: plt.show() # show single plot














    # CPU USAGE
    #print('>>> Creating graphs CPU-usage')
    #count = 0
    #for n in range(0,len(folders)):
    #    for i in range (0,len(exp[n])):

    #        count += 1
    #        ticks   = []
    #        labels  = []

    #        png_file = 'figures/CPU-usage_figure{}.png'

    #        # create list of relevant timestamps
    #        #for j in range(0,exp[n][i].time['epochtime'].shape[0]): # includes start/end timestamps
    #        for j in range(1,exp[n][i].time['epochtime'].shape[0]-1): # excludes start/end timestamps
    #            ticks.append(exp[n][i].time['epochtime'][j])
    #            labels.append(exp[n][i].time['segment'][j])

    #        # create tuple containing ticks and labels
    #        stamps = list(zip(ticks,labels))
    #        stamps.sort(key=lambda x: float(x[0]),reverse=False)
    #        timestamps  = [stamp[0] for stamp in stamps]
    #        timelabels = [stamp[1] for stamp in stamps]

    #        # graph title & subtitle
    #        title_sampling    = exp[n][i].sampling
    #        title_steps       = exp[n][i].steps
    #        title_vector      = cfg.vectors[exp[n][i].vector]
    #        title_mode        = cfg.samplingmode[exp[n][i].mode]
    #        # nicer output for title
    #        if exp[n][i].sampling       == 'flowbased':     samplingtype = 'flow-based sampling'
    #        elif exp[n][i].sampling     == 'packetbased':   samplingtype = 'packet-based sampling'

    #        title = '{}\n'.format(samplingtype)
    #        subtitle = '({}, n={})\n{}'.format(title_mode,title_steps,title_vector)

    #        fig = plt.figure(figsize=(21.0,9.0))
    #        plt.plot(exp[n][i].dstat['"epoch"'],exp[n][i].dstat['"usr"'],color = '#000000',label='CPU python')
    #        plt.plot(exp[n][i].dstat['"epoch"'],exp[n][i].dstat['"sys"'],color = '#566573',label='CPU system')

    #        # plot segments
    #        style = 'dotted'
    #        color = '#000000'
    #        #for j in (range (1,len(labels)-1)):
    #        for j in (range (0,len(labels))): # excludes start/end timestamps
    #            plt.axvline(x=stamps[j][0],ymin=0,ymax=1,linestyle=style,color=color) # plot vertical lines

    #        # plot labels
    #        plt.xticks(timestamps,timelabels,rotation=80) # create x-axis ticks
    #        plt.xlabel('segments', fontsize=14)
    #        plt.ylabel('CPU usage',fontsize=14)
    #        plt.title(title,ha='center',fontsize=18) # set title
    #        plt.suptitle(subtitle,x=0.515,y=0.905,ha='center',fontsize=10) # suptitle position between 0 and 1
    #        plt.legend(loc='best')
    #        plt.tight_layout() # increase space below x-axis for proper labeling

    #        if verbose: print('\t<< {}'.format(png_file.format(count)))
    #        plt.savefig(png_file.format(count)) # save plot to file

    #        # show/hide plots
    #        if (not plot): plt.close(fig) # close fig directly to not show it on script execution
    #        else: plt.show() # show single plot