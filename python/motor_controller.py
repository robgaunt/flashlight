__author__ = 'Rob Gaunt (robgaunt@gmail.com)'

import logging
from twisted.internet import serialport
from twisted.protocols import basic

SIMULATION_DELAY_SECONDS = 0.5


class MotorController(basic.LineOnlyReceiver):
  """Communicates with the Roboteq motor controller using a line-based protocol.

  See http://roboteq.com/files_n_images/files/manuals/nxtgen_controllers_userman.pdf for a
  reference to commands supported by the controller.

  Each line is terminated by a carriage return. After sending a command line, the controller will
  echo that command line back, followed by another line representing the command reply.
  """

  delimiter = '\r'

  def __init__(self, reactor, serialPortAddress, numChannels, simulateMode=False):
    """Initializes a MotorController.

    Args:
      reactor: The twisted.internet.reactor module.
      serialPortAddress: The address of the serial port to connect to.
      numChannels: The number of motors connected to the controller.
      simulateMode: If True, does not actually connect to the serial port, and simply simulates
        sending commands.
    """
    self.numChannels = numChannels
    self.serialPortAddress = serialPortAddress
    self.simulateMode = simulateMode
    self.reactor = reactor
    if not self.simulateMode:
      serialport.SerialPort(self, serialPortAddress, reactor, baudrate='115200')

  def sendLine(self, line):
    logging.debug('Controller %s sending: %s', self.serialPortAddress, line)
    if self.simulateMode:
      self.reactor.callLater(SIMULATION_DELAY_SECONDS, self.lineReceived, line)
      self.reactor.callLater(SIMULATION_DELAY_SECONDS, self.lineReceived, '+')
    else:
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
      channel: An integer between 1 and self.numChannels.
      value: A floating point value between -1 and 1.
    """
    self._validateChannel(channel)
    self._validateValue(value)
    # TODO(robgaunt): We want to enforce some rate-limiting here. TouchOSC can send commands much
    # faster than the controller responds. A good solution would be to make all commands use
    # absolute positioning (not relative) and queue up the most recent command received.
    # Effectively this would drop all intermediate positoning values and make the motor always
    # move to the most recent position requested.
    self.sendLine('!G %d %d' % (channel, value * 1000))

  def goToPosition(self, channel, value):
    """Sends a Go To Absolute Position command to the motor.

    Args:
      channel: An integer between 1 and self.numChannels.
      value: A floating point value between -1 and 1. The controller supports about 22 bits of
        precision in position.
    """
    self._validateChannel(channel)
    self._validateValue(value)
    # TODO(robgaunt): We may actually want to use PR commands instead of P commands and translate
    # all absolute movement commands into relative commands.
    # The position counter value is permitted to range between -2000000 and 2000000.
    self.sendLine('!P %d %d' % (channel, value * 2000000))

  def _validateValue(self, value):
    assert value <= 1.0 and value >= -1.0, 'Invalid value: %d' % value

  def _validateChannel(self, channel):
    assert channel >= 1 and channel <= self.numChannels, 'Invalid channel: %d' % channel
