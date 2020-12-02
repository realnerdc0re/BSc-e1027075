# -*- coding: utf-8 -*-
"""
Created on Fri Sep 11 09:25:55 2020

@author: Patrick Resch
"""

from pandas import read_csv
from timeit import default_timer as timer

import numpy as np
import pandas as pd

import subprocess
import os
import re
import sys

# available sampling-modes, used for informational outputs
samplingmode = {1:'every n-th packet',2:'sample & skip n packets',3:'sample first n packets of a flow',4:'sample n, skip n-1, sample n-2 ...'}
# capture files, https://www.unb.ca/cic/datasets/ids-2017.html
filenames = {1:'Monday-WorkingHours',2:'Tuesday-WorkingHours',3:'Wednesday-WorkingHours',4:'Thursday-WorkingHours',5:'Friday-WorkingHours'}


# ARGUMENT PARSING
# command line argument passthrough for better usability
import argparse
parser = argparse.ArgumentParser(description='script for sampling PCAP files via go-flows (flow-based sampling), output is CSV')

# positional arguments
parser.add_argument('mode', metavar = 'mode', type=int,nargs=1,help='select sampling mode: {}'.format(samplingmode))
parser.add_argument('file', metavar = 'file', type=int,nargs=1,help='select file to process: {}'.format(filenames))
parser.add_argument('n', metavar='n', type=int,nargs=1,help='integer used to determine sampling steps')
# optional arguments
parser.add_argument('-v','--verbose', action='store_true', help='output additional informations')
parser.add_argument('--superverbose', action='store_true', help='output additional informations, including loop iteration output')
parser.add_argument('-t','--time', action='store_true', help='measure runtimes')
parser.add_argument('-c','--check', action='store_true', help='check packet-count')
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
def importCSV(csvpath,csvusecols=None,verbose=False,encoding='utf-8'):
    # informational output
    print('\n\n'+40*'~'+' FUNCTION: importCSV '+40*'~')
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
            print('...added\n')
            tmp.append(feature)
        else:
            print('...discarded\n')
    
    if verbose:
        print('\n'+40*'~'+' FUNCTION: perpacketFeatures, summary '+40*'~')
        print('\n\t{}'.format(tmp))
        if (not time): input('\n...')
            
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
                if (not time): input('\n...')
            
            if superverbose:
                print('transformed:\n', dataset[feature][i])
                print('type:\n', type(dataset[feature][i]))
        
    
    if verbose and (not time): input('\n...')
            
    return

# sample first and every n-th package afterwards from given list of features
def flowSampling(dataset,n,features,mode=0,verbose=False,time=False):
    
    #samplingmode = {0: 'every {}-th packet'.format(n), 1: 'sample & skip {} packets'.format(n), 2: 'sample first {} packets of a flow'.format(n), 3: 'sample n, skip n-1, sample n-2 ... (n={})'.format(n)}
    
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
            if mode == 1:
                dataset.at[i,feature] = dataset[feature][i][0::n]
                
                if superverbose:
                        print('\nSampled:')
                        print(len(dataset[feature][i]))
                        print(dataset[feature][i])
                        input('\n...')
            
            # mode 1: sample n packets, skip n packets...
            elif mode == 2:
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
            elif mode == 3:
                dataset.at[i,feature] = dataset[feature][i][0:n]
                
                if superverbose:
                        print('\nSampled:')
                        print(len(dataset[feature][i]))
                        print(dataset[feature][i])
        
            # mode 3: sample n, skip n-1, sample n-2, skip n-3... packets of the flow
            elif mode == 4:
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
            input('\n...')
    
    if verbose and (not superverbose) and (not time):
        input('\n...')
    
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
        print('\n\n'+40*'~'+' FUNCTION: packetOutput '+40*'~')
        print('\npacket-list, length:\n{}'.format(len(plist)))
        print('\npacket-list, content:\n{}'.format(plist))
        print('\npacket-list, formatted:\n{}'.format(tmp))
        if not time: input('\n...')
    
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
    # index-position of chosen file
    findex = args.file[0]-1
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
    print('\n\n'+40*'~'+' SCRIPT: FlowSampling '+40*'~')
    print('\n'+20*'~'+' optional arguments '+20*'~')
    print("\n{}\t--verbose\n{}\t--superverbose\n{}\t--time\n{}\t--osx\n{}\t--windows".format(verbose,superverbose,time,osx,windows))
    print('\n{}, n = {}'.format(samplingmode[mode],n))
    
    print('\n'+20*'~'+' paths '+20*'~')
    print('\nPCAP: {}'.format(pcap))
    print('JSON: {}'.format(goflowsconf))
    print('CSV (flows): {}'.format(unlabeledcsv)) 
    print('CSV (sampled): {}'.format(sampledcsv))
    print('CSV (labeled): {}'.format(labeledcsv))
    
    print('\n'+20*'~'+' commands '+20*'~')
    print("\ngo-flows: {}".format(goflowscmd))
    print("labeling: {}".format(labelingcmd))
    if (not time): input('\n...') 

    
    # FLOW-CREATION & LABELING
    
    # execute go-flows to process passed PCAP file
    print("\n\n>>> create flow-CSV from PCAP with go-flows...")
    os.system(goflowscmd)
    
    # import output CSV from go-flows
    #poptions()
    dataset = importCSV(unlabeledcsv,None,verbose)
    
    if verbose:
        printdata(dataset,'go-flows CSV',verbose)
        if (not time): input('\n...') 
    
    
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
        
    for feature in features:
        print('\n\n>>> processing sampled packets: {}'.format(feature))
        for i in range(0,len(dataset.index)):
            dataset.at[i,feature] = sum(dataset[feature][i])/len(dataset[feature][i])
            
        if verbose:
            print('\n\n'+20*'~'+' Calculation, mean '+20*'~')
            print('\n{}'.format(dataset[feature]))
            if (not time): input('\n...') 
        
    if verbose:
        printdata(dataset,'sampled',verbose)
        if not time: input('\n...')
    
    # save dataframe as CSV for further preprocessing & classification
    print("\n>>> save data to CSV...")
    dataset.to_csv(sampledcsv, index=False)
    
    # label flow-based sampled CSV as last step of preparation for further classification
    print("\n>>> label flow-CSV...")
    os.system(labelingcmd)
    
    if time: 
        end = timer()
        print('\n[TOTAL TIME, FlowSampling.py]: %.3f' % (end-start),'seconds')
    
    if (not time): input('\n...')  
    exit()
    
    #sys.stdout.close()
    
    
    
    
    
    
    
     
    
    

    
    
   
    
   
    