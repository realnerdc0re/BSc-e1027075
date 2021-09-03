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
from os import path


# ARGUMENT PARSING
import argparse
parser = argparse.ArgumentParser(description='Script to automate experiments based on a given configuration via config.py. The Script does the sampling and model-creation on the local machine and syncs all necessary files from the local machine to a remote machine afterwards. Subsequently it creates predictions on the remote machine, saves the results and syncs back to the local machine.')
parser.add_argument('-v','--verbose', action='store_true', help='output verbose information')
parser.add_argument('-f','--fit', action='store_true', help='fit model on remote machine')
parser.add_argument('-m','--model', action='store_true', help='load model on local machine')
parser.add_argument('--nosync',action='store_true',  help= 'no syncing from local to remote')
parser.add_argument('--nosampling',action='store_true',help='use already sampled file if possible')
# force either just local or remote execution if selected at all
execution = parser.add_mutually_exclusive_group(required=False)
execution.add_argument('-l','--local', action='store_true', help='run scripts on local machine')
execution.add_argument('-r','--remote', action='store_true', help='run scripts on remote machine')
args = parser.parse_args()

# executes passed commands, on error the script exits
def callCommand(function):
    if (os.system(function)) != 0:
        print(Fore.RED+'\n<<< ERROR for os.system({})\n'.format(function)+Style.RESET_ALL)
        exit()
    return


