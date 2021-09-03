# Packet Sampling for Lightweight Machine Learning-based Anomaly Detection

## Introduction

This repository contains a various selection of Python scripts that can be utilized to study the effect of different packet sampling techniques on machine learning-based anomaly detection in network traffic. This work uses the decision tree-based Random Forest classifier algorithm to create the estimator model and genearte predictions. The following figure depicts a superficial workflow diagram that describes roughly the different stages necessary to create results:

![Diagram](docs/images/SuperficialDiagram.svg?raw=true "Superficial Diagram")


## Usage

A description about the used environmental setup can be found within this repositorys' [docs](/docs) folder. For necessary configurations you may want to look into the [configuration file](config.py) that contains various parameters, filepaths and remote machine information to modify for personal usage. Once necessary information is configures an experiment execution chain can be started with executing the [Master.py](Master.py) script with or without passing optional arguments:

```console
python3 Master.py -h
usage: Master.py [-h] [-v] [-f] [-m] [--nosync] [--nosampling] [-l | -r]

Script to automate experiments based on a given configuration via config.py. The Script does the sampling and model-creation on the local machine and syncs all necessary files from the local machine to a remote machine afterwards. Subsequently it
creates predictions on the remote machine, saves the results and syncs back to the local machine.

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

Examplary commands for every script for various usecases can be found in the appropriate documentation folder [examples](/docs/examples).


## Issues

Beside ensuring that the classification device has enough memory available. One occuring issue encountered in this work is an incompability between models generated on x86 architectures not being able to be imported on the armv6l Raspberry Pi Zero W. This problem could not be solved, instead a virtual machine was utilized to generate the results for this study. Two different approaches to export/import the model on different architectures failed. The first method was generating the model on an x86 64bit machine running Ubuntu, resulting in the following error when importing the model on the Raspberry Pi Zero W:

```console
File "sklearn/tree/_tree.pyx", line 607, in sklearn.tree._tree.Tree.__cinit__
ValueError: Buffer dtype mismatch, expected 'SIZE_t' but got 'long long'
```