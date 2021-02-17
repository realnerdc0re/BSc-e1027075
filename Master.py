#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 17 13:53:04 2021

@author: pjr
"""

import csv
import os
import sys
import pandas as pd
import time as epochtime

from pathlib import Path, PureWindowsPath, PurePath, PurePosixPath



# import experiment-configurations
import config as cfg

# MISSING: create all commands from configuration or file within iterations to work through experiments
# MISSING: mv original PCAP files into other folder, use editcap to just get small splitfile for testing purpuse speeeding up tests


if __name__ == '__main__':


	# informational output
	print('file: {}'.format(cfg.file))
	print('modes: {}'.format(cfg.mode))
	print('steps: {}'.format(cfg.steps))
	print('vectors: {}'.format(cfg.vector))
	input('blub')

	samplingcmd = 'python3 -u rpi-Sampling.py -e -f 1 5 5 4'
	modelcreationcmd = '' # doing rpi-Preprocessing on the local machine, saving the fitted RandomForest model

	# COMMANDS
	# creating base-directory
	mkdircmd = "ssh dietpi@10.10.45.55 'mkdir -p /mnt/data/CIC-IDS2017/PCAP/flow-sampledCSV/'"
	# forging command to sync sampled files and pre-processed model to VM/rpi (should be done via configuration file or lists defined in this script, containing sampling methods, steps...)
	synccmd = r'rsync -avz --progress /mnt/data/CIC-IDS2017/PCAP/flow-sampledCSV/Friday-WorkingHours_mode1_vector4_steps5_perflowsampled/ dietpi@10.10.45.55:/mnt/data/CIC-IDS2017/PCAP/flow-sampledCSV/Friday-WorkingHours_mode1_vector4_steps5_perflowsampled/'
	# cmd to execute Preprocessing & Classification on VM/rpi from local machine
	sshcmd = "ssh dietpi@10.10.45.55 'cd BSc-e1027075 && python3 -u rpi-Preprocessing.py -e -r -f 1 5 5 4 100000'"



	# EXECUTION (packed in loops, working through configuration lists given in config.py)

	#os.system(samplingcmd)
	#os.system(modelcreationcmd)
	os.system(mkdircmd)
	os.system(synccmd)
	os.system(sshcmd)
	#missing syncing results from VM/rpi back to local machine


	exit()