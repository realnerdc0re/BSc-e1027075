# Linux Machine

In this study a machine running Ubuntu has been used apply sampling and collect flows for further processing. All estimator models have been fitted on this machine.

## Setup

### OS

In this setup *aptitude* is used as preferred APT front-end for Debian packets, for Python *python3* and its packet-management *pip* is utilized.
```console
sudo apt-get update && sudo apt-get install aptitude
sudo aptitude update && sudo aptitude dist-upgrade
sudo aptitude install python3 python3-pip
```
### Python

Pythons packet-management *pip* was further used to install required modules as user:
```console
python3 -m pip install scikit-learn pandas psutil matplotlib colorama
```
### Tools

#### Labeling Script

The script used to label sampled network traffic of the CIC-IDS-2017 dataset can be downloaded at:
https://github.com/CN-TU/Datasets-preprocessing/tree/master/CIC-IDS-2017/labeling

#### go-flows

The flow exporter used in this study to collect network flows based on a passed JSON configuration for flow-key and feature specifications can be found here:
https://github.com/CN-TU/Datasets-preprocessing/tree/master/CIC-IDS-2017/labeling

#### Wireshark

Wireshark and all included tools like editcap or mergecap can be installed directly from the command line:
```console
sudo aptitude update
sudo aptitude install wireshark
```


## Machine Information

Basic specification of the server:
```console
OS: Ubuntu 20.10 x86_64
Host: MS-7C02 1.0
Kernel: 5.8.0-59-generic
CPU: AMD Ryzen 5 3600 (12) @ 3.600GHz
Memory: 16019MiB
```

## Installed

### Python Packets

