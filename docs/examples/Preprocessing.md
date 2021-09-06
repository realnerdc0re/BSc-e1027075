# Preprocessing.py - Script to perform necessary data pre-processing and classification for the implemented estimator algorithm

The script imports an already sampled network traffic capture in form of a CSV file. After the import is done, necessary pre-processing steps are taken like replacing NaN feature-values, fitting the scaler, applying Principal Component Analysis (PCA) and, depeneding on the passed argument, fitting or importing an estimator model to finally create predictions for the test portion of the data.

```console
python3 Preprocessing.py -h
usage: Preprocessing.py [-h] [-v] [--superverbose] [-m] [-s] [-l] [-r] [-t | -e] (-f m | -p m) file n j batch

script for preprocessing labeled CSVs

positional arguments:
  file                  select file to process: {0: 'Merged', 1: 'Monday-WorkingHours', 2: 'Tuesday-WorkingHours', 3:
                        'Wednesday-WorkingHours', 4: 'Thursday-WorkingHours', 5: 'Friday-WorkingHours'}
  n                     non-zero integer, used to determine sampling-steps
  j                     select feature-vector: {1: 'AGM_10s_flowbased.json', 2: 'AGM_60s.json', 3: 'AGM_3600s.json', 4:
                        'CAIA_flowSampling.json', 5: 'CAIA_packetSampling.json', 6: 'AGM_10s.json', 7: 'AGM_60s.json', 8:
                        'AGM_3600s.json'}
  batch                 choose numerical value for StandardScaler batchsize

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         output additional informations
  --superverbose        output additional dataset related informations
  -m, --model           import model
  -s, --save            save model
  -l, --local           used to determine PCA component number on local machine
  -r, --remote          execution on remote machine, different method to kill dstat, changing foldername for results
  -t, --time            display script runtime
  -e, --export          export timestamps & resource logs
  -f m, --flowsampling m
                        select sampling-mode: {1: 'every n-th packet', 2: 'sample & skip n packets', 3: 'first n packets',
                        4: 'sample n, skip n-1, sample n-2 ...'}
  -p m, --packetsampling m
                        select sampling-mode: {5: 'every n-th packet', 6: 'n out of N', 7: 'probability', 8: 'timebased'}
```

## Usage Example

Exemplary command to perform classification (importing the estimator model) for a specific experiment configuration:
```console
python3 Preprocessing.py -m -f 1 0 10 1
```
In this case the arguments passed to specificy the sampling-related attributes is necessary to select the correct folder containing the already sampled data and the estimator model to import.