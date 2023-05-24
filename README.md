# NetworkHealth
Check servers, services and internet connection.
Features:
- config via json-file
- ping a host
- check for open tcp ports
- check for http and https service 

## Usage
````
  usage: checkSoServers.py [configfile] [options]
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
 ````
## Config file
  the configuraion is done via json config file
  
### CFG
  A config entry can contain any of the command line configuraion params.
  Example:
````json 
[
  {"typ":"cfg", "info":["v=1","lc=1", "test-comment", "i=17","noerr=1","sslv=0"] },
  { "typ":" <more config lines> " }
]
  ````
  
### Ping
### TCP
````json 
  {"typ":"tcp", "host":"localhost:8080","info":"sub1.1"}
````
### HTTP 
  for HTTP and HTTPS services
````json   
  {"typ":"http", "host":"https://github.com",  "infobad":"+github webpage not available!"}
````  
### REM
  For remarks only
  
sub config arrays are executed only, if parent is ok.
  Example: 
````json  
[
  {"typ":"ping", "host":"8.8.8.8", "info":"google-dns for internet", "infobad":"google-dns nicht erreichbar. Keine Verbindung zum Internet!","sub":
     [
        {"typ":"ping", "host":"github.com",  "infobad":"+no connection to ipv4 github!"},
        {"typ":"http", "host":"https://github.com",  "infobad":"+github webpage not available!"}
    ]
  }
]
````
### Comments in json file
  if typ value starts with a # , the whole line is ignored
  
### Example
  see: test/checkServersConfig.json

  
