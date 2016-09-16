#!/usr/bin/env python
from __future__ import print_function
import time
import os
import sys
import socket 
import re
import fileinput
import subprocess as sb 
from xml.etree import ElementTree as et
from pprint import pprint

'''
Script to correct /etc/hosts and common MacOS / Linux networking issues
'''

__version__ = '0.1 - Beta testing'
__author__ = 'Michael Taylor - mike.taylor@autodesk.com'


def file_exists(path):
    if os.path.isfile(path):
        parser(path)

        
def parser(file):
    if file[-5:] == 'hosts':
        with open(file, 'r') as f:
            file_data = f.readlines()
        hostfile.file_data = file_data
        hostfile.file_path = str(file)

    elif file[-3:] == 'xml':
        with open(file, 'r+') as f:
            file_data = f.read()
        bb_xml.file_data = file_data
        bb_xml.file_path = str(file)

    elif file[-3:] == 'cfg':
        with open(file, 'r+') as f:
            file_data = f.read()
        wt_cfg.file_data(file_data)
        wt_cfg.file_path = str(file)

    elif file[-3:] == 'map':
        with open(file, 'r+') as f:
            file_data = f.read()
        fs_map.file_data(file_data)        
        fs_map.file_path = str(file)


class FileInfo(object):
    def __init__(self):
        self.ips = []
        self.hostnames = []
        self.host_table = {}
        self.file_path = ''
        self.file_data = ''

    def file_data(self, file_data):
        self.file_data = file_data

    def __len__(self):
        return len(self.file_data)

    def __iter__(self):
        return iter(self.file_data)

    def __str__(self):
        return str(self.file_data)


class SystemInfo(object):
    def __init__(self):
        self.gw_int = None
        self.primary_int = None
        self.primary_ip = None

    def set_gateway(self, gw_int):
        self.gw_int = gw_int
        
    def set_ip(self, primary_ip):
        self.primary_ip = primary_ip
    
    def info(self):
        return self.primary_ip, self.gw_int
        

def setup():
    ips_match = re.compile('\d+\.\d+\.\d+\.\d+')
    host_match = re.compile('^\s*\d+\.\d+\.\d+\.\d+')
    
    hostfile.ips = re.findall(ips_match, str(hostfile))
    hostfile.hostnames = [line.split()[1:] for line in hostfile.file_data if re.findall(host_match, line)]
    
    if os.uname()[0] == 'Linux':
        
        try:
            with open('/proc/net/route', 'r') as f:
                route_table = f.readlines()
            route_table = [lines.split() for lines in route_table]
            gw_int = [lines[0] for lines in route_table[1:] if lines[1] == '00000000' and lines[7] == '00000000']
            
            hipmachine.set_gateway(gw_int[0])    

            cmd = ['ip', 'addr', 'show', gw_int[0]]
            ip_from_gw_int, err = sb.Popen(cmd, stdout=sb.PIPE).communicate()
            primary_ip = re.findall('\d+\.\d+\.\d+\.\d+',ip_from_gw_int)[0]
             
            hipmachine.set_ip(primary_ip)
        except IndexError:
            print('Unable to locate gateway flag in internal routing table')
            print('Please set a gateway so multicast traffic is possible')
            sys.exit()

    elif os.uname()[0] == 'Darwin':
        
        cmd = ['route', 'get', '224.0.0.1']
        ip_match = re.compile('(?<=interface:\s)\w+.*?')
        ip_from_gw_int, err = sb.Popen(cmd, stdout=sb.PIPE).communicate()
         
        gw_int = re.findall(ip_match, ip_from_gw_int)
        hipmachine.set_gateway(gw_int[0])
        
        ip_search = re.compile('(?<=inet\s)\d+\.\d+\.\d+\.\d+')
        cmd_ifcfg = ['ifconfig', gw_int[0]] 
        ip_data, err = sb.Popen(cmd_ifcfg, stdout=sb.PIPE).communicate()
        primary_ip = re.findall(ip_search, ip_data)
                
        hipmachine.set_ip(primary_ip[0])
        darwin_check() 
    else:
        print('Your operating system is not supported - Exiting script')
        sys.exit()

    if hostfile.ips.count(hipmachine.primary_ip) <= 1:
        hostfile.host_table = dict(zip(hostfile.ips, hostfile.hostnames))
        hosts_check()
    else:
        flush_ip(hipmachine.primary_ip) 
        hosts_check() 


def darwin_check():
    try:
        get_host_cmd = ['scutil', '--get', 'HostName', '&>', '/dev/null']
        host_id, err = sb.Popen(get_host_cmd, stdout=sb.PIPE).communicate()

        get_comp_cmd = ['scutil', '--get', 'ComputerName', '&>', '/dev/null']
        comp_id, err = sb.Popen(get_comp_cmd, stdout=sb.PIPE).communicate()

        set_host_cmd = ['scutil', '--set', 'HostName', os.uname()[1]]
        set_comp_cmd = ['scutil', '--set', 'ComputerName', os.uname()[1]]

        if host_id.rstrip() != os.uname()[1] or comp_id.rstrip() != os.uname()[1]:
            sb.call(set_host_cmd)
            sb.call(set_comp_cmd)

        elif host_id.rstrip() == os.uname()[1] and comp_id.rstrip() == os.uname()[1]:
            print("No changes needed - hostname & computer name match")
    except Exception as e:
        print('Error encountered when parsing routing table')
        print('Exiting script')
        sys.exit(1)


