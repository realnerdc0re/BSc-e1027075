#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 16 13:53:04 2020

@author: pjr
"""

import glob
import csv
import os
import sys
import pandas as pd


# directories
#rpi
flowfolder = '/home/dietpi/BSc-e1027075/rpi/flow-sampled'
packetfolder = '/home/dietpi/BSc-e1027075/rpi/packet-sampled'


# ARGUMENT PARSING
import argparse
parser = argparse.ArgumentParser(description='Script to merge multiple CSVs into a single file.')
# force choice for folder-selection
samplegroup = parser.add_mutually_exclusive_group(required=True)
samplegroup.add_argument('--flowsampling', action='store_true', help='merge flow-sampled CSVs')
samplegroup.add_argument('--packetsampling',action='store_true', help='merge packet-sampled CSVs')
args = parser.parse_args()


if __name__ == '__main__':

	# check arguments
	flowsampling = args.flowsampling
	packetsampling = args.packetsampling
	# set folder-path for merge
	if flowsampling:
		os.chdir(flowfolder)
		mergefolder = flowfolder
	elif packetsampling:
		os.chdir(packetfolder)
		mergefolder = packetfolder

	extension = 'csv'
	print('\n\n>>> merging sampled data into CSV...')
	# save all files matching *Hours.csv into list, these are the already labeled CSV files
	matchedfiles = [i for i in glob.glob('*Hours.{}'.format(extension))]
	# concat all labeled csv-files into single csv
	singlecsv = pd.concat([pd.read_csv(f) for f in matchedfiles])
	singlecsv.to_csv(str(mergefolder)+"/Merged.csv", index = False,encoding='utf-8-sig')

	exit()