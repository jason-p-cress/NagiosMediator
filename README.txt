Extensible NagiosXI Mediator for IBM Predictive Insights
========================================================

Introduction
============

This mediator provides ingestion of performance metrics from a Nagios XI installation using
the NagiosXI API interface. The performance metrics of interest can be user-defined within
the config/nagios_metric_file_definitions.txt. As such, any custom Nagios plugins, whether
they be provided by Nagios, by the user community, or customer specific, can be utilized
with Predictive Insights.

Installation
============

1. Unzip the package to the desired location (e.g. /opt/IBM/scanalytics/mediators/ExtensibleNagiosMediator)

2. Open the Predictive Insights mediation utility, and open the pamodel file located in the pamodel directory
   of this distribution.

3. Ensure that the correct time zone is configured for your PI installation (VERY IMPORTANT)

4. Ensure that the "File Path" is pointed to the nagioscsv directory where you installed this package
   on the filesystem

5. If you will be deploying to a new topic, ensure that you create the topic (e.g. NAGIOS)
      see: https://www.ibm.com/support/knowledgecenter/en/SSJQQ3_1.3.3/com.ibm.scapi.doc/admin_guide/t_tsaa_adminguide_linktotopic.html

6. New topics default to a 15 minute aggregation interval, which is probably not what you want. Modify the topic
   and change the aggregation interval to something more relevant (e.g. 5-minutes) 
      see: https://www.ibm.com/support/knowledgecenter/en/SSJQQ3_1.3.4/com.ibm.scapi.doc/admin_guide/t_tsaa_adminguide_settingtheaggregationinterval.html

7. Configure the mediator as described in the "Configuring the mediator" section of this README

8. Test the mediator by running the new-nagios.py file located under the bin directory of your mediator installation
   location. Inspect the created CSV files and ensure that there is metric data being generated, as expected for your
   particular Nagios XI deployment. If the expected data is being generated, create a crontab entry (generally
   using the 'scadmin' user, or if you have installed PI as a different user, you would use that user). For example:

   */5 * * * * /opt/IBM/scanalytics/mediators/Nagios558Mediator/bin/new-nagios558.py

   ... will run the mediator on a 5-minute recurring schedule.

9. Deploy the NAGIOS558.pamodel definition to the desired topic using the PI mediation tool. The default model can be
   found in the 'pamodel' directory of the location where you unzipped the mediator pack.

10. Start the extractor instance using the 'admin.sh' utility under $PI_HOME/bin/. For example:

    >>run_extractor_instance -m=EXTRACT -s=20190201-0000 -t=NAGIOS

   ... will start extracting data beginning on Feb 1 2019 at midnight, and continue to extrace data until stopped.


Configuring the mediator
========================

The 'config' directory contains the 'nagios_config.txt' where you define the connection details and behavior. 

	protocol: http or https, the protocol used to access the NagiosXI API
	hostName: The hostname or IP address of the NagiosXI server
	port: The port number of the NagiosXI API
	apikey: This is the key used to access the API, which can be obtained from the user configuration
                of the NagiosXI user used to request the data
	logginglevel: set to INFO for minimal logging. INFO, WARNING, ERROR, DEBUG
	saveApiResponse: If set to 1, will write out the raw API response received from Nagios to the log directory
	unWebify: for future

Customization of the nagios_metric_file_definitions.txt file 
============================================================

The 'config' directory contains the 'nagois_metric_file_definitions.txt', which defines the CSV files, the monitor
records in the Nagios API response, the structure of the CSV files, and how to define what data goes into the CSV
files. It is laid out in this configuration file as such:

PI Filename		Monitor Record			CSV Definition
The csv filename	The NagiosXI monitor name	The structure of the csv and data definitions

PI Filename:
	For this version of the mediator, a predictive insights model file is included that contains the following
        Metric Groups, and their associated CSV files:

	cpuUsage		timestamp,host name,cpu usage	
        diskUsage		timestamp,host name,disk name,disk used,disk free
	memoryData		timestamp,host name,memory total,memory used
	pingData		timestamp,host name,ping_rta value,ping_pl value
	swapUsage		timestamp,host name,swap data
	totalProcess		timestamp,host name,total processes
	HTTPData		timestamp,host name,http data
	cpuLoad			timestamp,host name,Load5
	cpuStats		timestamp,host name,user,system,iowait,idle
	users			timestamp,host name,users
	networkUtilization	timestamp,host name,interface,inbound utilization,outbound utilization

Different Nagios monitors may provide data for the above model in different ways. For example, if you are using
the NCPA agent for monitoring a Windows server, CPU utilization information is provided by a monitor entitled 
"CPU Usage", while if you were also using the NRPE monitoring agent for Linux, the information is provided by a 
monitor entitled "CPU Stats". Additionally, different monitoring methods may output their performance data in 
different formats. For example, while both the Windows NRPE monitoring agent and the Linux SNMP monitoring agent use
a monitor named "CPU Usage", the output of the performance data (found in the "performance_data" JSON object of
the monitor API responce) is formatted completely differently. 

This configuration file allows you to define:
	1. The Monitor Record you want to pull performance data from (which is servicestatus->name in the API response)
	2. The CSV file you want to write the performance data to (generally matching one of the above files)
	3. The structure of the CSV and the method of extraction of data (e.g. from a JSON attribute, a regular
	   expression extraction of data from a JSON attribute, or a literal value. Examples:

           var[timestamp]  --  inserts the current timestamp into this column of the CSV file
           value[host_name]  --  inserts the value of the attribute 'host_name' for this monitor's JSON response
           regex[performance_data:"load5=(.+?)\;"]  --  extracts text from the attribute 'performance_data' for this
                                                        for this monitor's JSON response
           literal[0]  --  inserts the literal value of 0 into this column of the CSV file

If you have defined multiple metric definitions that use the same CSV file, and the CSV header information / columns
do not match between

A note about Network Utilization in Nagios - In general, default monitors for servers do not include network 
utilization data. For network devices (router/switch), this information is usually included by default. Also, the
VMware default monitors include aggregate network utilization. The example metric definition file included in this 
distribution includes entries for both network device utilization (using the Network Switch / Router wizard provided
in Nagios) and for VMWare network utilization (enabled by default using the Nagios VMWare wizard).

... more documentation to follow

 
   


