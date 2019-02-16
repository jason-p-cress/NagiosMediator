#!/usr/bin/python


##############################
#
# Nagios 5.5.8 mediator for IBM Predictive Insights
#
# 2/7/19 - Jason Cress (jcress@us.ibm.com)
#
###################################################

import urllib2
import json
import sys
import time
import re
import datetime
import os
import shlex
import csv
import StringIO
import logging


#############################
#
#  Funciton to read configuration file
#
#######################################

def load_properties(filepath, sep='=', comment_char='#'):
    """
    Read the file passed as parameter as a properties file.
    """
    props = {}
    with open(filepath, "rt") as f:
        for line in f:
            l = line.strip()
            if l and not l.startswith(comment_char):
                key_value = l.split(sep)
                key = key_value[0].strip()
                value = sep.join(key_value[1:]).strip().strip('"') 
                props[key] = value 
    return props

##############################
#
#  Function definition to write out a line to the appropriate csv file with metric data
#
#######################################################################################

def writePiCsvEntry(filename, csvheader, csvdatadef, csvDict, apiMonitorEntry):
   noWrite = 0
   csvLineToWrite = ""
   for headeritem in csvheader.split(','):
      headeritem = headeritem.strip('\"')
      myValueDef = csvDict[headeritem]
      extr = re.search('(^.+?)\[', myValueDef)
      if(extr):
         myOp = extr.group(1)
      else:
         print "FATAL: unable to determine operand in config for line in nagios metric definition file: " + csvdatadef      # should probably be determined in initial config file processing section...
         exit(0) 
      extr = re.search('^.+?\[(.*)\]', myValueDef)
      if(extr):
         myValue = extr.group(1)
      else:
         print "FATAL: malformed config line in Nagios metric definition file: " + csvdatadef     # should probably be determined in initial config file processing section...
         exit(0)
      if(myOp == 'var'):
         if(myValue == 'timestamp'):
            csvLineToWrite = csvLineToWrite + myTimeStamp
         else:
            print "FATAL: Unknown internal variable " + myValue + " in config, line: " + csvdatadef + ". Should be 'timestamp'"      # should probably be determined in initial config file processing section...
            exit(0) 
      elif(myOp == 'literal'):
         csvLineToWrite = csvLineToWrite + "," +  myValue
      elif(myOp == 'value'):
         csvLineToWrite = csvLineToWrite + "," + apiMonitorEntry[myValue]
      elif(myOp == 'regex'):
         extr = re.search('(.+?)\:', myValue)
         if(extr):
            apiJsonKey = extr.group(1)
            logging.debug("going to perform regex on item " + apiJsonKey)
            if(apiMonitorEntry[apiJsonKey]):
               logging.debug("found the key, continue on")
               csvMetric = apiMonitorEntry[apiJsonKey]
               extr = re.search('.+?\:(.*)', myValue)
               if(extr): 
                  myRegex = extr.group(1)
                  extr = re.search(myRegex, csvMetric)
                  if(extr):
                     csvLineToWrite = csvLineToWrite + "," + extr.group(1)
                  else:
                     logging.warning("WARNING: no regex match found for regex \"" + myRegex + "\" and string " + csvMetric + ", ignoring. Nagios service: " + apiMonitorEntry['name'] + ", host name: " + apiMonitorEntry['host_name'])
                     logging.debug("apiMonitorEntry is: " + str(apiMonitorEntry))
                     noWrite = 1
               else:
                  logging.error("ERROR: regex to extract regex value from entry " + myValue + " failed")
            else:
               logging.warning("WARNING: In monitor " + apiMonitorEntry['name'] + " definition for host " + apiMonitorEntry['host_name'] + ", json entry value with name " + apiJsonKey + " not found, ignoring.")
               noWrite = 1
               csvLineToWrite = csvLineToWrite + "," + "0"
         else:
            logging.error("ERROR: problem extracting json entry in variable " + myValue)
            
   for metric in csvDict:
      logging.debug("DEBUG: Metric name: " + metric + ", value: " + csvDict[metric])
      pass
   logging.debug("PARSING DONE WRITING LINE: " + csvLineToWrite)
   if(noWrite == 0):
      if(os.path.isfile( mediatorHome + 'nagioscsv/' + filename)):
         thisCsvFile = open( mediatorHome + "nagioscsv/" + filename, "a")
         thisCsvFile.write(csvLineToWrite + "\n")
         thisCsvFile.close()
      else:
         thisCsvFile = open( mediatorHome + "nagioscsv/" + filename, "a")
         thisCsvFile.write(csvheader + "\n")
         thisCsvFile.write(csvLineToWrite + "\n")
         thisCsvFile.close()
 
   
#################
#
#  Initial configuration items
#
##############################

mediatorBinDir = os.path.dirname(os.path.abspath(__file__))
extr = re.search("(.*)bin", mediatorBinDir)
if extr:
   mediatorHome = extr.group(1)
else:
   print "FATAL: unable to find mediator home directory. Is it installed properly? bindir = " + mediatorBinDir
   exit()

