@echo off
echo start Network Heath check...
echo to test, start 2 applications to listen on ports 7777 and 8080
echo and kill them after a few seconds

python ..\src\checkSomeServers.py checkServersConfig.json
