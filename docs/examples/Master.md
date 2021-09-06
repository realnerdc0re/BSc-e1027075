# Master.py - Script to automatically execute pre-defined experiment configurations

This script imports previously defined experiment configurations from the [configuration file](../../config.py) and automatically executes all necessary scripts on the server and the remote device to fit an estimator model and gather results on the remote device. After every successfully finished experiment configuration gathered results are synced from the remote device to the server for further evaluation.

```console
python3 Master.py -h
usage: Master.py [-h] [-v] [-f] [-m] [--nosync] [--nosampling] [-l | -r]

Script to automate experiments based on a given configuration via config.py. The Script does the sampling and model-creation on the local machine and syncs all necessary files from the local machine to a remote machine afterwards. Subsequently it creates predictions on the remote machine, saves the results and syncs back to the local machine.

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  output verbose information
  -f, --fit      fit model on remote machine
  -m, --model    load model on local machine
  --nosync       no syncing from local to remote
  --nosampling   use already sampled file if possible
  -l, --local    run scripts on local machine
  -r, --remote   run scripts on remote machine
```

## Usage Example

