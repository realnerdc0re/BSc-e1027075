# Sampling.py - Script to select proper sampling script based on passed arguments


```console
python3 Sampling.py -h
usage: Sampling.py [-h] [-v] [--superverbose] [-t | -e] (-f m | -p m) file n j

script to sample pcap files, saving labled csv into folders

positional arguments:
  file                  select file to process: {0: 'Merged', 1: 'Monday-WorkingHours', 2: 'Tuesday-WorkingHours', 3:
                        'Wednesday-WorkingHours', 4: 'Thursday-WorkingHours', 5: 'Friday-WorkingHours'}
  n                     non-zero integer, used to determine sampling-steps
  j                     select feature-vector: {1: 'AGM_10s_flowbased.json', 2: 'AGM_60s.json', 3: 'AGM_3600s.json', 4:
                        'CAIA_flowSampling.json', 5: 'CAIA_packetSampling.json', 6: 'AGM_10s.json', 7: 'AGM_60s.json', 8:
                        'AGM_3600s.json'}

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         output verbose information
  --superverbose        output additional verbose informations, including loop-iteration output
  -t, --time            measure runtimes
  -e, --export          export timestamps & resource logs
  -f m, --flowsampling m
                        select sampling-mode: {1: 'every n-th packet', 2: 'sample & skip n packets', 3: 'first n packets',
                        4: 'sample n, skip n-1, sample n-2 ...'}
  -p m, --packetsampling m
                        select sampling-mode: {5: 'every n-th packet', 6: 'n out of N', 7: 'probability', 8: 'timebased'}
```

## Usage Examples

