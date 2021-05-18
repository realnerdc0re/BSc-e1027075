import time as epochtime
import numpy as np
import pandas as pd
import sys
import csv
import os

from pandas import read_csv
from pandas.plotting import scatter_matrix
from matplotlib import pyplot
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
    files = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Merged']
    filename = '{}_flows.csv'

    # COMMAND TO CREATE FLOWS
    #~/Git/go-flows/./go-flows run features ~/Git/BSc-e1027075/go-flows-configurations/CAIA_packetSampling.json export csv Merged_flows_unlabeled.csv source libpcap Merged.pcap

    # COMMAND TO LABEL FLOWS
    #python3 /mnt/data/BSc-e1027075/Labeling.py /mnt/data/CIC-IDS2017/PCAP/Original\ PCAPs/Merged_flows 5tuple

    for file in files:
        currentfile = filename.format(file)
        filepath = path / currentfile
        dataset = importCSV(filepath,None,False,None) # import current file
        print('\n',dataset.groupby('Label').size()) # outputs distribution of attack and benign labeled flows
        input('...')

    exit()
