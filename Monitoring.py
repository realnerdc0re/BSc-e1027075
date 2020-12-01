# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 11:12:06 2020

@author: Noooberino
"""

# https://psutil.readthedocs.io/en/latest/
import psutil
import os

# https://pypi.org/project/memory-profiler/
from memory_profiler import profile

# https://medium.com/the-andela-way/machine-monitoring-tool-using-python-from-scratch-8d10411782fd
# https://medium.com/survata-engineering-blog/monitoring-memory-usage-of-a-running-python-program-49f027e3d1ba


# https://www.geeksforgeeks.org/memory-profiling-in-python-using-memory_profiler/
@profile
def monitor():
    # https://psutil.readthedocs.io/en/latest/#processes
    # get all process IDs & total cpu usage of the system
    processids = psutil.pids()
    cputotalvalue = psutil.cpu_percent(interval=1)
    
    # get process ID & cpu usage of the current process
    processid = os.getpid()
    processidinfos = psutil.Process(processid)
    cpupidvalue = processidinfos.cpu_percent(interval=1)
    
    
    print('\n\n'+40*'~'+' SCRIPT: Monitoring.py '+40*'~')
    print('\nCPU (total): {}'.format(cputotalvalue))
    print('\n\nPIDs: {}'.format(processids))
    
    print('\n\n'+20*'~'+' SCRIPT: Monitoring.py, all running processes '+20*'~'+'\n')
    for pid in processids:
        print('PID {}: {}'.format(pid, psutil.Process(pid)))
    
    # https://psutil.readthedocs.io/en/latest/#process-class
    # can be used to speed up value caching by a lot
    # fetch infos from current process of this script
    with processidinfos.oneshot():
        print('\n\n'+20*'~'+' SCRIPT: Monitoring.py, .oneshot() '+20*'~'+'\n')
        print('name: ', processidinfos.name())
        print(processidinfos.exe())
        print(processidinfos.cpu_times())
        print('cpu usage: ', processidinfos.cpu_percent())
        print('\nmemory-info:\n', processidinfos.memory_info())
        # outputs memory usage of all processes running
        print('\nmemory-map:\n', processidinfos.memory_maps())
        print('\nfull memory-info:\n', processidinfos.memory_full_info())
        
    
    # has to be tested when actual workload is happening, right now always outputs zero
    print('\n\n'+20*'~'+' SCRIPT: Monitoring.py, current python process '+20*'~'+'\n')
    print('PID number: {}'.format(processid))
    print('PID infos: {}'.format(processidinfos))
    print('CMD: {}'.format(processidinfos.cmdline()))
    print('CPU (PID={}): {}'.format(processid, cpupidvalue))



if __name__ == '__main__':
    
    monitor()
 
    
    

    