All Python related packets installed on the server machine:
```console
dpkg -l|grep python|awk '{print $2,$3}'
libpython2.7-minimal:amd64 2.7.18-1build2
libpython3-dev:amd64 3.8.6-0ubuntu1
libpython3-stdlib:amd64 3.8.6-0ubuntu1
libpython3.8:amd64 3.8.10-0ubuntu1~20.10.1
libpython3.8-dev:amd64 3.8.10-0ubuntu1~20.10.1
libpython3.8-minimal:amd64 3.8.10-0ubuntu1~20.10.1
libpython3.8-stdlib:amd64 3.8.10-0ubuntu1~20.10.1
python-apt-common 2.1.3ubuntu1.4
python-matplotlib-data 3.3.0-3
python-pip-whl 20.1.1-2
python2.7-minimal 2.7.18-1build2
python3 3.8.6-0ubuntu1
python3-apport 2.20.11-0ubuntu50.7
python3-apt 2.1.3ubuntu1.4
python3-aptdaemon 1.1.1+bzr982-0ubuntu34.1
python3-aptdaemon.gtk3widgets 1.1.1+bzr982-0ubuntu34.1
python3-bcrypt 3.1.7-3
python3-blinker 1.4+dfsg1-0.3ubuntu2
python3-bottle 0.12.15-2.1
python3-brlapi:amd64 6.0+dfsg-4ubuntu7
python3-bs4 4.9.1-1
python3-cairo:amd64 1.16.2-4
python3-certifi 2020.4.5.1-1
python3-cffi-backend 1.14.2-1
python3-chardet 3.0.4-7
python3-click 7.1.2-1
python3-colorama 0.4.3-1build1
python3-commandnotfound 20.10.1
python3-compizconfig:amd64 1:0.9.14.1+20.10.20200813-0ubuntu1
python3-cryptography 3.0-1ubuntu0.1
python3-cups:amd64 2.0.1-3
python3-cupshelpers 1.5.12-0ubuntu3.1
python3-cycler 0.10.0-3
python3-dateutil 2.8.1-4
python3-dbus 1.2.16-3
python3-debconf 1.5.74
python3-debian 0.1.37
python3-defer 1.0.6-2.1
python3-dev 3.8.6-0ubuntu1
python3-distro 1.5.0-1
python3-distro-info 0.23ubuntu1
python3-distupgrade 1:20.10.16
python3-distutils 3.8.10-0ubuntu1~20.10
python3-docker 4.1.0-1.2
python3-docopt 0.6.2-2.2ubuntu1
python3-evdev 1.3.0+dfsg-1build1
python3-fasteners 0.14.1-2
python3-flask 1.1.2-1
python3-future 0.18.2-4
python3-gdbm:amd64 3.8.10-0ubuntu1~20.10
python3-gi 3.38.0-1
python3-gi-cairo 3.38.0-1
python3-html5lib 1.1-1
python3-httplib2 0.18.1-1
python3-ibus-1.0 1.5.23-0ubuntu1
python3-idna 2.10-1
python3-influxdb 5.2.3-1
python3-itsdangerous 1.1.0-2
python3-jeepney 0.4.3-1
python3-jinja2 2.11.2-1
python3-jwt 1.7.1-2ubuntu2
python3-keyring 21.3.0-1
python3-kiwisolver 1.2.0-1
python3-launchpadlib 1.10.13-1
python3-lazr.restfulclient 0.14.2-2build1
python3-lazr.uri 1.0.5-1
python3-ldb 2:2.1.4-2ubuntu0.1
python3-lib2to3 3.8.10-0ubuntu1~20.10
python3-lockfile 1:0.12.2-2.2
python3-louis 3.14.0-1
python3-lxml:amd64 4.5.2-1ubuntu0.4
python3-macaroonbakery 1.3.1-1
python3-magic 2:0.4.15-4
python3-mako 1.1.2+ds1-1
python3-markdown 3.2.2-2
python3-markupsafe 1.1.1-1
python3-matplotlib 3.3.0-3
python3-minimal 3.8.6-0ubuntu1
python3-monotonic 1.5-3
python3-nacl 1.4.0-1
python3-nautilus 1.2.3-3
python3-netifaces 0.10.4-1ubuntu4
python3-notify2 0.3-4
python3-numpy 1:1.18.4-1ubuntu1
python3-oauthlib 3.1.0-2
python3-olefile 0.46-2
python3-openssl 19.1.0-2
python3-paramiko 2.7.1-2ubuntu1
python3-path-and-address 2.0.1-2
python3-pexpect 4.6.0-4
python3-pil:amd64 7.2.0-1ubuntu0.3
python3-pip 20.1.1-2
python3-pkg-resources 49.3.1-2
python3-ply 3.11-4
python3-problem-report 2.20.11-0ubuntu50.7
python3-protobuf 3.12.3-2ubuntu2
python3-psutil 5.7.2-1
python3-ptyprocess 0.6.0-1ubuntu1
python3-pyasn1 0.4.8-1
python3-pyatspi 2.38.0-1
python3-pycryptodome 3.9.7+dfsg1-1
python3-pygame 1.9.6+dfsg-3
python3-pygments 2.3.1+dfsg-4ubuntu0.2
python3-pyinotify 0.9.6-1.2ubuntu1
python3-pymacaroons 0.13.0-3
python3-pyparsing 2.4.7-1
python3-pysmi 0.3.2-2
python3-pysnmp4 4.4.6+repack1-2
python3-pystache 0.5.4-6.1
python3-renderpm:amd64 3.5.47-1
python3-reportlab 3.5.47-1
python3-reportlab-accel:amd64 3.5.47-1
python3-requests 2.23.0+dfsg-2
python3-requests-unixsocket 0.2.0-2
python3-rfc3339 1.1-2
python3-scour 0.37-4build1
python3-secretstorage 3.1.2-1
python3-setproctitle:amd64 1.1.10-2
python3-setuptools 49.3.1-2
python3-simplejson 3.17.0-1
python3-six 1.15.0-1
python3-software-properties 0.99.3.1
python3-soupsieve 2.0.1-1
python3-speechd 0.10.1-2
python3-sss 2.3.1-3ubuntu4
python3-systemd 234-3build2
python3-talloc:amd64 2.3.1-1
python3-tk:amd64 3.8.10-0ubuntu1~20.10
python3-tz 2020.1-2
python3-uno 1:7.0.6-0ubuntu0.20.10.1
python3-update-manager 1:20.10.6
python3-urllib3 1.25.9-1
python3-wadllib 1.3.4-1
python3-webencodings 0.5.1-2
python3-websocket 0.53.0-2ubuntu1
python3-werkzeug 1.0.1+dfsg1-2
python3-wheel 0.34.2-1
python3-xdg 0.26-3ubuntu1
python3-xkit 0.5.0ubuntu4
python3-yaml 5.3.1-2ubuntu0.1
python3.8 3.8.10-0ubuntu1~20.10.1
python3.8-dev 3.8.10-0ubuntu1~20.10.1
python3.8-minimal 3.8.10-0ubuntu1~20.10.1
```

