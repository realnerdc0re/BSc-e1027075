#!/usr/bin/env python


flowsmode = {1:'every n-th packet',2:'sample & skip n packets',3:'sample first n packets of a flow',4:'sample n, skip n-1, sample n-2 ...'}
packetsmode = {1:'every n-th packet',2:'time-based'}
filenames = {0:'Merged',1:'Monday-WorkingHours',2:'Tuesday-WorkingHours',3:'Wednesday-WorkingHours',4:'Thursday-WorkingHours',5:'Friday-WorkingHours'}
featurevectors = {1:'AGM_10s.json', 2:'AGM_60s.json',3:'AGM_3600s.json',4:'CAIA_flowSampling.json',5:'CAIA_packetSampling.json'}


# experiment configurations
file = [5] # Friday-WorkingHours
vector = [4] # CAIA_flowSampling.json
mode = [1,3] # every n-th packet, first n packets
steps = [3,5,7] # n
