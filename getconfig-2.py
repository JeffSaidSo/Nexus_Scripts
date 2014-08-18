#message format=json command type=cli_show_ascii
#This script uses an input file containing switch IP's and goes to each switch and saves the configs locally in the user-specified directory
import sys
import getpass
import os
import datetime
import requests
import json
import fileinput
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
import ssl

class MyAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block = False):
        self.poolmanager = PoolManager(num_pools = connections,
                                       maxsize = maxsize,
                                       block = block,
                                       ssl_version = ssl.PROTOCOL_SSLv3)
        
#Test to see if the user added an input file argument to the command line
try:
        input = (sys.argv[1]) 
except IndexError:
        os.system('cls' if os.name == 'nt' else 'clear')
        print "GetConfig gathers configs from any number of supported Cisco Nexus Switches\n"
        print "Usage: GetConfig.py <input_file>"
        print "The input file is a simple text file with a single switch IP on each line"
        print "like this:\n192.168.0.4\n192.168.0.5\n192.168.0.6"       

# if input file argument is present, test to see if the file exists
else:   
        if os.path.isfile(input) == False:
                print "Input File not found"
        else:

        
                #user input needed for each switch stored to global variables so we only ask once.
                #password is collected using getpass so it is not echoed to the screen
                switchuser = raw_input ("Enter username: ")
                switchpassword = getpass.getpass("Please enter password:") 
                defaultdir = os.getcwd()
                localdir = raw_input ("Enter a local DIRECTORY to save the switch config(s) (default is):" + defaultdir + ": ")
                #check to see if user input for config storage directory was received; if not, default to OS CWD path
                if len(localdir) == 0:
                        localdir = defaultdir
                        
                #check to see if user input for config storage directory is valid; if not, loop until valid                
                while os.path.isdir(localdir) == False:
                        print '"%s"'%localdir + " does not appear to be a valid directory"
                        localdir = raw_input ("Enter a local DIRECTORY to save the switch config(s): ")

                #Read input file from the command line and begin processing. Using a FOR loop to grab each line of the input file
                os.system('cls' if os.name == 'nt' else 'clear')        
                for line in fileinput.input():
                        #stripping carriage return from IP addresses
                        line = line.rstrip()
                        #each line instance is a switch IP address
                        url = "http://" + line + "/ins"                   
                        # the "show run" and "show switchname" payloads that will be sent to the switch
                        config_headers = {'content-type':'application/json'}
                        payload = {
                          "ins_api": {
                                "version": "1.0",
                                "type": "cli_show_ascii",
                                "chunk": "0",
                                "sid": "1",
                                "input": "show run",
                                "output_format": "json"
                          }
                        }
                        sname_headers = {'content-type':'application/json'}
                        payload2 = {
                          "ins_api": {
                                "version": "1.0",
                                "type": "cli_show_ascii",
                                "chunk": "0",
                                "sid": "1",
                                "input": "show switchname",
                                "output_format": "json"
                          }
                        }
                        
                        print "Contacting: " + line
                        # Using 'requests' to contact the switch and send payloads. Timeout skips switches that are unreachable/unsupported. 
                        try:                            
                            myRequest = requests.Session()
                            myRequest.mount('https://', MyAdapter())
                            response_config = myRequest.post(url, verify=False, timeout = 10, data = json.dumps(payload), headers = config_headers,auth = (switchuser,switchpassword)).json()
                            response_sname = myRequest.post(url,verify = False, timeout = 5, data = json.dumps(payload2), headers = sname_headers,auth = (switchuser,switchpassword)).json()
                            
                        except ValueError:
                            print "Invalid Username/password combination on " + line
                        except requests.exceptions.InvalidURL:
                            print "Invalid URL"
                        except requests.exceptions.ConnectionError:
                            print "No Connection to " + line + "\nIf switch is supported and reachable, verify NXAPI feature is enabled:"
                            print "Example:\nswitch#Conf t\nswitch(config)#feature nxapi\n"
                        except requests.exceptions.Timeout:
                            print "Switch is not reachable"
                        else:                           
                            
                            #Turn response into human readable switch config                 
                            formatted_config = response_config['ins_api']['outputs']['output']['body']
                            switchname = response_sname['ins_api']['outputs']['output']['body']                        
                            #remove CRLF from switchname response; Use switchname + date\time to create output filename
                            path = localdir + os.sep + switchname.rstrip() + datetime.datetime.now().strftime("-%m-%d-%Y{%H.%M.%S}.txt")                            
                            #Open output file for writing
                            configfile = open(path, "w")
                            configfile.write(formatted_config)
                            #close file
                            configfile.close()
                            print "config written to " + path + "\n"
