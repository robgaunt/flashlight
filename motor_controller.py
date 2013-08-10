__author__ = 'Rob Gaunt (robgaunt@gmail.com)'

import logging
from twisted.internet import serialport
from twisted.protocols import basic


class MotorController(basic.LineOnlyReceiver):
  """Communicates with the Roboteq motor controller using a line-based protocol."""

  delimiter = '\r'

  def __init__(self, reactor, serialPortAddress, numChannels):
    self.numChannels = numChannels
    self.serialPortAddress = serialPortAddress
    serialport.SerialPort(self, serialPortAddress, reactor, baudrate='115200')

  def sendLine(self, line):
    logging.debug('Controller %s sending: %s', self.serialPortAddress, line)
    basic.LineOnlyReceiver.sendLine(self, line)

  def lineReceived(self, line):
    logging.debug('Controller %s received: %s', self.serialPortAddress, line)

  def connectionFailed(self):
    # TODO(robgaunt): error handling
    logging.error('Controller %s: connection failed!', self.serialPortAddress)

  def connectionMade(self):
    logging.info('Controller %s: connection made', self.serialPortAddress)

  # Public API
  def go(self, channel, value):
    """Sends a 'G' (Go To Speed) command to motor.

    Args:
      channel: An integer between 1 and self._numChannels.
      value: An integer between -1000 and 1000.
    """
    assert value <= 1000 and value >= -1000, 'Invalid value: %d' % value
    assert channel >= 1 and channel <= self.numChannels, 'Invalid channel: %d' % channel
    # TODO(robgaunt): We want to enforce some rate-limiting here. TouchOSC can send commands much
    # faster than the controller responds. A good solution would be to make all commands use
    # absolute positioning (not relative) and queue up the most recent command received.
    # Effectively this would drop all intermediate positoning values and make the motor always
    # move to the most recent position requested.
    self.sendLine('!G %d %d\r' % (channel, value))
