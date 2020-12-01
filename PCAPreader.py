# -*- coding: utf-8 -*-
"""
Created on Wed Oct 28 08:13:47 2020

@author: Noooberino
"""

import argparse
import os
import sys
import csv
import scapy
import scapy.utils
import dpkt
import socket
import inspect

from scapy.all import *
from scapy.utils import RawPcapReader


import pyshark

def process_pcap_scapy(file_name):
    print('Opening {}...'.format(file_name))

    # test RawPcapReader (returning each package as string)
    count = 0
    for (pkt_data, pkt_metadata,) in RawPcapReader(file_name):
        count += 1
        
    print('{} contains {} packets'.format(file_name, count))
    input('>> press enter to continue...')
    
    # test rdpcap
    #pcap = PcapReader(file_name)
    pcap = rdpcap(file_name)
    print(pcap)
    
    
    sessions = pcap.sessions()
    print(sessions)
    input('>> press enter to continue...')
    
    summary = pcap.summary()
    print(summary)
    input('>> press enter to continue...')
    
    
    
    count = 0 
    for packet in pcap:
        count += 1
        print('Packet-Number:', count)
        print(type(packet))
        #if packet.haslayer(TLS):
        #    print('Protocol:', packet.tls.proto)
        #input('press enter to continue...')
        #print(packet[IP])
        if Ether in packet:
            print(packet[Ether].dst)
            print(packet[Ether].src)
            packet[Ether].show()
        
        # https://stackoverflow.com/questions/46583686/scapy-getlayer-options
        
        if IP in packet:
            print(packet[IP].dst)
            print(packet[IP].src)
            packet[IP].show()
        #if Raw in packet:
        #    print(packet[Raw].load)
        #input('press enter to continue...')
    
    # open pcap in wireshark (doesnt work)
    wireshark(pcap)
    
    
    return

def process_pcap_dpkt(file_name):
    #f = open(r'C:\Users\Noooberino\shared\Patrick\BsC\sample.pcap','rb')
    f = open(file_name,'rb')
    pcap = dpkt.pcap.Reader(f)
    print('Type(pcap):', type(pcap))
    print('Attributes pcap:\n', dir(pcap))

    input('>> press enter to continue...')
    
    count = 0 
    for (ts,buf) in pcap:
        count += 1
        print('Packet-Number:', count)
        print('Type(ts):', type(ts))
        print('Timestamp ts:', ts)
        print('Type(buf):', type(buf))
        print(buf)
        try:
            eth = dpkt.ethernet.Ethernet(buf)
            print('Attributes eth:\n', dir(eth))
            print('Attributes eth.ip:\n', dir(eth.ip))
            print('Attributes eth.data:\n', dir(eth.data))
            print('Destinatino IP:', socket.inet_ntoa(eth.data.dst))
            print('Source IP:', socket.inet_ntoa(eth.data.src))
            print('Type(eth):', type(eth))
            #print(eth)
            
        except:
            pass
    
    
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PCAP reader')
    parser.add_argument('--pcap', metavar='<pcap file name>',
                        help='pcap file to parse', required=True)
    args = parser.parse_args()
    
    file_name = args.pcap
    if not os.path.isfile(file_name):
        print('"{}" does not exist'.format(file_name), file=sys.stderr)
        sys.exit(-1)


    process_pcap_scapy(file_name)
    
    process_pcap_dpkt(file_name)
    
    #pcap = pyshark.FileCapture(file_name)
    
    # https://scapy.readthedocs.io/en/latest/api/scapy.utils.html#scapy.utils.PcapReader
    # https://scapy.readthedocs.io/en/latest/api/scapy.layers.html
    #pcap = rdpcap(file_name)
    
    
    # https://stackoverflow.com/questions/20093238/get-ip-addresses-from-pcap-file-in-scapy
    
    
    
    # https://osric.com/chris/accidental-developer/2020/04/modifying-a-packet-capture-with-scapy/
    # https://scapy.readthedocs.io/en/latest/usage.html?highlight=timestamp#tcp-timestamp-filtering
    

       
    sys.exit(0)