if __name__ == '__main__':

    start = timer()

    verbose = args.verbose
    remote  = args.remote
    nosync  = args.nosync
    local   = args.local
    fit     = args.fit
    models  = args.model
    nosamp  = args.nosampling
    samp = True
    varg = ''

    print('\n'+40*'~'+' SCRIPT: Master.py '+40*'~')
    # check passed optional arguments and commands
    if verbose:
        varg = '-v' # set argument to call other framework scripts
        print(cfg.vcolor+'\n'+20*'~'+' configuration & arguments '+20*'~')
        print('files:\n\t{}\n\nsampling-modes:\n\t{}{}\n\nfeature-vectors:\n\t{}\n'.format(cfg.filenames,cfg.fsamplingmode,cfg.psamplingmode,cfg.vectors))
        print('\tfile:\t{}\n\tvector:\t{}\n\tmode:\t{}\n\tstep:\t{}'.format(cfg.file,cfg.vector,cfg.mode,cfg.steps))
        print('\n\tverb:\t{}\n\tfit:\t{}\n\tmodel:\t{}\n\tnosync:\t{}\n\tlocal:\t{}\n\tremote:\t{}'.format(verbose,fit,models,nosync,local,remote))
        print(67*'~'+Style.RESET_ALL)

    # check online-status of remote machine
    if not local:
        ping = os.system('ping -c 1 {} >/dev/null 2>&1'.format(cfg.remoteip)) # ping remote machine

        if ping == 0:   print('>>> Status {}: '.format(cfg.remoteip)+Fore.YELLOW+'ONLINE'+Style.RESET_ALL)
        else:           print('>>> Status {}: '.format(cfg.remoteip)+Fore.RED+'OFFLINE'+Style.RESET_ALL); exit()

    # iterate over configurations
    for file in cfg.file:
        for vector in cfg.vector:
            # folder selection based on given feature-vector
            if vector < cfg.vectorlimit:
                basefolder  = cfg.flowfolder
                sarg        = '-f'
                samplingtype = 'flowbased'
            else:
                basefolder  = cfg.packetfolder
                sarg        = '-p'
                samplingtype = 'packetbased'

            mkdir = "ssh {} 'mkdir -p {}'".format(cfg.remote,basefolder)

            for mode in cfg.mode: # iterate over given sampling-modes

                # plausibility check of given configuration, continue on pointless combinations
                # flow-based feature-vectors and packet-based sampling-modes
                if vector < cfg.vectorlimit and mode >= cfg.samplinglimit: continue
                # packet-based feature-vectors and flow-based sampling-modes
                elif vector >= cfg.vectorlimit and mode < cfg.samplinglimit: continue

                for steps in cfg.steps: # iterate over given sampling-steps
                    # forge folders & sampling command based on configuration
                    folder    = cfg.foldername.format(cfg.filenames[file],mode,vector,steps,samplingtype)
                    sampling = 'python3 Sampling.py -e {} {} {} {} {} {}'.format(varg,sarg,mode,file,steps,vector)

                    if models:
                        model = 'python3 Preprocessing.py -e -m --local {} {} {} {} {} {} {}'.format(varg,sarg,mode,file,steps,vector,cfg.batchsize)
                    else:
                        model = 'python3 Preprocessing.py -e -s --local {} {} {} {} {} {} {}'.format(varg,sarg,mode,file,steps,vector,cfg.batchsize)

                    if fit: ssh = "ssh {} 'cd {} && python3 -u Preprocessing.py -e -r -s {} {} {} {} {} {}'".format(cfg.remote,cfg.remotewd,sarg,mode,file,steps,vector,cfg.batchsize) # fit and save model on remote
                    else:   ssh = "ssh {} 'cd {} && python3 -u Preprocessing.py -e -r -m {} {} {} {} {} {}'".format(cfg.remote,cfg.remotewd,sarg,mode,file,steps,vector,cfg.batchsize) # importing model on remote

                    sync   = r'rsync -avz --progress {}/{}/ {}:{}/{}/'.format(basefolder,folder,cfg.remote,basefolder,folder) # sync to remote
                    csync  = r'rsync -avz --progress {}/{} {}:{}'.format(cfg.wd,cfg.configuration,cfg.remote,cfg.remoteconf)  # sync configuration
                    resync = r'rsync -avz --progress {}:{}/{}/ {}/{}/'.format(cfg.remote,basefolder,folder,basefolder,folder) # sync to local

                    if (not remote): # LOCAL
                        if nosamp:
                            currentfile = cfg.filenames[file]+'.csv'
                            print(Fore.YELLOW+'\n>>> Search experiment folder: {}'.format(basefolder/folder)+Style.RESET_ALL)
                            if path.exists(basefolder/folder/currentfile):
                                print(Fore.YELLOW+'>>> Found already sampled capture: {}'.format(currentfile)+Style.RESET_ALL)
                                samp = False
                            else:
                                print(Fore.YELLOW+'>>> No sampled capture file found!'+Style.RESET_ALL)
                                samp = True

                        if samp:
                            print(Fore.YELLOW+'\n>>> Sample PCAP on local machine: {}'.format(sampling)+Style.RESET_ALL)
                            callCommand(sampling)

                        print(Fore.YELLOW+'\n>>> Create and save model on local machine: {}'.format(model)+Style.RESET_ALL)
                        callCommand(model)

                        if local: # skip processing on remote machine
                            end = timer()
                            print('\n(runtime : %.3f' % (end-start),'seconds)\n')
                            continue

                    if (not local): # REMOTE
                        print(Fore.YELLOW+'\n>>> Create base-folder on remote machine: {}'.format(mkdir)+Style.RESET_ALL)
                        callCommand(mkdir)

                        print(Fore.YELLOW+'\n>>> Sync experiment configuration from local to remote machine: {}'.format(csync)+Style.RESET_ALL)
                        callCommand(csync)

                        if (not nosync):
                            print(Fore.YELLOW+'\n>>> Sync content from local to remote machine: {}'.format(sync)+Style.RESET_ALL)
                            callCommand(sync)

                        print(Fore.YELLOW+'\n>>> Execute pre-processing and classification on remote machine: {}'.format(ssh)+Style.RESET_ALL)
                        callCommand(ssh)

                        print(Fore.YELLOW+'\n>>> Sync results back to local machine: {}'.format(resync)+Style.RESET_ALL)
                        callCommand(resync)

    end = timer()
    print(20*'#')
    print('\n(runtime : %.3f' % (end-start),'seconds)\n')
    print(Fore.GREEN+'\n\n<<< EXPERIMENTS SUCCESSFULLY COMPLETED!\n'+Style.RESET_ALL)

    exit()