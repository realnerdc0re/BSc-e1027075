#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 16 13:53:04 2020

@author: Patrick Resch
"""

import glob
import csv
import os
import sys



# choices for argument-parsing
# flowsampling-modes
flowsmode = {1:'every n-th packet',2:'sample & skip n packets',3:'sample first n packets of a flow',4:'sample n, skip n-1, sample n-2 ...'}
# packetsampling-modes
packetsmode = {1:'every n-th packet'}
# capture files, https://www.unb.ca/cic/datasets/ids-2017.html
filenames = {0:'All',1:'Monday-WorkingHours',2:'Tuesday-WorkingHours',3:'Wednesday-WorkingHours',4:'Thursday-WorkingHours',5:'Friday-WorkingHours'}
# feature vectors
featurevectors = {1:'AGM_10s.json', 2:'AGM_60s.json',3:'AGM_3600s.json',4:'CAIA_flowSampling.json',5:'CAIA_packetSampling.json'}

# directories
#rpi
#flowfolder = '/mnt/data/CIC-IDS2017/PCAP/flow-sampledCSV'
#packetfolder = '/mnt/data/CIC-IDS2017/PCAP/packet-sampledCSV'
flowfolder = '/home/dietpi/BSc-e1027075/rpi/flow-sampled'
packetfolder = '/home/dietpi/BSc-e1027075/rpi/packet-sampled'



# ARGUMENT PARSING
import argparse
parser = argparse.ArgumentParser(description='Script to merge multiple CSVs into a single file.')

# force sampling method & mode
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