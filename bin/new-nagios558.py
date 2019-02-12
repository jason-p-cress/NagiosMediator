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
         print "unable to determine operand in config for line"      # should probably be determined in initial config file processing section...
         exit(0) 
      extr = re.search('^.+?\[(.*)\]', myValueDef)
      if(extr):
         myValue = extr.group(1)
      else:
         print "malformed config line"     # should probably be determined in initial config file processing section...
         exit(0)
      if(myOp == 'var'):
         if(myValue == 'timestamp'):
            csvLineToWrite = csvLineToWrite + myTimeStamp
         else:
            print "Unknown internal variable " + myValue + " in config, line: " + csvdatadef      # should probably be determined in initial config file processing section...
            exit(0) 
      elif(myOp == 'literal'):
         csvLineToWrite = csvLineToWrite + "," +  myValue
      elif(myOp == 'value'):
         csvLineToWrite = csvLineToWrite + "," + apiMonitorEntry[myValue]
      elif(myOp == 'regex'):
         extr = re.search('(.+?)\:', myValue)
         if(extr):
            apiJsonKey = extr.group(1)
            if debug: print "going to perform regex on item " + apiJsonKey
            if(apiMonitorEntry[apiJsonKey]):
               #print "found the key, continue on"
               csvMetric = apiMonitorEntry[apiJsonKey]
               extr = re.search('.+?\:(.*)', myValue)
               if(extr): 
                  myRegex = extr.group(1)
                  extr = re.search(myRegex, csvMetric)
                  if(extr):
                     csvLineToWrite = csvLineToWrite + "," + extr.group(1)
                  else:
                     print "WARNING: no regex match found for regex \"" + myRegex + "\" and string " + csvMetric + ", ignoring. Nagios service: " + apiMonitorEntry['name'] + ", host name: " + apiMonitorEntry['host_name']
                     if debug: print "apiMonitorEntry is: " + str(apiMonitorEntry)
                     noWrite = 1
               else:
                  print "regex to extract regex value from entry " + myValue + " failed"
            else:
               print "Warning: In monitor " + apiMonitorEntry['name'] + " definition for host " + apiMonitorEntry['host_name'] + ", json entry value with name " + apiJsonKey + " not found, ignoring."
               noWrite = 1
               csvLineToWrite = csvLineToWrite + "," + "0"
         else:
            print "problem extracting json entry in variable " + myValue
            
   for metric in csvDict:
      #print "Metric name: " + metric + ", value: " + csvDict[metric]
      pass
   if debug: print "PARSING DONE WRITING LINE: " + csvLineToWrite
   if(noWrite == 0):
      if(os.path.isfile( mediatorHome + 'nagioscsv/' + filename)):
         thisCsvFile = open( mediatorHome + "nagioscsv/" + filename, "a")
         thisCsvFile.write(csvLineToWrite + "\n")
         thisCsvFile.close()
      else:
         thisCsvFile = open( mediatorHome + "nagioscsv/" + filename, "w")
         thisCsvFile.write(csvheader + "\n")
         thisCsvFile.write(csvLineToWrite + "\n")
         thisCsvFile.close()
 
   
#################
#
#  Initial configuration items
#
##############################

mediatorBinDir = os.getcwd()
extr = re.search("(.*)bin", mediatorBinDir)
if extr:
   mediatorHome = extr.group(1)
else:
   print "unable to find mediator home directory. Is it installed properly?"
   exit()

if(os.path.isdir(mediatorHome + "nagioscsv")):
   csvFileDir = "../nagioscsv/"
else:
   print "unable to find nagioscsv directory"
   exit()

if(os.path.isfile(mediatorHome + "/config/nagios_config.txt")):
   pass
else:
   print "unable to find mediator config file " + mediatorHome + "/config/nagios_config.txt"
   exit()

configvars = load_properties(mediatorHome + "/config/nagios_config.txt")

print configvars
print configvars['hostName']

if 'hostName' in configvars.keys():
   myNagiosHost = configvars['hostName']
   print "Nagios host is " + myNagiosHost
else:
   print "Nagios host name not defined in config file."
   exit()

if 'protocol' in configvars.keys():
   myProtocol = configvars['protocol']
   print "Protocol to use is " + myProtocol
else:
   print "Protocol (http or https) not defined in config file."
   exit()

if 'apikey' in configvars.keys():
   myApiKey = configvars['apikey']
   print "API key to use: " + myApiKey
else:
   print "API key not defined in config file."
   exit()

if 'port' in configvars.keys():
   myNagiosPort = configvars['port']
   print "TCP Port to use: " + myNagiosPort
else:
   print "Port number not defined in config file. Defaulting to port 80"
   myNagiosPort = "80"

if 'debug' in configvars.keys():
   if (configvars['debug'] == '1'):
      print "Debug enabled..."
      debug = 1
   else:
      debug = 0

if 'saveApiResponse' in configvars.keys():
   if (configvars['saveApiResponse'] == '1'):
      print "saving API response under log directory..."
      saveApiResponse = 1
   else:
      saveApiResponse = 0

myTimeStamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
#myProtocol = "http"
#myNagiosHost = "192.168.2.127"
#myNagiosPort = "80"
#myApiKey = "ucMCdER6V46mf5HTbSufj73QJVVCN4HBfpaLk08fkdUChBrLpfZLGjSlu4dh8TRG"

