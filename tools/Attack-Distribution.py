import time as epochtime
import numpy as np
import pandas as pd
import sys
import csv
import os

from pandas import read_csv
from pandas.plotting import scatter_matrix
import matplotlib.pyplot as plt
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
from pathlib import Path, PureWindowsPath, PurePath, PurePosixPath

mntd = PurePosixPath('/mnt')

# ARGUMENT PARSING
# command line argument passthrough for better usability
import argparse
parser = argparse.ArgumentParser(description='Simple script to analyzed flows already collected from PCAPs. Commands for go-flows and labeling are commented within the source code. Outputs all occuring attack types and their respective counts for each workday or the merged file. Can be used to generate histogram for attack distribution.')
args = parser.parse_args()


# import CSV
def importCSV(csvpath,csvusecols=None,verbose=False,chunksize=None,encoding='utf-8'):  


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

    return csvdata
# outputs additional informations only shown in verbose mode
def verboseprint(dataset):
    print('\n{}\n'.format(dataset.columns))
    print('\n{}'.format(dataset.info()))
    return
# outputs basic datset informations
def printdata(dataset,heading,verbose=False):
    print('\n\n'+40*'~'+' FUNCTION: printdata, {} '.format(heading)+40*'~')
    print('\n{}\n'.format(dataset))
    #print('\n{}\n'.format(dataset.describe()))
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


if __name__ == '__main__':

    verbose = True
    path = mntd / 'data' / 'CIC-IDS2017' / 'PCAP' / 'Original PCAPs'
    #files = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    files = ['Monday-WorkingHours','Tuesday-WorkingHours','Wednesday-WorkingHours','Thursday-WorkingHours','Friday-WorkingHours']
    filename = '{}_flows.csv'

    # COMMAND TO CREATE FLOWS
    #~/Git/go-flows/./go-flows run features ~/Git/BSc-e1027075/go-flows-configurations/CAIA_packetSampling.json export csv Merged_flows_unlabeled.csv source libpcap Merged.pcap
    #~/Git/go-flows/./go-flows run features ~/Git/BSc-e1027075/go-flows-configurations/AGM_10s.json export csv Merged_flows_unlabeled.csv source libpcap Merged.pcap
    # COMMAND TO LABEL FLOWS
    #python3 /mnt/data/BSc-e1027075/Labeling.py /mnt/data/CIC-IDS2017/PCAP/Original\ PCAPs/Merged_flows 5tuple
    #python3 /mnt/data/BSc-e1027075/Labeling.py /mnt/data/CIC-IDS2017/PCAP/Original\ PCAPs/Merged_flows 5tuplebi
    #python3 /mnt/data/BSc-e1027075/Labeling.py /mnt/data/CIC-IDS2017/PCAP/Original\ PCAPs/Merged_flows AGM


    for file in files:
        currentfile = filename.format(file)
        filepath = path / currentfile
        dataset = importCSV(filepath,None,False,None) # import current file
        print('\n',dataset.groupby('Label').size()) # outputs distribution of attack types and benign labeled flows

        ad = dataset.groupby('Attack').size() # attack types distribution
        print('\n{}\n{}'.format(ad, type(ad)))
        input('...')

        #pd.set_option('display.max_rows', None)
        #sd = dataset.groupby('sourceIPAddress').size() # source IP distribution
        #dd = dataset.groupby('destinationIPAddress').size() # destinatin IP distribution
        #print('\n{}\n{}'.format(sd, type(sd)))
        #print('\n{}\n{}'.format(dd, type(dd)))

        if False: # following code block could be placed within the for-loop to generate histogram (at the end not used in the thesis, instead created a table)
            attacks = []
            numbers = []

            n = len(ad)

            for i in range(0,n):
                attacks.append(ad.index[i])
                numbers.append(ad[i])

            attacks.pop(10)
            numbers.pop(10)

            attacks[9] = 'Infiltration:Dropbox download' # rename to increase readability (bad one because with AGM there is actually exactly that name used for other attack type)

            tickx = [0,0.25,0.5,0.75,1,1.25,1.5,1.75,2,2.25,2.5,2.75,3,3.25]


            print('{}\n{}'.format(attacks,numbers))

            #fig = plt.figure(figsize=(21.0,9.0),frameon=True)
            fig,ax = plt.subplots(figsize=(21.0,9.0))
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_visible(False)
            ax.spines["top"].set_visible(False)

            #plt.title('CAIA',ha='center',fontsize=16) # set title
            plt.bar(tickx,numbers,color='#6E6E74',width=0.125,edgecolor='#4F4F5A',linewidth=2,tick_label=attacks)
            plt.xticks(rotation=80,size=14)
            plt.yticks([]) # dont plot any numbers on the y-axiy
            #plt.tick_params(top=False,bottom=False)

            #plt.xlabel('Attacks')
            #plt.ylabel('Numbers')
            move = [-0.035,-0.035,-0.05,-0.065,-0.05,-0.075,-0.05,-0.05,-0.015,-0.065,-0.08,-0.035,-0.03,-0.035] # manually adjust positioning CAIA
            for i,v in enumerate(numbers):
                xvalue = tickx[i] + move[i]
                plt.text(x=xvalue,y=v+2500,s=v,size=14)

            plt.subplots_adjust(bottom=0.35) # create space for attack labels
            #plt.axis('off')

            plt.savefig('/home/noooberino/Git/BSc-e1027075-Thesis/graphics/figures/CAIAdistribution.pdf',bbox_inches='tight',pad_inches=0) # save plot to file
            #plt.imsave('/home/noooberino/Git/BSc-e1027075-Thesis/graphics/figures/CAIAdistribution.pdf')
            plt.show()

            #ad.plot.bar()
            #pyplot.hist(attackdistribution.)

    exit()