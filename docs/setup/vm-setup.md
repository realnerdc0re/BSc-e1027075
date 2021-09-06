# Virtual Machine

In this study a virtual machine in form of an LXC container running on Proxmox VE is used to create predictions. The virtual machine imports an already fitted estimator model.

## Setup

In this setup *aptitude* is used as preferred APT front-end for Debian packets, for Python *python3* and its packet-management *pip* is utilized. Additional packets were installed necessary for script executions.

```console
sudo apt-get update && sudo apt-get install aptitude
sudo aptitude update && sudo aptitude dist-upgrade
sudo aptitude install net-tools git dstat rsync psmisc
sudo aptitude install python3 python3-pip
```

In order to connect properly to from the server to the virtual machien SSH keys have to be generated:
```console
ssh-keygen -t rsa -b 4096
```
The servers' public key has to be added in *~/.ssh/authorized_keys* on the virtual machine for key-based SSH authentification. It is also necessary to uncomment the following line in */etc/ssh/sshd_config* to enable key-based authentication:
```console
#AuthorizedKeysFile .ssh/authorized_keys .ssh/authorized_keys2
```
Pythons packet-management *pip* was further used to install required modules as user, in particlar the scikit-learn module was forced being installed in the same version as the server machine:
```console
python3 -m pip install scikit-learn==0.23.2
python3 -m pip install scikit-learn pandas psutil matplotlib colorama
```
Setting PYTHONPATH environment variable:
```console
vi ~/.bashrc
```
Add following line, replace *<user>* with the user that is actually used on the machine:
```console
export PYTHONPATH="$ {PYTHONPATH}:/home/<user>/.local/bin"
```



## Machine Information

Basic specifications of the virtual machine:
```console
OS: Debian GNU/Linux 10 (buster) x86_64
Kernel: 5.4.119-1-pve
CPU: Intel Atom D525 (1) @ 1.795GHz
Memory: 1024MiB
```