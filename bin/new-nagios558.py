#!/usr/bin/python


##############################
#
# Nagios 5.5.8 mediator for IBM Predictive Insights
#
# 2/4/19 - Jason Cress (jcress@us.ibm.com)
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

def unless(cond, func_if_false, func_if_true):
    if not cond:
        func_if_false()
    else:
        func_if_true()

#################
#
#  Initial configuration items
#
##############################

if(os.path.isdir("../nagioscsv")):
   csvFileDir = "../nagioscsv/"
else:
   csvFileDir = "./"

myTimeStamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
myProtocol = "http"
myNagiosHost = "192.168.2.127"
myNagiosPort = "80"
myApiKey = "ucMCdER6V46mf5HTbSufj73QJVVCN4HBfpaLk08fkdUChBrLpfZLGjSlu4dh8TRG"

serviceStatusQuery = myProtocol + "://" + myNagiosHost + ":" + myNagiosPort + "/nagiosxi/api/v1/objects/servicestatus?apikey=" + myApiKey + "&pretty=1"

#hostStatusQuery = myProtocol + "://" + myNagiosHost + ":" + myNagiosPort + "/nagiosxi/api/v1/objects/hoststatus?apikey=" + myApiKey + "&pretty=1"

############################
#
#  Read metric and csv file definitions from configuration file
#
###############################################################

configDict = {}

with open("../config/nagios_metric_file_definitions.txt", "r") as configline:
   for line in configline:
      if not line.startswith("#") and not line.isspace(): 
         data = shlex.split(line)
         nagiosRecord = data[1]

         # evaluate filename config definition and sub in <timestamp>. If <timestamp> doesn't exist, error out

         if("<timestamp>" in data[0]):
            myFileName = data[0].replace("<timestamp>", myTimeStamp)
            print myFileName
         else:
            print "File name for monitor " + data[1] + " is missing timestamp definition."
            exit()

         configDict.setdefault(nagiosRecord, {})['filename'] = myFileName
         configDict.setdefault(nagiosRecord, {})['csvdata'] = data[2]

         string_file = StringIO.StringIO(configDict[nagiosRecord]['csvdata'])

         myCsvString = ""
         for row in csv.reader(string_file):
            for element in row:
               extr = re.search('(.+?)\=', str(element))
               if extr:
                  myCsvString = myCsvString + '"' + extr.group(1) + '",'
               else:
                  print "parse error on line " 
         myCsvString = myCsvString[:-1]

         configDict.setdefault(nagiosRecord, {})['csvheader']=myCsvString

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

#serviceStatusContents = urllib2.urlopen(serviceStatusQuery).read()
#serviceStatusApiOutput = open("serviceStatusApiOutput.json", "w")
#serviceStatusApiOutput.write(serviceStatusContents)
#serviceStatusApiOutput.close
#parsedServiceStatusContents = json.loads(serviceStatusContents)

print "reading API"
with open("mockedServiceStatus.json") as f:
   parsedServiceStatusContents = json.load(f)


###########
#
#  Iterate through service status response and pull PI metrics of interest, write to files
#
##########################################################################################

recordCount = int(parsedServiceStatusContents['recordcount'])
print("number of service status records: " + str(recordCount))

recordIndex = 0
while recordIndex < recordCount:

   myHostName = parsedServiceStatusContents['servicestatus'][recordIndex]['host_name']
   myServiceName = parsedServiceStatusContents['servicestatus'][recordIndex]['name']

   print myServiceName
   if(parsedServiceStatusContents['servicestatus'][recordIndex]['performance_data']):
      myPerfData = str(parsedServiceStatusContents['servicestatus'][recordIndex]['performance_data'])
      print("performance_data=" + myPerfData)
   else:
      print("WARNING: no performance data attribute found for service name " + myServiceName + " and host name " + myHostName)

   if(myServiceName in configDict):
      # parse csv definition from configuration file to pull out metric values
      print "Found matching config entry for " + myServiceName
      #myConfigItems = split(configDict[myServiceName][csvdata])
      #check to see if the csv file exists for this metric set. If not, create it
      if(os.path.isfile('../nagioscsv/' + configDict[myServiceName]['filename'])):
         thisCsvFile = open("../nagioscsv/" + configDict[myServiceName]['filename'], "a")
         thisCsvFile.write(configDict[myServiceName]['csvdata'] + "\n")
         thisCsvFile.close()
      else:
         thisCsvFile = open("../nagioscsv/" + configDict[myServiceName]['filename'], "w")
         thisCsvFile.write(configDict[myServiceName]['csvheader'] + "\n")
         thisCsvFile.write(configDict[myServiceName]['csvdata'] + "\n")
         thisCsvFile.close()
         
       
   else:
      print "No config entry for " + myServiceName 


   recordIndex = recordIndex + 1
   