All Python modules installed on the server machine:
```console
python3 -m pip list
Package                 Version
----------------------- ---------------
apturl                  0.5.2
bcrypt                  3.1.7
beautifulsoup4          4.9.1
blinker                 1.4
bottle                  0.12.15
Brlapi                  0.7.0
ccsm                    0.9.14.1
certifi                 2020.4.5.1
chardet                 3.0.4
chrome-gnome-shell      0.0.0
click                   7.1.2
colorama                0.4.3
command-not-found       0.3
compizconfig-python     0.9.14.1
cryptography            3.0
cupshelpers             1.0
cycler                  0.10.0
dbus-python             1.2.16
defer                   1.0.6
distro                  1.5.0
distro-info             0.23ubuntu1
docker                  4.1.0
docopt                  0.6.2
duplicity               0.8.12.0
evdev                   1.3.0
fasteners               0.14.1
Flask                   1.1.2
folder-color            0.0.86
folder-color-common     0.0.86
future                  0.18.2
Glances                 3.1.4.1
html5lib                1.1
httplib2                0.18.1
idna                    2.10
influxdb                5.2.3
itsdangerous            1.1.0
jeepney                 0.4.3
Jinja2                  2.11.2
joblib                  0.17.0
keyring                 21.3.0
kiwisolver              1.3.1
language-selector       0.1
launchpadlib            1.10.13
lazr.restfulclient      0.14.2
lazr.uri                1.0.5
lockfile                0.12.2
louis                   3.14.0
lxml                    4.5.2
macaroonbakery          1.3.1
Mako                    1.1.2
Markdown                3.2.2
MarkupSafe              1.1.1
matplotlib              3.3.3
memory-profiler         0.58.0
meson                   0.55.3
monotonic               1.5
netifaces               0.10.4
notify2                 0.3
numpy                   1.19.4
oauthlib                3.1.0
olefile                 0.46
pandas                  1.1.4
paramiko                2.7.1
path-and-address        2.0.1
pexpect                 4.6.0
Pillow                  7.2.0
pip                     20.1.1
ply                     3.11
protobuf                3.12.3
psutil                  5.7.3
pyasn1                  0.4.8
pycairo                 1.16.2
pycryptodomex           3.9.7
pycups                  2.0.1
pygame                  1.9.6
pygame-gui              0.4.2
Pygments                2.3.1
PyGObject               3.38.0
pyinotify               0.9.6
PyJWT                   1.7.1
pymacaroons             0.13.0
PyNaCl                  1.4.0
pyOpenSSL               19.1.0
pyparsing               2.4.7
pyRFC3339               1.1
pysmi                   0.3.2
pysnmp                  4.4.6
pystache                0.5.4
python-apt              2.1.3+ubuntu1.4
python-dateutil         2.8.1
python-debian           0.1.37
python-magic            0.4.16
pytz                    2020.1
pyxdg                   0.26
PyYAML                  5.3.1
ranger-fm               1.9.3
reportlab               3.5.47
requests                2.23.0
requests-unixsocket     0.2.0
scikit-learn            0.23.2
scipy                   1.5.4
scour                   0.37
screen-resolution-extra 0.0.0
SecretStorage           3.1.2
setproctitle            1.1.10
setuptools              49.3.1
simplejson              3.17.0
six                     1.15.0
soupsieve               2.0.1
ssh-import-id           5.10
system-service          0.3
systemd-python          234
threadpoolctl           2.1.0
ubuntu-advantage-tools  27.0
ubuntu-drivers-common   0.0.0
ufw                     0.36
unattended-upgrades     0.1
urllib3                 1.25.9
usb-creator             0.3.7
wadllib                 1.3.4
webencodings            0.5.1
websocket-client        0.53.0
Werkzeug                1.0.1
wheel                   0.34.2
xkit                    0.0.0
```