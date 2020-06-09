# This script detects for the presence of either a BME680 sensor on the I2C bus or a Sense HAT
# The BME680 includes sensors for temperature, humidity, pressure and gas content
# The Sense HAT does not have a gas sensor, and so air quality is approximated using temperature and humidity only.

import sys
import os
import json

import smbus

from bme680 import BME680
from enviroplushat import ENVIROPLUS
from w1therm import W1THERM
from sma import SMA
from sense_hat_air_quality import get_readings
from hts221 import HTS221

from http.server import HTTPServer, BaseHTTPRequestHandler


class balenaSense():
    readfrom = 'unset'
    bus = smbus.SMBus(1)

    def __init__(self):
        # First, check for enviro plus hat (since it also has BME on 0x76)
        try:
            self.bus.write_byte(0x23, 0)  # test if we can connect to ADS1015
            self.readfrom = 'enviroplus'
            self.sensor = ENVIROPLUS()
            print('Found Enviro+ Hat')
        except IOError:
            print('Enviro Plus hat not found')
        except ImportError:
            print('Import enviroplushat module failed')

        # Next, check to see if there is a BME680 on the I2C bus
        if self.readfrom == 'unset':
            try:
                self.bus.write_byte(0x76, 0)
                print('BME680 found on 0x76')
                self.sensor = BME680(self.readfrom)
                self.readfrom = 'bme680primary'
            except IOError:
                print('BME680 not found on 0x76, trying 0x77')
                try:
                    self.bus.write_byte(0x77, 0)
                    print('BME680 found on 0x77')
                    self.sensor = BME680(self.readfrom)
                    self.readfrom = 'bme680secondary'
                except IOError:
                    print('BME680 not found on 0x77')
            except ImportError:
                print('Import bme680 module failed')

        # If no BME680, is there a Sense HAT?
        if self.readfrom == 'unset':
            try:
                self.bus.write_byte(0x5F, 0)
                self.readfrom = 'sense-hat'
                print('Using Sense HAT for readings (no gas measurements)')

                # Import the sense hat methods
                self.sense_hat_reading = lambda: get_readings(HTS221())
            except:
                print('Sense HAT not found')

        # Next, check if there is a 1-wire temperature sensor (e.g. DS18B20)
        if self.readfrom == 'unset':
            try:
                self.sensor = W1THERM(os.getenv('BALENASENSE_1WIRE_SENSOR_ID'))
                self.readfrom = '1-wire'
                print('Using 1-wire for readings (temperature only)')
            except:
                print('1-wire sensor not found')

        if self.readfrom == 'unset':
            try:
                self.sensor = SMA(ip=os.getenv("BALENASENSE_SOLAR_IP"),
                                  user=os.getenv("BALENASENSE_SOLAR_USER"),
                                  password=os.getenv("BALENASENSE_SOLAR_PASSWORD"),
                                  sensor_id=os.getenv('BALENASENSE_SOLAR_SENSOR'))
                self.readfrom = 'sma-solar'
                print('Using SMA solar connection at %s' % self.sensor.ip)
            except:
                print('SMA solar connection not found')

        # If this is still unset, no sensors were found; quit!
        if self.readfrom == 'unset':
            print('No suitable sensors found! Exiting.')
            sys.exit()

    def sample(self):
        if self.readfrom == 'sense-hat':
            return self.apply_offsets(self.sense_hat_reading())
        else:
            return self.apply_offsets(self.sensor.get_readings(self.sensor))

    def apply_offsets(self, measurements):
        # Apply any offsets to the measurements before storing them in the database
        if os.environ.get('BALENASENSE_TEMP_OFFSET'):
            measurements[0]['fields']['temperature'] = measurements[0]['fields']['temperature'] + float(
                os.environ['BALENASENSE_TEMP_OFFSET'])

        if os.environ.get('BALENASENSE_HUM_OFFSET'):
            measurements[0]['fields']['humidity'] = measurements[0]['fields']['humidity'] + float(
                os.environ['BALENASENSE_HUM_OFFSET'])

        if os.environ.get('BALENASENSE_ALTITUDE'):
            # if there's an altitude set (in meters), then apply a barometric pressure offset
            altitude = float(os.environ['BALENASENSE_ALTITUDE'])
            measurements[0]['fields']['pressure'] = measurements[0]['fields']['pressure'] * (1 - (
                        (0.0065 * altitude) / (
                            measurements[0]['fields']['temperature'] + (0.0065 * altitude) + 273.15))) ** -5.257

        return measurements


class balenaSenseHTTP(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        measurements = balenasense.sample()
        if measurements:
            self.wfile.write(json.dumps(measurements[0]['fields']).encode('UTF-8'))
        else:
            print("No active sensors... waiting until next measurement.")

    def do_HEAD(self):
        self._set_headers()


# Start the server to answer requests for readings
balenasense = balenaSense()

while True:
    server_address = ('', 80)
    httpd = HTTPServer(server_address, balenaSenseHTTP)
    print('Sensor HTTP server running')
    httpd.serve_forever()
