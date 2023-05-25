#!/usr/bin/env python
# checkServers.py

"""
This is to check, if server is available, tcp and / or web- service running
Used by checkSomeServers.py

for copyright see: MIT License
2018 by lifesim.de

"""

__author__ = "rundekugel@github"
__version__ = "0.1.3"

import time
import sys
import icmplib

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
    import socket
    BUFFER_SIZE = 1024
    result = 1
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(globs.timeout)
    try:
        s.connect((host, port))
        time.sleep(0.7)
        s.close()
        result = 0
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
