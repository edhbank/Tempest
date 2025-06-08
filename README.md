Tempest Weather Station UDP Packets

I have a Tempest Weather Station in my backyard. It communicates wirelessly with a hub that is connected via wi-fi to my home internet.  The hub pushes the weather data from the station to the tempest website, which then makes the data available via a webpage which is accessible here.  It’s a great system, but what happens if the internet is out or the tempest servers are down for maintenance?  The up-to-the-minute temperature and wind data are not accessible.

Solution:
As it turns out, the hub also broadcasts the weather data in JSON format via UDP packets on the local network.

The python script tempest_web_server.py program listens for the packets and makes the aggregated data available upon request with JSON formatted response. The program then serves /static/index.html web page which renders the JSON in readable format using Anguler.
This is a work in progress. 

