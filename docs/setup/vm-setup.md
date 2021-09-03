# Virtual Machine

In this study a virtual machine in form of an LXC container running on Proxmox VE is used to create predictions. The virtual machine imports an already fitted estimator model.

## Setup

In this setup *aptitude* is used as preferred APT front-end for Debian packets, for Python *python3* and its packet-management *pip* is utilized.
```console
sudo apt-get update && sudo apt-get install aptitude
sudo aptitude update && sudo aptitude dist-upgrade
sudo aptitdue install python3 python3-pip
```

Pythons packet-management *pip* was further used to install required modules as user:
```console
python3 -m pip install scikit-learn pandas psutil matplotlib
```



## Machine Information

Basic specification of the virtual machine:
```console
OS: Debian GNU/Linux 10 (buster) x86_64Host: MS-7C02 1.0
Kernel: 5.4.119-1-pve
CPU: Intel Atom D525 (1) @ 1.795GHz
Memory: 1024MiB
```
