# PacketSampling.py - Script to execute packet-based sampling modes on a traffic capture file in PCAP format

This script peforms packet-based sampling patterns onto a networ traffic capture file prior to collecting flows. Wireshark tools mergecap, editcap and capinfos are utilized to perform the sampling, afterwards go-flows collects flows to export the resulting data as CSV and utilizes a labeling script in preparation for preprocessing and classification.

```console
python3 PacketSampling.py -h
usage: PacketSampling.py [-h] [-v] [--superverbose] [-t] [-c] [-s s] split mode file n j

script for sampling PCAP files via editcaps (packetsampling), output is CSV

positional arguments:
  split           integer used to determine the split-size for PCAP files
  mode            choose samplign mode: {5: 'every n-th packet', 6: 'n out of N', 7: 'probability', 8: 'timebased'}
  file            select file to process: {0: 'Merged', 1: 'Monday-WorkingHours', 2: 'Tuesday-WorkingHours', 3: 'Wednesday-
                  WorkingHours', 4: 'Thursday-WorkingHours', 5: 'Friday-WorkingHours'}
  n               integer used to determine sampling steps
  j               choose feature-vector: {1: 'AGM_10s_flowbased.json', 2: 'AGM_60s.json', 3: 'AGM_3600s.json', 4:
                  'CAIA_flowSampling.json', 5: 'CAIA_packetSampling.json', 6: 'AGM_10s.json', 7: 'AGM_60s.json', 8:
                  'AGM_3600s.json'}

optional arguments:
  -h, --help      show this help message and exit
  -v, --verbose   output additional informations
  --superverbose  output additional informations, including loop iteration output
  -t, --time      measure function-runtimes
  -c, --check     check if number of sampled packets is correct
  -s s, --seed s  set seed for np random generator
```

## Usage Example

In order to apply packet-based sampling with the AGM feature-vector, in particular sample every n-th packet of the network traffic capture file (n=10) for Friday, passing a split-size of 5000 for the PCAP file, the following arguments are necessary to execute the script:
```console
python3 PacketSampling.py 5000 5 0 5 10 6
```
