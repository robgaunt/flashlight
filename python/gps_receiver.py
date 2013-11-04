__author__ = 'Rob Gaunt (robgaunt@gmail.com)'

import logging

from twisted.internet import serialport
from twisted.protocols import basic


class GpsParseException(Exception):
  pass


class GpsData(object):
  def __init__(self, latitude, longitude, altitude):
    self.latitude = latitude
    self.longitude = longitude
    self.altitude = altitude

  def __str__(self):
    return 'GPSData[lat=%0.4f lon=%0.4f alt=%d]' % (self.latitude, self.longitude, self.altitude)


class GpsReceiver(basic.LineOnlyReceiver):
  """Parses GPS data read over a serial port.

  Currently this is known to work with the tracker2 made by Argent Data Systems. The tracker must
  be configured in output mode TEXT on the serial port used for communication.
  """

  def __init__(self, reactor, serial_port, baudrate='4800'):
    serialport.SerialPort(self, serial_port, reactor, baudrate=baudrate)
    self._callbacks = []

  def add_callback(self, callback):
    self._callbacks.append(callback)

  def connectionFailed(self):
    logging.error('GpsReceiver: Connection failed!')

  def connectionMade(self):
    logging.info('GpsReceiver: Connection made')
    
  def lineReceived(self, line):
    gps_data = None
    try:
      if line.startswith('$GPWGT'):
        gps_data = self._parse_gwpgt_line(line)
      # We currently don't parse other types of messages.
    except GpsParseException:
      logging.exception('Invalid GPS line: %s', line)

    if gps_data:
      for callback in self._callbacks:
        callback(gps_data)

  def _latitude_char_to_sign(self, latitude_char):
    if latitude_char == 'N':
      return 1
    elif latitude_char == 'S':
      return -1
    else:
      raise GpsParseException('Invalid latitude character %s' % latitude_char)

  def _longitude_char_to_sign(self, longitude_char):
    if longitude_char == 'E':
      return 1
    elif longitude_char == 'W':
      return -1
    else:
      raise GpsParseException('Invalid longitude character %s' % longitude_char)

  def _parse_gwpgt_coordinate(self, raw_coordinate, sign):
    try:
      raw_coordinate = float(raw_coordinate)
      degrees = int(raw_coordinate / 100)
      minutes = raw_coordinate % 100
      return sign * (degrees + minutes / 60.0)
    except ValueError as e:
      raise GpsParseException('Invalid coordinate: %s %s', raw_coordinate, e)

  def _parse_gwpgt_line(self, line):
    parts = line.split(',')
    if len(parts) < 6:
      raise GpsParseException('Invalid format')

    if parts[1] != 'V':
      logging.debug('GWPGT data is not valid: %s', line)
      return None

    try:
      latitude = self._parse_gwpgt_coordinate(parts[2], self._latitude_char_to_sign(parts[3]))
      longitude = self._parse_gwpgt_coordinate(parts[4], self._longitude_char_to_sign(parts[5]))
      altitude_meters = int(parts[6])
      return GpsData(latitude, longitude, altitude_meters)
    except ValueError as e:
      raise GpsParseException('Expected a number: %s' % e)
