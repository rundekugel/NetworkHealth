#!/usr/bin/env python

# -*- coding: utf-8 -*-
#  $Id: checkSomeServers.py 56 2022-06-07 09:32:59Z BEB $

"""
check if servers are reachable and can check for http service available
for linux this must be run as root, because of ping (icmp)
by rundekugel@github

usage: call with json-config file as param or:
-v=<0..n>   verbosity level. 0=errors; 1=changes; 2=status; more...
-sslv=<0|1> check ssl certs
"""

import json
import sys
import os
import time
import checkServers as cs

__author__ = "rundekugel@github"
__version__ = "0.1.3"

class Cconfig():
    # cfg_typ = 0
    # cfg_adr = 1
    # cfg_info = 2
    # cfg_info_bad = 3
    # cfg_sub = 4

    # cfg=[]
    # type = None
    # hostname = None
    # info = None
    # infoBad = None
    # # sub=None
    # subs = []
    # lastError = None
    # id=None

    def __init__(self, cfg, verbosity=1):
        # parsing json-cfg
        self.type = cfg.get("typ")
        self.hostname = cfg.get("host")
        self.id = cfg.get("id")
        self.info = cfg.get("info")
        self.infoBad = cfg.get("infobad")
        self.lastError = 0
        self.subs=[]
        lsubs = cfg.get("sub")  ; #self.subs=[]
        if lsubs:
            # if not isinstance(lsubs, list):
                # lsubs = [lsubs]
            lsubs=force2list(lsubs)    
            for sub in lsubs:
                if sub:
                    self.subs.append(Cconfig(sub))

    def valid(self):
        if self.type != None:
            return True
        else:
            return False

    def tostring(self):
        return json.dumps(self)
        ret = [str(self.type), str(self.hostname), str(self.id), str(self.info), str(self.infoBad),
               str(self.lastError)]
        ret = ";".join(ret)
        if self.subs:
            for sub in self.subs:
                ret += "[" + sub.tostring() + "]"
        return ret

    def copyOldResult(self, oldcfg):
        self.lastError = oldcfg.lastError
        if oldcfg.subs and self.subs:
            copyStatusFromOldCfgs(self.subs, oldcfg.subs)


def timestamp():
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %X")


def addlog(text, addtime=True, newLine=True):
    if addtime:
        text = timestamp() + " " + text
    if newLine:
        print(text)
    else:
        sys.stdout.write(text)

def force2list(itemOrList):
  #if no list, make a list from it
  if not itemOrList:
    return []
  if not isinstance(itemOrList, list):
    itemOrList=[itemOrList]
  return itemOrList
    
def checkOne(cfg, verbosity=1, verifysslcert=False, logOnlyChanges=False):
    msg = ""
    r = 0
    if not cfg.valid():
        if verbosity:
            addlog("bad data: " + str(cfg))
        cfg.lastError = -1
        return 1

    if verbosity > 2:
        addlog("checking [" + cfg.info + "] ...")
    a=CstatusText()
    #CstatusText.text="checking [" + cfg.info + "] ..."
    if cfg.type in ["ping","http","tcp","log","udp"]:
        a.callall("checking [" + str(cfg.info )+ "] ...")

    if cfg.type == "ping":  # ping it
        t = cs.ping(cfg.hostname, verbosity - 1 )
        if t:  # got result
            if verbosity > 3:
                addlog(cfg.hostname + ' is up!')
        else:
            r = 1
            msg = cfg.hostname + ' is down! '
            if t== 0.0:
                msg += "DNS ok."
            if cfg.info:
                msg += cfg.info

    if cfg.type == "http":  # test service
        r = cs.checkHttp(cfg.hostname, verbosity=verbosity, verifysslcert=verifysslcert)
        if r == None:
            msg = cfg.hostname + " server unavailable!"
            r=1
        elif r == 0:
            if verbosity > 3:
                addlog(cfg.hostname + ' is up!')
        else:
            msg = cfg.hostname + " http-service unavailable! [%i]"%r

    # test tcp
    if cfg.type == "tcp":
        port = 80
        # if cfg.hostname[0]=='[':  #seems to be ipv6
        # else:
        h = cfg.hostname.rsplit(':', 1)
        host = h[0]
        if len(h) > 1:
            port = int(h[1], 10)
        r = cs.checkTcpPort(host, port)
        if r == 0:
            if verbosity > 3:
                addlog(cfg.hostname + ' is up!')
        else:
            msg = cfg.hostname + " tcp-port unavailable!"

    if r != 0:
        if cfg.infoBad:
            if cfg.infoBad[0] == "+":
                msg += " " + cfg.infoBad[1:]
            elif cfg.infoBad != "":
                msg = cfg.infoBad
        if verbosity:
          if logOnlyChanges:
            if r!=cfg.lastError:
              addlog(msg)
          else:
            addlog(msg)
    else:  # ok
        if cfg.lastError != 0 and verbosity:  # changed?
            if cfg.type[0] != '#':  # is it only a comment?
                msg = cfg.hostname
                if cfg.info:
                    msg += " " + cfg.info
                addlog(msg + " is back.")
    cfg.lastError = r

    if r == 0 and cfg.subs:
        for subcfg in cfg.subs:
            r += checkOne(subcfg, verbosity, verifysslcert)
    else:
        if cfg.subs:
            for subcfg in cfg.subs:
                subcfg.lastError = 1
    return r


