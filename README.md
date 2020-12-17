# BSc-e1027075

labeling:
https://github.com/CN-TU/Datasets-preprocessing/tree/master/CIC-IDS-2017/labeling

go-flows:
https://github.com/CN-TU/go-flows

wireshark:
```
aptitude update
aptitude install wireshark
```


filepaths need to be set correctly in following scripts:

Classification.py
FlowSampling.py
PacketSampling.py
Preprocessing.py

Use Control.py to run scripts.

python Control.py -h
usage: Control.py [-h] [-v] [--superverbose] [-t] (--linux | --osx | --windows) (--flowsampling m | --packetsampling m) file n j

Script to execute sampling, labeling, preprocessing and classification scripts on given capture file.

positional arguments:
  file                select file to process: {0:'All', 1: 'Monday-WorkingHours', 2: 'Tuesday-WorkingHours', 3: 'Wednesday-
                      WorkingHours', 4: 'Thursday-WorkingHours', 5: 'Friday-WorkingHours'}
  n                   non-zero integer, used to determine sampling-steps
  j                   select feature-vector: {1: 'AGM_10s.json', 2: 'AGM_60s.json', 3: 'AGM_3600s.json', 4:
                      'CAIA_flowSampling.json', 5: 'CAIA_packetSampling.json'}

optional arguments:
  -h, --help          show this help message and exit
  -v, --verbose       output verbose information
  --superverbose      output additional verbose informations, including loop-iterations output
  -t, --time          measure runtimes
  --linux             use Linux paths & commands
  --osx               use MacOS paths & commands
  --windows           use Windows paths & commands
  --flowsampling m    select sampling-mode: {1: 'every n-th packet', 2: 'sample & skip n packets', 3: 'sample first n
                      packets of a flow', 4: 'sample n, skip n-1, sample n-2 ...'}
  --packetsampling m  select sampling-mode: {1: 'every n-th packet'}
