# FlowSampling.py - Script to execute flow-based sampling modes a traffic capture file in PCAP format

This script is able to collect flows from a passed capture file, saving the collected flows in form of a CSV file. Afterwards this CSV file is imported and, again depending on the passed arguments, the specified sampling mode is applied on packets within each flow. At the end of its execution the script utilizes a labeling script to label the resulting data in preparation for preprocessing and classification.


```console
python3 FlowSampling.py -h
usage: FlowSampling.py [-h] [-v] [--superverbose] [--debug] [-t] mode file n j

script for sampling PCAP files via go-flows (flow-based sampling), output is CSV

positional arguments:
  mode            select sampling mode: {1: 'every n-th packet', 2: 'sample & skip n packets', 3: 'first n packets', 4:
                  'sample n, skip n-1, sample n-2 ...'}
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
  --debug         output debugging informations, including flow-features containing NaNs
  -t, --time      measure runtimes

```

## Usage Examples

In order to apply flow-based sampling with the AGM feature-vector, in particular sample every n-th packet within each collected flow flow (n=10), the following arguments are necessary to execute the script:
```console
python3 FlowSampling.py 1 5 10 5 1

```