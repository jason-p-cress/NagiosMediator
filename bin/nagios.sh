#!/bin/sh
# 
# JAVA_HOME needs to be declared here. Jobs running from CRON do not have the user's profile variables in them
#
#export JAVA_HOME=/home/scadmin/java/jdk1.8.0_131/bin/java
export JAVA_HOME=/home/scadmin/InfoSphereStreams/4.2.0.3/java/bin/java
FULLPATH=$(cd $(dirname $0) && pwd )
cd - > /dev/null 2>&1
export PATH=$JAVA_HOME/bin:$PATH
for line in $(grep . $FULLPATH/../config/nagios_config.txt); do declare $line; done
#

#java -Dprotocol="$protocol" -DhostName="$hostName" -Dport="$port" -Dapikey="$apikey" -Dfilepath="$filepath" -jar $jarpath/NagiosMediationUtility.jar

./Nagios558.py

