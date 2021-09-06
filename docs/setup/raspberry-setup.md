# Raspberry Pi Zero W

The Raspberry Pi Zero W used at the beginning of this thesis was used with DietPi, a lightweight Debian OS for single-board computers.

## Setup

### DietPi Installation

Steps taken to install and configure the Raspberry Pi Zero:

* Download [DietPi](https://dietpi.com/) version for Raspberry Pi
* Create flash-drive with [balenaEtcher](https://www.balena.io/etcher/)
* configure WiFi with diet-pi configurator
* proceed applying automatic updates after WiFi configuration
* no additional software selected for installation

### DietPi Configuration

After the installation process finished following configurations were applied. 

Set defaults:
```console
sudo nano /etc/defaults/keyboard
```
Configure timezone:
```console
sudo dpkg-reconfigure tzdata
```
### Packet Installation

Install the following Debian packets:
```console
sudo apt-get update
sudo apt-get install git dstat wajig
```
Install Python related packets:
```console
sudo apt-get install python3 python3-pip python3-numpy python3-matplotlib python3-scipy
```
The following installed packets can probably be skipped, they were installed nonetheless:
```console
sudo apt-get install build-essential python3-dev python3-setuptools python3-wheel
```
Necessary Python modules to install:
```console
python3 -m pip install scikit-learn pandas colorama
```

### SSH service

The default SSH service was replaced with OpenSSH to have an easier time pulling latest Git commits on the device, using scp and other SSH related services:
```console
sudo systemctl stop dropbear
sudo systemctl disable dropbear
sudo apt-get update
sudo apt-get install openssh-server
```
After OpenSSH is installed, generate keys and free diskspace:
```console
ssh-keygen -t rsa
sudo apt autoremove
```
### Tweaks
To significantly improve boot times:
```console
sudo nano /boot/dietpi.txt
```
Change the following lines:
```console
CONFIG_BOOT_WAIT_FOR_NETWORK=0
CONFIG_NTP_MODE=0
```
Speed up apt by disabling compression feature:
```console
sudo echo 'Acquire::GzipIndexes "false";' > /etc/apt/apt.conf.d/98dietpi-uncompressed
sudo /boot/dietpi/func/dietpi-set_software apt-cache clean
sudo apt update
```