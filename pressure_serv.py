#!/usr/bin/python
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Can enable debug output by uncommenting:
#import logging
#logging.basicConfig(level=logging.DEBUG)

import json
import requests
import Adafruit_BMP.BMP085 as BMP085
import BaseHTTPServer
import threading
from threading import Lock
import time

# Default constructor will pick a default I2C bus.
#
# For the Raspberry Pi this means you should hook up to the only exposed I2C bus
# from the main GPIO header and the library will figure out the bus number based
# on the Pi's revision.
#
# For the Beaglebone Black the library will assume bus 1 by default, which is
# exposed with SCL = P9_19 and SDA = P9_20.
sensor = BMP085.BMP085()

# Optionally you can override the bus number:
#sensor = BMP085.BMP085(busnum=2)

# You can also optionally change the BMP085 mode to one of BMP085_ULTRALOWPOWER,
# BMP085_STANDARD, BMP085_HIGHRES, or BMP085_ULTRAHIGHRES.  See the BMP085
# datasheet for more details on the meanings of each mode (accuracy and power
# consumption are primarily the differences).  The default mode is STANDARD.
#sensor = BMP085.BMP085(mode=BMP085.BMP085_ULTRAHIGHRES)

print('Temp = {0:0.2f} *C'.format(sensor.read_temperature()))
print('Pressure = {0:0.2f} Pa'.format(sensor.read_pressure()))
print('Altitude = {0:0.2f} m'.format(sensor.read_altitude()))
print('Sealevel Pressure = {0:0.2f} Pa'.format(sensor.read_sealevel_pressure()))

lock = threading.Lock()
values = {
    
}

def pollWindDirection():
    while True:
        try:
            print("Querying Open WeatherMap")
            # my weather station doesnt have a wind vane for direction so im using local wind vane for direction.  
            response = requests.get("https://api.openweathermap.org/data/2.5/onecall?latxx.xxxxx&lon=-xx.xxxxx&exclude=minutely,hourly,daily,alerts&appid=xxxx")
            
            if response.status_code != 200:
                print("Got ["+str(response.status)+"] from Open WeatherMap")
                continue

            data = response.json()            
            
            if "current" in data:
                current = data["current"]
                lock.acquire()
                if "wind_deg" in current:                    
                    values["winddir"] = current["wind_deg"]
                if "uvi" in current:                    
                    values["UV"] = current["uvi"]
                lock.release()
                
        except Exception:
            print("Error Open WeatherMap")
            pass

        time.sleep(300)

def pollPressure():
    pressureHistoryList = []
    while True:
        try:
            # Update adjustment factor based on your height http://www.csgnetwork.com/barcorrecthcalc.html
            adjustedHpa = sensor.read_pressure() * 1.019303644
            inchesOfMercury = adjustedHpa * 0.00029530
            pressureHistoryList.insert(0,round(inchesOfMercury,2))
            lock.acquire()
            values["baromin"] = max(pressureHistoryList, key=pressureHistoryList.count)
            lock.release()
            if len(pressureHistoryList) > 30:
                pressureHistoryList = pressureHistoryList[0:29]            
            time.sleep(2)
        except Exception:
            print("Error reading barometric pressure")
            pass
    

def getCurrentValues():
    lock.acquire()
    _values = values.copy()
    print("returning " + str(_values))
    lock.release()
    return json.dumps(_values)

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(s):
        s.send_response(200)
        s.send_header("Content-Type", "application/json")
        s.end_headers()
        s.wfile.write(getCurrentValues())
        
server_class = BaseHTTPServer.HTTPServer
httpd = server_class(("0.0.0.0", 8080), MyHandler)
try:
    pressurePollThread = threading.Thread(target=pollPressure)
    pressurePollThread.start()
    # windDirPollThread = threading.Thread(target=pollWindDirection)
    # windDirPollThread.start()
    httpd.serve_forever()
except KeyboardInterrupt:
    pass
httpd.server_close()