def hosts_check():
    print('Making corrections to /etc/hosts file (backup file saved as .backup)')
    flush_ip(hipmachine.primary_ip)
    flush_host(hostname)
    append_host(hipmachine.primary_ip, hostname)
    backburner_correction(hostname)


def append_host(ip, hostname):
    with open('/etc/hosts', 'a+') as host_add:
        newline = [ip, '\t', hostname, '\n']
        for item in newline:
            host_add.write('%s' % item)


def flush_ip(ip):
    print('/etc/hosts is backed up')

    for line in fileinput.input('/etc/hosts', inplace=1, backup='.backup'):
        if not hipmachine.primary_ip in line:
            sys.stdout.write(line)


def flush_host(hostname):
    for line in fileinput.input('/etc/hosts', inplace=1):
        if not hostname in line.split():
            sys.stdout.write(line)


def backburner_correction(hostname):
    print("Stopping backburner server & local manager")
    stop_service()

    tree = et.parse(bb_xml.file_path)    
    root = tree.getroot()
    ServerSettings = root[3][0]
    ManagerName = ServerSettings[0]
    ServerName = ServerSettings[2]
    
    if ServerName.text == os.uname()[1]  and ManagerName.text == os.uname()[1]:
        print("backburner.xml's Server & Manager element match hostname - no changes needed")
        start_service()
    
    elif ServerName.text == 'localhost' and ManagerName.text == 'localhost':
        print("backburner.xml's Server & Manager elements are set to localhost - no changes needed")
        start_service()

    elif ManagerName.text != 'localhost' and ManagerName.text != os.uname()[1]:
        print("Your manager doesn't match your hostname:'{}'  or 'localhost'".format(os.uname()[1]))
        answer = raw_input("Is '{}' your correct backburner manager?(yes or no): ".format(ManagerName.text))
        
        if answer.lower() == 'yes' or answer.lower() == 'y':
            print("All done.")
            start_service()
            sys.exit()
        
        elif answer.lower() == 'no' or answer.lower() == 'n':
            ManagerName.text = raw_input('Please type the backburner manager hostname or ip address: ')
            ServerName.text = os.uname()[1] 
            tree.write(bb_xml.file_path)
            start_service()
            print("All done.")

    else:
        print('Your backburner.xml file has the following contents:')
        print('ManagerName = {manager_name}'.format(manager_name=ManagerName.text))
        print('ServerName = {server_name}'.format(server_name=ServerName.text))
        print("If you would like to correct the contents, a backup of the original will be made")
        ans = raw_input('Would like to correct this config?(Yes or No) ').lower()
        
        if ans == 'yes' or ans == 'y':
            print('Backing up copy of current backburner.xml to backburner.xml_backup')
        
            os.chdir( discreet_path + '/backburner/Network/')
            sb.call('cp -p backburner.xml  backburner.xml_backup', shell=True)
        
            print('''
            Modifying backburner.xml manger & server tokens 
            
            from:    
            ManagerName = {}
            ServerName  = {}
               
            to:
            ManagerName = {}
            ServerName  = {}
           
            '''.format(ManagerName.text, ServerName.text, os.uname()[1], os.uname()[1]))
    
            ManagerName.text = socket.gethostname()
            ServerName.text = socket.gethostname()
            
            tree.write('bb_xml.file_path')
            print("Correction done - starting backburner service")
            raw_input('Press any key to start backburner services')
            start_service()
                   

def start_service():
    if kernel == 'Linux':
        sb.call(['/etc/init.d/backburner_server start'], shell=True)
        sb.call(['/etc/init.d/backburner_manager start'], shell=True)
    else:
        sb.call(['/usr/discreet/backburner/backburner start'], shell=True)


def stop_service():
    if kernel == 'Linux':
        sb.call(['/etc/init.d/backburner_server stop'], shell=True)
        sb.call(['/etc/init.d/backburner_manager stop'], shell=True)
    else:
        sb.call(['/usr/discreet/backburner/backburner stop'], shell=True)


def main():
    file_list = ['/etc/hosts',
                discreet_path + 'backburner/Network/backburner.xml']

    for files in file_list:
        file_exists(files)
    setup()

if __name__ == '__main__':
    
    if os.geteuid() != 0:
        sys.exit("You need to have root privileges to run this script")

    hostname = os.uname()[1]
    kernel = os.uname()[0]
    
    df, err = sb.Popen(['df', '/'], stdout=sb.PIPE).communicate()
    df = df.split('\n')
    dskfree = df[1].split()[-2]

    if dskfree == '100%':
        print('Disk is full - please free space and rerun script')
        sys.exit(1)

    if os.path.isdir('/opt/Autodesk/io'):
        discreet_path = '/opt/Autodesk/'
    else:
        discreet_path = '/usr/discreet/'

    hipmachine = SystemInfo()
    hostfile = FileInfo()
    host_table = FileInfo()
    bb_xml = FileInfo()
    main()
