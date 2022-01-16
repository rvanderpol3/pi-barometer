# pi-barometer

Reads the barometric pressure and adjust for altitude.  You'll need a Raspberry Pi with a soldered BMP085 for this project to work.  `pressure_serv.py` will return the pressure in json in response to an HTTP `GET` on port 8080.
