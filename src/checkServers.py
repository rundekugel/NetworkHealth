#!/usr/bin/env python
# checkServers.py

"""
This is to check, if server is available, tcp and / or web- service running
Used by checkSomeServers.py

for copyright see: MIT License
2018 by lifesim.de

"""

__author__ = "rundekugel@github"
__version__ = "0.1.4"

import time
import sys
import icmplib
import socket
from contextlib import closing

class globs:
    timeout = 1.5

def ping(host, verbosity=1):
    """
    Returns time to responds, if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """
    res = None
    try:
        # p = multiping.MultiPing([host])
        p = icmplib.ping(host, count=1, timeout=globs.timeout, privileged=False)
        r, rn = p.min_rtt, p.packets_received
        if verbosity > 1:
            print ('ping: %sms; OK:%s' % (str(r), str(rn)))
        res = round(r, 3)
        if verbosity > 0:
            print (res)
        if p.packets_received == 0:
            return None
    finally:
        return res


def checkTcpPort(host, port, verbosity=1):
    """

  :rtype: object
  """
    BUFFER_SIZE = 1024
    result = 1
    try:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.settimeout(globs.timeout)
            r=s.connect_ex((host, port))
            result = r
    except:
        result = 2

    return result


def checkHttp(url, verbosity=1, verifysslcert=False, timeout=globs.timeout):
    """
    test if url exists. port can also be part of url.
  """
    import requests
    result = None
    if timeout is None:
        timeout = globs.timeout
    try:
        r = requests.head(url, verify=verifysslcert, timeout=timeout)
        if r.status_code >=300 and r.status_code <=308:
            result = 0
        elif r.status_code in (200,202,401):
            result = 0
        else:
            result = r.status_code
    except:
        import traceback
        if verbosity > 1:
            print (traceback.format_exc())

    return result


# -----  prepared test_port with check for filtered/closed/open/error ---------
# from https://www.redhat.com/sysadmin/test-tcp-python-scapy
class TcpFlags:
    """
    https://www.wireshark.org/docs/wsug_html_chunked/ChAdvTCPAnalysis.html
    """
    SYNC_ACK = 0x12
    RST_PSH = 0x14


class IcmpCodes():
    """
    ICMP codes, to decide
    https://www.ibm.com/docs/en/qsip/7.4?topic=applications-icmp-type-code-ids
    """
    Host_is_unreachable = 1
    Protocol_is_unreachable = 2
    Port_is_unreachable = 3
    Communication_with_destination_network_is_administratively_prohibited = 9
    Communication_with_destination_host_is_administratively_prohibited = 10
    Communication_is_administratively_prohibited = 13


#FILTERED_CODES = [x.value for x in IcmpCodes]


class RESPONSES:
    """
    Customized responses for our port check
    """
    FILTERED = 0
    CLOSED = 1
    OPEN = 2
    ERROR = 3


def test_port(
        address: str,
        dest_ports: int,
        verbose: bool = False
) -> RESPONSES:

    import os
    import sys
    import traceback
    from enum import IntEnum
    from pathlib import Path
    from random import randint
    from typing import Dict, List
    from argparse import ArgumentParser
    from scapy.layers.inet import IP, TCP, ICMP
    from scapy.packet import Packet
    from scapy.sendrecv import sr1, sr

    NON_PRIVILEGED_LOW_PORT = 1025
    NON_PRIVILEGED_HIGH_PORT = 65534
    ICMP_DESTINATION_UNREACHABLE = 3

    """
    Test the address + port combination
    :param address:  Host to check
    :param dest_ports: Ports to check
    :return: Answer and Unanswered packets (filtered)
    
    Author: Jose Vicente Nunez <@josevnz@fosstodon.org>
    """
    src_port = randint(NON_PRIVILEGED_LOW_PORT, NON_PRIVILEGED_HIGH_PORT)
    ip = IP(dst=address)
    ports = TCP(sport=src_port, dport=dest_ports, flags="S")
    reset_tcp = TCP(sport=src_port, dport=dest_ports, flags="S")
    packet: Packet = ip / ports
    verb_level = 0
    if verbose:
        verb_level = 99
        packet.show()
    try:
        answered = sr1(
            packet,
            verbose=verb_level,
            retry=1,
            timeout=1,
            threaded=True
        )
        if not answered:
            return RESPONSES.FILTERED
        elif answered.haslayer(TCP):
            if answered.getlayer(TCP).flags == TcpFlags.SYNC_ACK:
                rst_packet = ip / reset_tcp
                sr(rst_packet, timeout=1, verbose=verb_level)
                return RESPONSES.OPEN
            elif answered.getlayer(TCP).flags == TcpFlags.RST_PSH:
                return RESPONSES.CLOSED
        elif answered.haslayer(ICMP):
            icmp_type = answered.getlayer(ICMP).type
            icmp_code = int(answered.getlayer(ICMP).code)
            if icmp_type == ICMP_DESTINATION_UNREACHABLE and icmp_code in FILTERED_CODES:
                return RESPONSES.FILTERED
    except TypeError:
        traceback.print_exc(file=sys.stdout)
        return RESPONSES.ERROR



def main():
    result = 1
    port = 80
    if len(sys.argv) < 2:
        print( 'parameter missing!')
        return 1
    else:
        url = sys.argv[1]
        hostname = url.replace('http://', '', 1)
        if hostname[:5] == 'https':
            port = 443
            hostname = url.replace('https://', '', 1)
        h = hostname.split('/')[0]
        h = h.split(':')
        hostname = h[0]
        if len(h) > 1:
            if verbosity:
                print( h[1])
            if h[1] != '':
                try:
                    port = int(h[1], 10)
                except:
                    pass

        result = ping(hostname)
        if result != None:
            if verbosity:
                print( hostname + ' is up!')
        else:
            print( hostname + ' is down!')
        if result != None:
            if 0 == checkTcpPort(hostname, port):
                if verbosity:
                    print( hostname + ' tcp ' + str(port) + ' open.')
            else:
                print( hostname + 'tcp ' + str(port) + ' unreachable!')
                result |= 64
        r = checkHttp(url)
        if r==None:
            print("Server nicht erreichbar [" + str(r) + '] ' + url)
        elif r > 0:
            result |= 32
            print( 'url problem=[' + str(r) + '] ' + url)
        elif verbosity:
            print( 'ok: ' + url)
        return result


if __name__ == '__main__':
    sys.exit(main())
# okay decompiling checkServers.pyc
