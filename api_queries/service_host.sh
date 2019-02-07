#/user/bin/bash

#https://192.168.40.146:10443/nagiosxi/api/v1/objects/servicehosts?apikey=8eSk09rVJlMobKHWasI8kbNhVkWBGcA4JIIKQ9VPNXeeHUrQm9fZj2gfFd6BIFFo&pretty=1

curl -o servicestatus.json http://nagios/nagiosxi/api/v1/objects/servicestatus?apikey=ucMCdER6V46mf5HTbSufj73QJVVCN4HBfpaLk08fkdUChBrLpfZLGjSlu4dh8TRG&pretty=1
