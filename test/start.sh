#!/bin/bash
echo start Network Heath check...
echo to test, type in console:
echo nc -lk 7777
echo and kill it after a few seconds

# for 1st positive tests
nc -l 7777 &
nc -lk 8080 &

../src/checkSomeServers.py checkServersConfig.json
