#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 17 13:53:04 2021

@author: pjr
"""

import os
import config as cfg
from colorama import Fore, Style
from timeit import default_timer as timer




# MISSING: mv original PCAP files into other folder, use editcap to just get small splitfile for testing purpuse speeeding up tests


# ARGUMENT PARSING
import argparse
parser = argparse.ArgumentParser(description='Script to automate experiments based on a given configuration via config.py. The Script does the sampling and model-creation on the local machine and syncs all necessary files from the local machine to a remote machine afterwards. Subsequently it creates predictions on the remote machine, saves the results and syncs back to the local machine.')
parser.add_argument('-v','--verbose', action='store_true', help='output verbose information')
parser.add_argument('-l','--local', action='store_true',help='just do sampling and classification on local machine')
args = parser.parse_args()


if __name__ == '__main__':

    start = timer()

    verbose = args.verbose

    # check passed optional arguments and commands
    print('\n'+40*'~'+' SCRIPT: Master.py '+40*'~')
    if verbose:
        print('\nfiles:\n\t{}\n\nsampling-modes:\n\t{}\n\nfeature-vectors:\n\t{}\n'.format(cfg.filenames,cfg.modes,cfg.vectors))
        print(20*'~'+' configuration '+20*'~')
        print('\n\tfile:\t{}\n\tvector:\t{}\n\tmode:\t{}\n\tstep:\t{}\n\n'.format(cfg.file,cfg.vector,cfg.mode,cfg.steps))
        input('...')

    # check online-status of remote machine
    ping = os.system('ping -c 1 {} >/dev/null 2>&1'.format(cfg.remoteip)) # ping remote machine
    if ping == 0: print('>>> Status {}: '.format(cfg.remoteip)+Fore.GREEN+'ONLINE'+Style.RESET_ALL)
    else: print('>>> Status {}: '.format(cfg.remoteip)+Fore.RED+'OFFLINE'+Style.RESET_ALL), exit()

    # iterate over configurations
    for file in cfg.file:
        for vector in cfg.vector: # iterate over given feature-vectors

            # folder selection based on given feature-vector
            if vector < cfg.vectorlimit:
                basefolder = cfg.flowfolder
                sarg = '-f'
                foldername = '{}_mode{}_vector{}_steps{}_perflowsampled'
            else:
                basefolder = cfg.packetfolder
                sarg = '-p'
                foldername = '{}_mode{}_vector{}_steps{}_packetsampled'
            mkdircmd = "ssh {} 'mkdir -p {}'".format(cfg.remote,basefolder)

            for mode in cfg.mode: # iterate over given sampling-modes

                # check plausibility of given configuration, continue on pointless combinations
                if vector < cfg.vectorlimit and mode >= cfg.samplinglimit: continue # perflow feature-vectors and packetsampling-modes
                elif vector >= cfg.vectorlimit and mode < cfg.samplinglimit: continue #packetsampling feature-vectors and perflowsampling-modes

                for steps in cfg.steps: # iterate over given sampling-steps

                    # forge folders & commands based on configuration
                    currentfolder = foldername.format(cfg.filenames[file],mode,vector,steps)
                    samplingcmd = 'python3 rpi-Sampling.py -e {} {} {} {} {}'.format(sarg,mode,file,steps,vector)
                    modelcmd = 'python3 rpi-Preprocessing.py -e -s {} {} {} {} {} {}'.format(sarg,mode,file,steps,vector,cfg.batchsize)
                    synccmd = r'rsync -avz --progress {}/{}/ {}:{}/{}/'.format(basefolder,currentfolder,cfg.remote,basefolder,currentfolder)
                    sshcmd = "ssh {} 'cd {} && python3 -u rpi-Preprocessing.py -e -r -m {} {} {} {} {} {}'".format(cfg.remote,cfg.remotewd,sarg,mode,file,steps,vector,cfg.batchsize) # importing model on remote
                    #sshcmd = "ssh {} 'cd {} && python3 -u rpi-Preprocessing.py -e -r -s {} {} {} {} {} {}'".format(cfg.remote,cfg.remotewd,sarg,mode,file,steps,vector,cfg.batchsize) # saving model on remote
                    resynccmd = r'rsync -avz --progress {}:{}/{}/ {}/{}/'.format(cfg.remote,basefolder,currentfolder,basefolder,currentfolder)

                    # subsequential script & command exections
                    print('>>> Sample PCAP on local machine: {}'.format(samplingcmd))
                    os.system(samplingcmd)

                    print('>>> Create and save model on local machine: {}'.format(modelcmd))
                    os.system(modelcmd)

                    print('>>> Create base-folder on remote machine: {}'.format(mkdircmd))
                    os.system(mkdircmd)

                    print('>>> Sync content from local to remote machine: {}'.format(synccmd))
                    os.system(synccmd)
                    #input('...')

                    print('>>> Execute pre-processing and classification on remote machine: {}'.format(sshcmd))
                    os.system(sshcmd)
                    #input('...')

                    print('>>> Sync results back to local machine: {}'.format(resynccmd))
                    os.system(resynccmd)
                    #input('...')

    end = timer()
    print('\n(runtime : %.3f' % (end-start),'seconds)\n')

    exit()