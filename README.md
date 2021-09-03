# Packet Sampling for Lightweight Machine Learning-based Anomaly Detection

## Introduction

This repository contains a various selection of Python scripts that can be utilized to study the effect of different packet sampling techniques on machine learning-based anomaly detection in network traffic. This work uses the decision tree-based Random Forest classifier algorithm to create the estimator model and genearte predictions. The following figure depicts a superficial workflow diagram that describes roughly the different stages necessary to create results:

![Diagram](docs/images/SuperficialDiagram.svg?raw=true "Superficial Diagram")


## Usage

A description about the used environmental setup can be found within this repositorys' [docs](/docs) folder. For necessary configurations you may want to look into the [configuration file](config.py) that contains various parameters, filepaths and remote machine information to modify for personal usage. Once necessary information is configures an experiment execution chain can be started with executing the [Master.py](Master.py) script with or without passing optional arguments:

```console
python3 Master.py
```



## Issues