def cfgArray2Objects(cfgArray):
    supercfg = []
    for cfg in cfgArray:
        supercfg.append(Cconfig(cfg))
    return supercfg


def loadCfgFromFile(filename, verbosity=1):
    cfgs = []
    try:
        f = open(filename, 'r')
        config = json.load(f)
        f.close()
        cfgs = cfgArray2Objects(config)
    except :
        addlog("error parsing json-file: " + str(filename))
        import traceback
        errMsg = traceback.format_exc().split('\n')[-2]  # the error reason only
        addlog(errMsg)
        return []
    return cfgs


def copyStatusFromOldCfgs(newconfigs, oldconfigs):
    try:
        for cfg in newconfigs:
            for ocfg in oldconfigs:
                if cfg.type == ocfg.type and cfg.hostname == ocfg.hostname:
                    # asume, they're the same ==> update
                    # cfg.lastError = ocfg.lastError
                    cfg.copyOldResult(ocfg)
                    continue
        return cfg
    except:
        return []
    return []

class CstatusText():
    text="init."
    callbacks=[]
    def register(self, cb):
        self.callbacks.append(cb)
    def unregister(self, cb):
        self.callbacks.remove(cb)
    def callall(self, text=None):
        if text==None:
            text=self.text
        for cb in self.callbacks:
            cb(text)

def usage():
    u = """
  usage: checkSomeServers.py [configfile] [options]
   configfile-default= "checkServers.json"
   -v<n>      verbosity 
   -i<n>      intervall in secs
   -r<n>      repeat n times. -1 for infinity
   -sslv<n>   verify ssl certs 0=no; 1=yes
   -noerr     suppress all system error messages
   -lc        log only changes
  use this:
    checkSoServers.py -v1 -i3 2> nul
  to ommit the warnings about missing ssl cert
  """
    return u


def main():
    # defaults
    repcnt = -1
    verbosity = 1
    interval = 1
    verifysslcert = 0
    configfile = "checkServers.json"
    cfgs = []
    logOnlyChanges=False
    _saveErrOut=sys.stderr 

    for p in sys.argv[1:]:
        if "-" == p[0]:
            if p[1] == "v":
                verbosity = int(p[2:], 10)
            if p[1] == "r":
                repcnt = int(p[2:], 10)
            if p[1] == "i":
                interval = int(p[2:], 10)
            if p[1:5] == "sslv":
                verifysslcert = p[5:] != '0'
            if p[1] == "?" or p[1] == 'h':
                print(usage())
            if p[1:] == "noerr":
                sys.stderr = open('nul', 'w')
            if p[1:] == "lc":
                logOnlyChanges=True
        else:
            configfile = p

    if not configfile:
        print(usage())
        sys.exit(1)

    if verbosity:
        print("Running...")

    a=CstatusText()
    #a.register(addlog)

        # mainloop
    while repcnt:
        repcnt -= 1
        r = 0
        # moved loadconfig inside the loop, so changed config doesn't need restart
        CstatusText.text = "load new config"
        a.callall("ca")
        ncfgs = loadCfgFromFile(configfile)
        if not ncfgs:
            addlog("no valid config!")
            time.sleep(1)
            continue
        copyStatusFromOldCfgs(ncfgs, cfgs)
        cfgs = ncfgs
          
        for cfg in cfgs:  
          if verbosity > 3:
            print(cfg.tostring())
          if cfg.type=="cfg":
            params=force2list(cfg.info)
            for p in params:
              p=p.split("=")
              if verbosity>1:
                addlog("cfg: "+str(id))
              try:
                if p[0]=="lc":
                  logOnlyChanges=int(p[1],10)
                if p[0]=="v":
                  verbosity=int(p[1],10)
                if p[0]=="noerr":
                  if int(p[1],10):
                    sys.stderr = open('nul', 'w')
                  else:
                    sys.stderr = _saveErrOut
                if p[0]=="sslv":
                  verifysslcert=int(p[1],10)
                if p[0] == "timeout":
                    t=verifysslcert=int(p[1],10)
                    if t:
                        cs.globs.timeout = t
              except:
                  import traceback
                  errMsg = traceback.format_exc().split('\n')[-2]  # the error reason only
                  print(errMsg)

        CstatusText.text = "check..."
        if verbosity:
            addlog("Check...    \r", newLine=0)
        for cfg in cfgs:
            try:
                r += checkOne(cfg, verbosity=verbosity, verifysslcert=verifysslcert, logOnlyChanges=logOnlyChanges)
            except:
                r += 1
        if verbosity > 1 or r > 0:
            addlog("--- done ---")
        else:
            if verbosity:
                addlog("--- done ---\r", newLine=0)
        time.sleep(interval)
        CstatusText.text="--- done ---"
        a.callall()
    if verbosity:
        addlog("end.")


main()

# eof