if(os.path.isdir(mediatorHome + "log")):
   logging.basicConfig(filename=mediatorHome + 'log/nagios-mediator.log',level=logging.INFO)
else:
   print "FATAL: unable to find log directory." 
   exit()

if(os.path.isdir(mediatorHome + "nagioscsv")):
   csvFileDir = "../nagioscsv/"
else:
   print "FATAL: unable to find nagioscsv directory"
   exit()

if(os.path.isfile(mediatorHome + "/config/nagios_config.txt")):
   pass
else:
   print "FATAL: unable to find mediator config file " + mediatorHome + "/config/nagios_config.txt"
   exit()

configvars = load_properties(mediatorHome + "/config/nagios_config.txt")

logging.debug("Configuration variables are: " + str(configvars))

if 'hostName' in configvars.keys():
   myNagiosHost = configvars['hostName']
   logging.info("Nagios host is " + myNagiosHost)
else:
   print "FATAL: Nagios host name not defined in config file."
   exit()

if 'protocol' in configvars.keys():
   myProtocol = configvars['protocol']
   logging.info("Protocol to use is " + myProtocol)
else:
   print "FATAL: Protocol (http or https) not defined in config file."
   exit()

if 'apikey' in configvars.keys():
   myApiKey = configvars['apikey']
   logging.debug("API key to use: " + myApiKey)
else:
   print "FATAL: API key not defined in config file."
   exit()

if 'port' in configvars.keys():
   myNagiosPort = configvars['port']
   logging.debug("DEBUG: TCP Port to use: " + myNagiosPort)
else:
   print "WARNING: Port number not defined in config file. Defaulting to port 80"
   myNagiosPort = "80"

if 'logginglevel' in configvars.keys():
   if (configvars['logginglevel'] in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']):
      logging.basicConfig(filename=mediatorHome + 'log/nagios-mediator.log',level=configvars['logginglevel'])
      logging.info("Logging is" + configvars['logginglevel'])
   else:
      logging.info("Unknown log level, default to INFO")
      

if 'saveApiResponse' in configvars.keys():
   if (configvars['saveApiResponse'] == '1'):
      logging.info("saving API response under log directory...")
      saveApiResponse = 1
   else:
      saveApiResponse = 0

myTimeStamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())

serviceStatusQuery = myProtocol + "://" + myNagiosHost + ":" + myNagiosPort + "/nagiosxi/api/v1/objects/servicestatus?apikey=" + myApiKey + "&pretty=1"

#hostStatusQuery = myProtocol + "://" + myNagiosHost + ":" + myNagiosPort + "/nagiosxi/api/v1/objects/hoststatus?apikey=" + myApiKey + "&pretty=1"

############################
#
#  Read metric and csv file definitions from configuration file
#
#  Create the following dict object mapping out the configuration file:
#
#  configDict:
#  
#      [<Service Index>]
#         [servicename]=the name of the Nagios monitor record or service
#         [csvheader]=csv header definition for associated file
#         [filename]=filename to write csv data
#         [csvdata]=regex extraction definition (defines which api response attribute e.g. performance_data and the regex used)
#         [csvDict]
#            [csv metric]=operation (value/regex/etc), api attribute, and regex
#            [csvdata]=regex extraction definition (defines which api response attribute e.g. performance_data and the regex used)
#            [csvDict]
#               [csv metric]=operation (value/regex/etc), api attribute, and regex
#               [csv metric]=operation (value/regex/etc), api attribute, and regex
#               [csv metric]=operation (value/regex/etc), api attribute, and regex
#               ...
#               ...
#               ... ( + # of csv columns for this file)
#      [<Service Index>] ( + # of service definitions in configuration file)
#         [<Service Name>]
#            ...
#            ...
#            ...
#
###############################################################

configDict = {}
configLineNumber = 0

