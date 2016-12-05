#!/usr/bin/env python
from __future__ import print_function
from contextlib import contextmanager
from xml.etree import ElementTree as et
import os
import sys
import re
import fileinput
import subprocess as sb

__version__ = '0.2 - Beta'
__author__ = 'Michael Taylor - mike.taylor@autodesk.com'


@contextmanager
def ignored(*exceptions):
    try:
        yield
    except exceptions:
        pass


file_list = ['/etc/hosts', '/usr/discreet/backburner/Network/backburner.xml']


def parser():
    with ignored(OSError):
        with open(file_list[0], 'r') as f:
            hostfile = f.readlines()
        with open(file_list[1], 'r') as f:
            bb_xml = f.read()
            return hostfile, bb_xml


def primary_int():
    """ primary_int function performs the following actions:
           1. Checks kernel - Parses routing table for default route
           2. Stores the flagged gateway interface
           3. returns primary interface as "gw_int"
    """

    if kernel == 'linux':
        with open('/proc/net/route', 'r') as f:
            route_table = f.readlines()
        route_tb = [lines.split() for lines in route_table]
        zero = '00000000'
        gw_int = []
        for line in route_tb:
            if line[1] == zero and line[7] == zero:
                gw_int.append(line[0])

    if kernel == 'darwin':
        cmd = ['route', 'get', '224.0.0.1']
        ip_match = re.compile('(?<=interface:\s)\w+.*?')
        ip_from_gw_int, err = sb.Popen(cmd, stdout=sb.PIPE).communicate()
        gw_int = re.findall(ip_match, ip_from_gw_int)
    return gw_int


def correct_hostfile(primary_ip):
    """ correct_hostfile function compares the ip address assigned
        to the primary_interface, against the resolved entry in
        the /etc/hosts file.
    """
    _hostname = os.uname()[1]
    print('Making corrections to /etc/hosts file (backup file saved as .backup)')

    for line in fileinput.input('/etc/hosts', inplace=1, backup='.backup'):
        if primary_ip not in line:
            if _hostname not in line.split():
                sys.stdout.write(line)

    with open('/etc/hosts', 'a+') as host_add:
        newline = [primary_ip, '\t', _hostname, '\n']
        for item in newline:
            host_add.write('%s' % item)


def backburner_fix(xml, ipaddr):
    """This function does (4) operations:
       (1) Stops backburner services
       (2) Checks whether the backburner manager is remote or local.
       (3) Then corrects the xml file if needed.
       (4) Starts backburner services
    """
    host = os.uname()[1]

    #Stopping backburner
    print('Performing backburner.xml checks...')
    print('Stopping backburner services')
    cmd = '/etc/init.d/backburner'
    pid = sb.Popen([cmd, 'stop'])
    pid.wait()

    tree = et.fromstring(xml)
    m_name = tree.getiterator('ManagerName')[0]
    s_name = tree.getiterator('ServerName')[0]

    #Manager correction
    if m_name.text != host and \
       m_name.text != ipaddr and \
       m_name.text != 'localhost':
        print('Manager %s does not match hostname!' % (m_name.text))
    while True:
        try:
            ans = raw_input('Are you using a remote manager? (y/n) ')

            if ans == 'y' or ans == 'yes':
                print('Skipping manager name correction')
            elif ans == 'n' or ans == 'no':
                print('Correcting the manager name to the local workstation IP')
                m_name.text = ipaddr
            else:
                raise ValueError
                continue
        except ValueError:
            print("Sorry, I didn't understand the input")
        else:
            break
    #Server correction
    if s_name.text != os.uname()[1] and \
       s_name.text != ipaddr and \
       s_name.text != 'localhost':
        print('Server name mismatch in backburner.xml..')
        s_name.text = ipaddr
        print('Corrected!')

    data = et.ElementTree(tree)
    data.write(file_list[1])

    #Starting Backburner
    start_pid = sb.Popen([cmd, 'start'])
    start_pid.wait()




def get_ipaddr(gw_int):
    """Returns the primary IP address"""
    if kernel == 'linux':
        cmd = ['ip', 'addr', 'show', gw_int[0]]
        ip_from_gw_int, err = sb.Popen(cmd, stdout=sb.PIPE).communicate()
        primary_ip = re.findall('\d+\.\d+\.\d+\.\d+', ip_from_gw_int)[0]

    if kernel == 'darwin':
        ip_search = re.compile('(?<=inet\s)\d+\.\d+\.\d+\.\d+')
        cmd_ifcfg = ['ifconfig', gw_int[0]]
        ip_data, err = sb.Popen(cmd_ifcfg, stdout=sb.PIPE).communicate()
        primary_ip = re.findall(ip_search, ip_data)[0]

    return primary_ip


def main():
    """ The main function does (3) operations:
         1. Setup the /etc/hosts file to be hashed
            into a dictionary for corrections.
         2. Stores backburner.xml data into bb_xml
         3. Locates primary interface & ip address
    """
    hostfile, bb_xml = parser()

    ips_match = re.compile('^\d+\.\d+\.\d+\.\d+')
    host_match = re.compile('^\s*\d+\.\d+\.\d+\.\d+')

    ips = [ln.split()[0] for ln in hostfile if re.findall(ips_match, ln)]
    names = [ln.split()[1:] for ln in hostfile if re.findall(host_match, ln)]
    host_table = dict(zip(ips, names))
    ipaddr = get_ipaddr(primary_int())

    correct_hostfile(ipaddr)
    backburner_fix(bb_xml, ipaddr)


if __name__ == '__main__':
    try:
        kernel = os.uname()[0].lower()
    except AttributeError:
        sys.exit("This operating system is not supported")
    else:
        if os.geteuid() != 0:
            sys.exit("You need to have root privileges to run this script")
        main()
