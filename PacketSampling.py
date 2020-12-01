# -*- coding: utf-8 -*-
"""
Created on Fri Sep 11 09:25:55 2020

@author: Patrick
"""

from timeit import default_timer as timer

import numpy as np
import pandas as pd

import subprocess
import os
import sys


samplingmode = {1:'every n-th packet'}


# ARGUMENT PARSING
# command line argument passthrough for better usability
import argparse
parser = argparse.ArgumentParser(description='script for sampling PCAP files via editcaps (packetsampling), output is CSV')

parser.add_argument('--verbose', action='store_true', help='output additional informations')
parser.add_argument('--superverbose', action='store_true', help='output additional informations, including loop iteration output')
parser.add_argument('--time', action='store_true', help='measure function-runtimes')
parser.add_argument('--windows', action='store_true', help='use windows paths')
parser.add_argument('--osx', action='store_true', help='use MacOS paths')
parser.add_argument('--check', action='store_true', help='check if number of sampled packets is correct')

parser.add_argument('split', metavar='split', type=int,nargs=1,help='integer used to determine the split-size for PCAP files')
parser.add_argument('mode', metavar='mode', type=int, nargs=1, help='choose samplign mode (1: every n-th packet, 2: sample n & skip n, 3: sample n & skip 2n)')
parser.add_argument('file', metavar='file', type=int,nargs=1,help='choose integer 0 - 4 for PCAPs from Monday to Friday' )
parser.add_argument('n', metavar='n', type=int,nargs=1,help='integer used to determine sampling steps')

args = parser.parse_args()


# DEFINITIONS

# returns list of features that contains multiple packet-values based on feature-keyword
def perpacketFeatures(dataset,keyword,verbose=False,time=False):
    
    # get all features from given dataset
    features = dataset.columns
    tmp = []
    
    if verbose:
        print('\n'+40*'~'+' FUNCTION: perpacketFeatures, all features '+40*'~')
        print('\n',features)
    
    print('\n'+40*'~'+' FUNCTION: perpacketFeatures, comparison '+40*'~')
    for feature in features:
        print(feature)
        if feature[0:len(keyword)] == keyword:
            print('MATCH\n')
            tmp.append(feature)
        else:
            print('...discarded\n')
    
    if verbose:
        print('\n'+40*'~'+' FUNCTION: perpacketFeatures, summary '+40*'~')
        print('\nper-packet features:\n', tmp)
        if (not time): input('\n{VERBOSE} press ENTER to continue.')
            
    return tmp

# convert single string or single integer (given with go-flows accumulate function or after NaN cleaning) into list of integers
# necessary to get the values as list of integers for sampling and calculations
def convertToList(dataset,features,verbose=False,time=False):
    
    for feature in features:
        
        if verbose and not superverbose:
            print('\n\n'+40*'~'+' FUNCTION: convertToList: {} '.format(feature)+40*'~')
            print('processing...')  
        
        for i in range(0,len(dataset.index)):
            if superverbose:
                print('\n'+40*'~'+' FUNCTION: convertToList: {}, row: {}/{} '.format(feature,(i+1),len(dataset.index))+40*'~')
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
                input('\n{PAUSE} press ENTER to continue.')
            
            if superverbose:
                print('transformed:\n', dataset[feature][i])
                print('type:\n', type(dataset[feature][i]))
        
    
    if verbose and (not time): input('\n{VERBOSE} press ENTER to continue.')
            
    return

# sample first and every n-th package afterwards from given list of features
def flowSampling(dataset,n,features,mode=0,verbose=False,time=False):
    
    samplingmode = {0: 'every {}-th packet'.format(n), 1: 'sample & skip {} packets'.format(n), 2: 'sample first {} packets of a flow'.format(n), 3: 'sample n, skip n-1, sample n-2 ... (n={})'.format(n)}
    
    # temporary list for sampling
    tmp = [] 
    
    # iterate over list of given features
    for feature in features:
        
        if verbose and not superverbose:
            print('\n'+40*' '+' SAMPLING: {} '.format(samplingmode[mode]))  
            print(40*'~'+' FUNCTION: flowSampling: {} '.format(feature)+40*'~')
            print('...processing...')
        
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
            if mode == 0:
                dataset.at[i,feature] = dataset[feature][i][0::n]
                
                if superverbose:
                        print('\nSampled:')
                        print(len(dataset[feature][i]))
                        print(dataset[feature][i])
                        input('\n{SUPERVERBOSE} press ENTER to continue.')
            
            # mode 1: sample n packets, skip n packets...
            elif mode == 1:
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
            elif mode == 2:
                dataset.at[i,feature] = dataset[feature][i][0:n]
                
                if verbose:
                        print('\nSampled:')
                        print(len(dataset[feature][i]))
                        print(dataset[feature][i])
        
            # mode 3: sample n, skip n-1, sample n-2, skip n-3... packets of the flow
            elif mode == 3:
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
            input('\n{SUPERVERBOSE} press ENTER to continue.')
    
    if verbose and (not superverbose) and (not time):
        input('\n{VERBOSE} press ENTER to continue.')
    
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
        print('\n\n\n'+40*'~'+' FUNCTION: packetOutput '+40*'~')
        print('\npacket-list, length:\n{}'.format(len(plist)))
        print('\npacket-list, content:\n{}'.format(plist))
        print('\npacket-list, formatted:\n{}'.format(tmp))
        if (not time): input('\n{VERBOSE} press ENTER to continue.')
    
    return tmp