with open( mediatorHome + "/config/nagios_metric_file_definitions.txt", "r") as configline:
   for line in configline:
      if not line.startswith("#") and not line.isspace(): 
         logging.debug("splitting line" + line)
         data = shlex.split(line)
         # -- REFACTOR TO INDEXING CONFIG DICT -- nagiosRecord = data[1]
         nagiosRecord = configLineNumber

         # evaluate filename config definition and sub in <timestamp>. If <timestamp> doesn't exist, error out

         if("[timestamp]" in data[0]):
            myFileName = data[0].replace("[timestamp]", myTimeStamp)
            logging.debug("File name for monitor " + data[1] + " is "+ myFileName )
         else:
            print "FATAL: File name for monitor " + data[1] + " is missing timestamp definition."
            exit()

         configDict.setdefault(nagiosRecord, {})['servicename'] = data[1]
         configDict.setdefault(nagiosRecord, {})['filename'] = myFileName
         configDict.setdefault(nagiosRecord, {})['csvdata'] = data[2]

         string_file = StringIO.StringIO(configDict[nagiosRecord]['csvdata'])

         myCsvString = ""
         myCsvDataString = ""
         for row in csv.reader(string_file):
            for element in row:
               extr = re.search('(.+?)\=', str(element))
               if extr:
                  myCsvString = myCsvString + '"' + extr.group(1) + '",'
                  myCsvKey = extr.group(1)
               else:
                  print "parse error on line " 
               logging.debug("extracting csvDataString from " + str(element))
               extr = re.search('.+?\=(.*)', str(element))
               if extr:
                  myCsvDataString = myCsvDataString + '"' + extr.group(1) + '",'
                  myCsvData = extr.group(1)
                  logging.debug("extracted csvDataString = " + myCsvDataString)
               else:
                  print "data definition parse error"
                  exit()
               configDict[nagiosRecord].setdefault('csvDict', {})[myCsvKey]=myCsvData
                
         myCsvString = myCsvString[:-1]               # remove trailing comma
         myCsvDataString = myCsvDataString[:-1]       # remove trailing comma

         configDict.setdefault(nagiosRecord, {})['csvheader']=myCsvString
         configDict.setdefault(nagiosRecord, {})['csvdatadef']=myCsvDataString

         # perform final sanity check on file csv formats to make sure they match other monitors sharing same output file

         for monitor in configDict:
            myHeader = configDict[monitor]['csvheader']
            myFile = configDict[monitor]['filename']
            for othermonitor in configDict:
               if configDict[othermonitor]['filename'] == myFile:
                  if myHeader != configDict[othermonitor]['csvheader']:
                     print "Fatal error: monitor \"" +  monitor + "\" uses same csv output file as \"" + othermonitor + "\" but the output format doesn't match"
                     print "   " + monitor + " csv format in config: " + configDict[monitor]['csvheader']
                     print "   " + othermonitor + " csv format in config: " + configDict[othermonitor]['csvheader']
                     exit()

      configLineNumber = configLineNumber + 1
	
############################
#
#  Begins here...
#
############################		


############################
#
#  Perform servicehosts API query and parse json responses as python object
#
#############################################################################################


print "reading API"

print "query url: " + serviceStatusQuery

serviceStatusContents = urllib2.urlopen(serviceStatusQuery).read()
parsedServiceStatusContents = json.loads(serviceStatusContents)

print "API read completed"


######
#
# uncomment the following to use a file instead of url query
#
# set saveApiResponse = 0 if doing this
#
############################################################

#with open("servicestatus_Nevada.json") as f:
#   parsedServiceStatusContents = json.load(f)
#saveApiResponse=0 

#########
#
# Write the API response to log directory if requested in config file
#
#####################################################################

if(saveApiResponse):
   serviceStatusApiOutput = open( mediatorHome + "/log/serviceStatusApiOutput.json", "w")
   serviceStatusApiOutput.write(serviceStatusContents)
   serviceStatusApiOutput.close

###########
#
#  Iterate through service status response and pull PI metrics of interest, write to files
#
##########################################################################################

recordCount = int(parsedServiceStatusContents['recordcount'])
logging.debug("number of service status records: " + str(recordCount))

recordIndex = 0
while recordIndex < recordCount:

   myHostName = parsedServiceStatusContents['servicestatus'][recordIndex]['host_name']
   myServiceName = parsedServiceStatusContents['servicestatus'][recordIndex]['name']

   logging.debug("Service name: " + myServiceName)
   if(parsedServiceStatusContents['servicestatus'][recordIndex]['performance_data']):
      myPerfData = str(parsedServiceStatusContents['servicestatus'][recordIndex]['performance_data'])
      logging.debug("performance_data=" + myPerfData)
   else:
      pass
      logging.debug("WARNING: no performance data found for Nagios monitor record: " + myServiceName)

   #########################
   # 
   #  Check to see if there are any matches (explicit or substring) for this record in the configuration dictionary
   #
   ################################################################################################################

   
   for serviceIndex in configDict:
      substringMatch = 0
      extr = re.search('match:(.*)', configDict[serviceIndex]['servicename'])
      if extr:
         checkMatch = extr.group(1)
         if(checkMatch in myServiceName):
            logging.debug("Match on substring test for monitor config record: " + myServiceName)
            logging.debug("checkMatch is: " + checkMatch + " and myServiceName is: " + myServiceName)
            substringMatch = 1 
         else:
            checkMatch = "not-substring-match"
         
      if((configDict[serviceIndex]['servicename'] == myServiceName) or (substringMatch == 1)):
         logging.debug("Found matching config entry for " + myServiceName + " and config record " + configDict[serviceIndex]['servicename'])
         logging.debug("writing to filename " + configDict[serviceIndex]['filename'] + ", csvheader " +  configDict[serviceIndex]['csvheader'] + ", data " + configDict[serviceIndex]['csvdatadef'])
         writePiCsvEntry(configDict[serviceIndex]['filename'], configDict[serviceIndex]['csvheader'], configDict[serviceIndex]['csvdatadef'], configDict[serviceIndex]['csvDict'], parsedServiceStatusContents['servicestatus'][recordIndex])
        
            
      else:
         pass
         logging.debug("No config entry for " + myServiceName)
         ##########################
         #
         #  No explicit or "match:" definitions found in the config for this monitor API record
         #
         ###################################################################################

   recordIndex = recordIndex + 1