serviceStatusQuery = myProtocol + "://" + myNagiosHost + ":" + myNagiosPort + "/nagiosxi/api/v1/objects/servicestatus?apikey=" + myApiKey + "&pretty=1"

#hostStatusQuery = myProtocol + "://" + myNagiosHost + ":" + myNagiosPort + "/nagiosxi/api/v1/objects/hoststatus?apikey=" + myApiKey + "&pretty=1"

############################
#
#  Read metric and csv file definitions from configuration file
#
#  Create the following dict object mapping out the configuration file:
#
#  configDict
#            [<Service Name>]
#	                   [csvheader]=csv header definition for associated file
#                          [filename]=filename to write csv data
#                          [csvdata]=regex extraction definition (defines which api response attribute e.g. performance_data and the regex used)
#                          [csvDict]
#                                   [csv metric]=operation (value/regex/etc), api attribute, and regex
#                          [csvdata]=regex extraction definition (defines which api response attribute e.g. performance_data and the regex used)
#                          [csvDict]
#                                   [csv metric]=operation (value/regex/etc), api attribute, and regex
#                                   [csv metric]=operation (value/regex/etc), api attribute, and regex
#                                   [csv metric]=operation (value/regex/etc), api attribute, and regex
#                                   ...
#                                   ...
#                                   ...
#            [<Service Name>]
#                           ...
#                           ...
#                           ...
#
###############################################################

configDict = {}
with open( mediatorHome + "/config/nagios_metric_file_definitions.txt", "r") as configline:
   for line in configline:
      if not line.startswith("#") and not line.isspace(): 
         #if debug: print("splitting line" + line)
         data = shlex.split(line)
         nagiosRecord = data[1]

         # evaluate filename config definition and sub in <timestamp>. If <timestamp> doesn't exist, error out

         if("[timestamp]" in data[0]):
            myFileName = data[0].replace("[timestamp]", myTimeStamp)
            #if debug: print myFileName
         else:
            print "File name for monitor " + data[1] + " is missing timestamp definition."
            exit()

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
               #if debug: print "extracting csvDataString from " + str(element)
               extr = re.search('.+?\=(.*)', str(element))
               if extr:
                  myCsvDataString = myCsvDataString + '"' + extr.group(1) + '",'
                  myCsvData = extr.group(1)
                  #if debug: print "extracted csvDataString = " + myCsvDataString
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
if debug: print("number of service status records: " + str(recordCount))

recordIndex = 0
while recordIndex < recordCount:

   myHostName = parsedServiceStatusContents['servicestatus'][recordIndex]['host_name']
   myServiceName = parsedServiceStatusContents['servicestatus'][recordIndex]['name']

   if debug: print myServiceName
   if(parsedServiceStatusContents['servicestatus'][recordIndex]['performance_data']):
      myPerfData = str(parsedServiceStatusContents['servicestatus'][recordIndex]['performance_data'])
      #if debug: print("performance_data=" + myPerfData)
   else:
      pass

   #########################
   # 
   #  Check to see if there are any explicit matches for this record in the configuration dictionary
   #
   #################################################################################################

   if(myServiceName in configDict):
      # parse csv definition from configuration file to pull out metric values
      if debug: print "Found matching config entry for " + myServiceName
      #myConfigItems = split(configDict[myServiceName][csvdata])
      #check to see if the csv file exists for this metric set. If not, create it
      #print "writing to filename " + configDict[myServiceName]['filename'] + ", csvheader " +  configDict[myServiceName]['csvheader'] + ", data " + configDict[myServiceName]['csvdatadef']
      writePiCsvEntry(configDict[myServiceName]['filename'], configDict[myServiceName]['csvheader'], configDict[myServiceName]['csvdatadef'], configDict[myServiceName]['csvDict'], parsedServiceStatusContents['servicestatus'][recordIndex])
        
   else:

      ###########################
      #
      #  No explicit matches in the configuration dictionary for this monitor...
      #  check to see if this monitor matches any "match" monitor definitions in the config
      #  There is probably a better way to do this, but unless the customer config file is
      #  ginormous it shouldn't be too much of an impact on performance
      #
      #####################################################################################

      for recordName in configDict:
         if("match:" in recordName):
            if debug: print "found config record with match definition: " + recordName
            extr = re.search('match:(.*)', recordName)
            if extr:
                checkMatch = extr.group(1) 
                if debug: print "checkMatch is: " + checkMatch + " and myServiceName is: " + myServiceName
                if(checkMatch in myServiceName):
                   monitorRecord = "match:" + checkMatch
                   writePiCsvEntry(configDict[monitorRecord]['filename'], configDict[monitorRecord]['csvheader'], configDict[monitorRecord]['csvdatadef'], configDict[monitorRecord]['csvDict'], parsedServiceStatusContents['servicestatus'][recordIndex])
                   if debug: print "Found a substring match for service"
                   if debug: print "===================================="
            
         else:
            pass
            #if debug: print "No config entry for " + myServiceName
            ##########################
            #
            #  No explicit or "match:" definitions found in the config for this monitor API record
            #
            ###################################################################################

   recordIndex = recordIndex + 1