if __name__ == '__main__':
    
    global verbose 
    global time
    global check
    
    #sys.stdout = open("PacketSamplingOutput.txt","w")
    
    # optional arguments
    verbose = args.verbose
    superverbose = args.superverbose
    if superverbose:
        verbose = True
    time = args.time
    windows = args.windows
    osx = args.osx
    check = args.check
    
    # positional arguments
    split = args.split[0]
    findex = args.file[0]
    smode = args.mode[0]
    n = args.n[0]
    
    # get working directory
    wd = os.getcwd()
    
    if time: start = timer()
    
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
        # current PCAP
        pcap = "{}".format(fpath)+"\\"+fname[findex]
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
        csvpath = r"D:\CIC-IDS2017\PCAP\packet-sampledCSV"
        # name for splitted files
        splitname = ["Monday-WorkingHours_split.pcap","Tuesday-WorkingHours_split.pcap","Wednesday-WorkingHours_split.pcap","Thursday-WorkingHours_split.pcap","Friday-WorkingHours_split.pcap"]
        # name for splitted files
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
        goflowsconf = "{}".format(wd)+"\\go-flows-configurations\CAIA_packetSampling.json"
        # labeling.py script
        labelingpath = r"labeling.py"
            
    
    
    # forged command to gather packets, -M ... human readable packet count output, findstr is grep aequivalent
    capinfoscmd = "{}".format(capinfospath)+" -M -c "+"{}".format(fpath)+"\\"+fname[findex]+" | findstr packets"
    # forged command to label sampled CSV file
    labelingcmd = "python "+"{}".format(labelingpath)+" "+"{}".format(csvpath)+"\\"+labelingname[findex]+" 5tuple"
    # forged command to drop payload (keep first 127 bytes of all packets)
    editsnapcmd = "{}".format(editcappath)+" -s 127 "+"{}".format(fpath)+"\\"+fname[findex]+" "+"{}".format(snappath)+"\\"+fname[findex]
    # forged command to remove all files in the splitPCAP folder
    cleansplitPCAP = "del /q /s "+"{}".format(splitpath)+"\\*"+" > NUL"
    # forged command to split PCAP files into smaller files based on required argument split
    editsplitcmd = "{}".format(editcappath)+" -c "+str(split)+" "+"{}".format(snappath)+"\\"+snapname[findex]+" "+"{}".format(splitpath)+"\\"+splitname[findex]
    # forged command to merge sampled PCAP files into one file
    mergecapcmd = "{}".format(mergecappath)+" -F pcap "+"{}".format(splitpath)+"\\* -w "+"{}".format(samplepath)+"\\"+samplename[findex]
    # forged command to convert sampled PCAP into (per-packet) CSV for Classification
    goflowscmd = "{}".format(goflowspath)+" run features "+"{}".format(goflowsconf)+" export csv "+"{}".format(csvpath)+"\\"+"{}".format(csvname[findex])+" source libpcap "+"{}".format(samplepath)+"\\"+"{}".format(samplename[findex])
    
    
    # files
    snapfile = "{}".format(snappath)+"\\"+snapname[findex]
    
    
    # check passed optional arguments and commands
    if verbose:
        print('\n\n'+40*'~'+' SCRIPT: PacketSampling '+40*'~')
        print('\n'+20*'~'+' optional arguments '+20*'~')
        print("\n{}\t--verbose\n{}\t--superverbose\n{}\t--time\n{}\t--osx\n{}\t--windows\n{}\t--check".format(verbose,superverbose,time,osx,windows,check))
        print('\n{}, n = {}'.format(samplingmode[smode],n))
        
        print('\n'+20*'~'+' paths '+20*'~')
        print('\nPCAP: {}'.format(pcap))
        print('JSON: {}'.format(goflowsconf))
        
        print('\n'+20*'~'+' commands '+20*'~')
        print('\npacket-count: {}'.format(capinfoscmd))
        print('drop payload: {}'.format(editsnapcmd))
        print('clear folder: {}'.format(cleansplitPCAP))
        print('split PCAP: {}'.format(editsplitcmd))
        print('merge splits: {}'.format(mergecapcmd))
        print ('go-flows: {}'.format(goflowscmd))
        print('labeling: {}'.format(labelingcmd))
        if (not time): input('\n...')
    
    # optional argument --check: get total & sampled packet count of the original PCAP
    if check:
        totalpacketcount = subprocess.check_output(capinfoscmd, shell=True, universal_newlines=True)  
        for word in totalpacketcount.split():
            if word.isdigit():
                totalpacketcount = int(word)
                totalpackets = np.arange(1,totalpacketcount+1,1)
                totalsamplecount = len(totalpackets[0::n])
                print('\n\n'+20*'~'+' check packets, file: {} '.format(fname[findex])+20*'~')
                print("\ntotal packets: {} ".format(totalpacketcount))
                print("\nsampled packets: {} ".format(totalsamplecount))
                if (not time): input('\n...')
    
    
    # PREPARE PCAP FILES
    # drop payload
    print('\n\n>>> dropping payload from {}'.format(pcap))
    os.system(editsnapcmd)
    # clean splitPCAP folder
    print('>>> cleaning folder {}'.format(splitpath))
    os.system(cleansplitPCAP)
    # split PCAP into smaller files
    print('>>> splitting PCAP from {} into folder {}'.format(snapfile,splitpath))
    os.system(editsplitcmd)
    
    
    # SAMPLING (per-packet)
    
    # get filenames from all splits and total number of split-files for further processing
    splitlist = os.listdir(splitpath)
    splitcount = len(splitlist)
    
    # variables to determine necessary packet-skips on split-file transition
    packetskip = 0
    samplepstart = 0
    nextpacketskip = 0
    nextsamplepstart = 0
    
    # variable to keep track of split-file count thats currently processed
    scount = 0
    
    print("\n>>> apply sampling... (number of necessary iterations: {})".format(splitcount))
    
    # iterate all split-files and apply sampling
    for file in splitlist:
        
        scount += 1
        # informational output
        if verbose: print('\n\n'+40*'~'+' SCRIPT: PacketSampling, file: {} (processing), iteration: {}/{}'.format(file,scount,splitcount)+40*'~')
            
        # forge command for capinfos to gather pcount of the current split-file
        capinfosplitcmd = "{}".format(capinfospath)+" -M -c "+"{}".format(splitpath)+"\\"+file+" | findstr packets"
        pcount = subprocess.check_output(capinfosplitcmd, shell=True, universal_newlines=True)  
        for word in pcount.split():
            if word.isdigit():
                pcount = int(word)
        
        # get skips for current split-file
        packetskip = nextpacketskip
        # the number of packets relevant for sampling in current split-file, considering skips
        samplepcount = pcount - packetskip
        
        # create list of all packets and packet indexes of the current split-file
        # list of packet numbers
        plist = np.arange(1,pcount+1,1)
        # list of packet index-numbers
        plistindex = np.arange(0,pcount,1)
        
        # SAMPLING: mode 1, every n-th packet, including first packet of the pcap
        if smode == 1:
            
            # calculate number of packets to skip for the next split-file
            modulo = samplepcount % n
            if modulo != 0:
                # calculate skips for the next split-file
                nextpacketskip = n - modulo
                nextsamplepstart = nextpacketskip
            else:
                nextpacketskip = 0
                nextsamplepstart = 0
            
            if verbose:
                print('\n\n'+20*'~'+' skipped packets in split-file '+20*'~')
                print("\n{}\t...current split-file".format(packetskip))
                print("{}\t...next split-file".format(nextpacketskip))
        
            # sample index-numbers, considering packet-skips from previous split-file
            psample = plistindex[packetskip::n]
            # sample packet-numbers, considering packet-skips from previous split-file (used for verbose output)
            psamplenumber = plist[packetskip::n]
            # numbers of packets that are used to remove packets with editcaps
            pdrop = np.delete(plist,psample.tolist())
        
        if verbose:
            print('\n\n'+20*'~'+' sampling packets in split-file'+20*'~')
            pprint = packetOutput(plist,10,False)
            print('\npacket-count (ignoring skips): {}\n\n'.format(len(plist))+'\t[{} ... {}]'.format(str(pprint[0]),str(pprint[1])))
            pprint = packetOutput(psamplenumber,10,False)
            print('\nsampled packets (considering skips): {}\n\n'.format(len(psamplenumber))+'\t[{} ... {}]'.format(str(pprint[0]),str(pprint[1])))
            pprint = packetOutput(pdrop,10,False)
            print('\ndropped packets (considering skips): {}\n\n'.format(len(pdrop))+'\t[{} ... {}]'.format(str(pprint[0]),str(pprint[1])))
            if verbose and (not superverbose) and (not time): input('\n...')
    
        # flip list to drop packets from split-file, starting from the end and working towards the first packets of the split-file
        pdrop = np.flip(pdrop)
        
        # number of iterations until all packets are dropped with 512 packets per slice (limiting factor from editcaps)
        iteration = int(len(pdrop)/512)+1    
        # iterate through all packets to drop from current split-file    
        for i in range(0,iteration):
            # create a slice of 512 packets to remove with editcaps
            pslice = pdrop[0:512]
            # remove these 512 packets from droplist for the next iteration
            pdrop = pdrop[512:]
        
            if superverbose:
                print('\n\n'+20*'~'+' packet removal, iteration: {}/{} '.format(i+1,iteration)+20*'~')
                pprint = packetOutput(pslice,10,False)
                print('\nslice: {}\n\n'.format(len(pslice))+'\t[{} ... {}]'.format(str(pprint[0]),str(pprint[1])))
            
                # only display remaining packets until last iteration
                if i < (iteration-1):
                    pprint = packetOutput(pdrop,10,False)
                    print('\nremaining: {}\n\n'.format(len(pdrop))+'\t[{} ... {}]'.format(str(pprint[0]),str(pprint[1])))  
                # output for increased readability in superverbose mode
                elif i == (iteration-1):
                    print('\n'+40*'~'+' SCRIPT: PacketSampling, file: {} (done), iteration: {}/{}'.format(file,scount,splitcount)+40*'~')
                    input('\n...')
            
            # create string containing packet numbers seperated with whitespaces as argument for editcaps execution
            arg = [str(int) for int in pslice]
            arg = " ".join(arg)
    
            # forged command to drop packets with editcap
            editcapcmd = "{}".format(editcappath)+" "+"{}".format(splitpath)+"\\"+file+" "+"{}".format(splitpath)+"\\"+"tmp.pcap"+" "+arg
            os.system(editcapcmd)
            # forge command to replace old split-file with sampled tmp.pcap file
            movecmd = r"move /Y "+"{}".format(splitpath)+"\\"+"tmp.pcap"+" "+"{}".format(splitpath)+"\\"+file+" > NUL"
            os.system(movecmd)
        
    if time:
        sampletime = timer()
        print('\n[SAMPLE TIME]: %.3f' % (sampletime-start),'seconds')
    
    # merge split-files into single pcap for further processing
    print("\n>>> merge sampled split-files into single PCAP...")
    os.system(mergecapcmd)
    if time:
        mergetime = timer()
        print('\n[MERGE TIME]: %.3f' % (mergetime-sampletime),'seconds')
    
    # optional argument --check: get packet count of processed (merged) PCAP and compare with sampled packet count obtained from the original PCAP
    if check:
        capinfoscmd = "{}".format(capinfospath)+" -M -c "+"{}".format(samplepath)+"\\"+samplename[findex]+" | findstr packets"
        print("\nforged capinfos (sampled packet count):\n", capinfoscmd)
        
        samplepacketcount = subprocess.check_output(capinfoscmd, shell=True, universal_newlines=True)
        
        for word in samplepacketcount.split():
            if word.isdigit():
                samplepacketcount = int(word)
        
        print('\n\n'+20*'~'+' check packets, file: {} '.format(samplename[findex])+20*'~')
        print("\ntotal packets: {} ".format(samplepacketcount))
        
        if samplepacketcount == totalsamplecount:
            print("\n\n>> [SUCCESS] number of sampled packets correct!")
        else:
            print("\n\n>> [ERROR] number of sampled packets not matching calculated value!")
    
    # create (per-packet) CSV file from single pcap file
    print("\n>>> create CSV from single PCAP via goflows...")
    os.system(goflowscmd)
    if time:
        goflowstime = timer()
        print('\n[GO-FLOWS TIME]: %.3f' % (goflowstime-mergetime),'seconds')
        
    # label sampled flow CSV for further classification
    print("\n>>> label CSV file for classification...")
    os.system(labelingcmd)
    if time:
        labelingtime = timer()
        print('\n[LABEL TIME]: %.3f' % (labelingtime-goflowstime),'seconds')
    
    if time: 
        end = timer()
        print('\n[TOTAL TIME, PacketSampling.py]: %.3f' % (end-start),'seconds')
    
    
    if (not time):  input('\n[QUIT] press ENTER to quit.')   
    exit()
    #sys.stdout.close()
    
    
    
    
    
    
    
     
    
    

    
    
   
    
   
    