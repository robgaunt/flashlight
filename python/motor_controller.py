__author__ = 'Rob Gaunt (robgaunt@gmail.com)'

import collections
import logging
from twisted.internet import serialport
from twisted.protocols import basic

SIMULATION_DELAY_SECONDS = 0.1


# Improvement to robustness:
# Wait up until 0.15 seconds for controller to ack command
# Otherwise pop queue, send next command, invoke failure handler

class MotorController(basic.LineOnlyReceiver):
  """Communicates with the Roboteq motor controller using a line-based protocol.

  See http://roboteq.com/files_n_images/files/manuals/nxtgen_controllers_userman.pdf for a
  reference to commands supported by the controller.

  Each line is terminated by a carriage return. After sending a command line, the controller will
  echo that command line back, followed by another line representing the command reply.
  """

  delimiter = '\r'

  def __init__(self, reactor, serial_port, num_channels):
    """Initializes a MotorController.

    Args:
      reactor: The twisted.internet.reactor module.
      serial_port: The address of the serial port to connect to. If empty, simulates sending
        and receiving commands instead.
      num_channels: The number of motors connected to the controller.
    """
    self.num_channels = num_channels
    self.serial_port = serial_port
    self.simulate = not serial_port
    self.reactor = reactor
    # List of tuples (command line, callback)
    self.command_queue = collections.deque()
    # The last line seen was the head of the command queue. The next line we see should be the
    # response to that command.
    self.pending_response = False
    if not self.simulate:
      serialport.SerialPort(self, serial_port, reactor, baudrate='115200')

  def sendCommand(self, command, callback=None):
    self.command_queue.append((command, callback))
    if len(self.command_queue) == 1:
      self.sendNextCommand()

  def sendNextCommand(self):
    command = self.command_queue[0][0]
    if not self.simulate:
      logging.debug('Controller %s sending: %s', self.serial_port, command)
      basic.LineOnlyReceiver.sendLine(self, command)
    else:
      self.reactor.callLater(SIMULATION_DELAY_SECONDS, self.lineReceived, command)
      self.reactor.callLater(SIMULATION_DELAY_SECONDS, self.lineReceived, '+')

  def commandComplete(self):
    self.command_queue.popleft()
    if self.command_queue:
      self.sendNextCommand();

  def lineReceived(self, line):
    logging.debug('Controller %s read line: %s', self.serial_port, line)
    if not line:
      return
    if self.pending_response:
      self.pending_response = False
      command, callback = self.command_queue.popleft()
      logging.debug('Controller %s Command %s Response %s', self.serial_port, command, line)
      if callback:
        callback(line)
      if self.command_queue:
        self.sendNextCommand()
    elif self.command_queue and line == self.command_queue[0][0]:
      logging.debug('Controller %s awaiting response for %s',
                    self.serial_port, self.command_queue[0][0])
      self.pending_response = True
    else:
      logging.debug('Controller %s read unexpected line: %s', self.serial_port, line)

  def connectionFailed(self):
    # TODO(robgaunt): error handling
    logging.error('Controller %s: connection failed!', self.serial_port)

  def connectionMade(self):
    logging.info('Controller %s: connection made', self.serial_port)

  # Public API
  def go(self, channel, value):
    """Sends a 'G' (Go To Speed) command to motor.

    Args:
      channel: An integer between 1 and self.num_channels.
      value: A floating point value between -1 and 1.
    """
    self._validate_channel(channel)
    self._validate_value(value)
    command = '!G %d %d' % (channel, value * 1000)
    for i, (existing_command, unused_callback) in enumerate(self.command_queue):
      # go commands don't take callback, so there is no concern about nuking someone else's
      # callback.
      # Note that position i = 0 represents a command which has already been sent and is awaiting
      # a response.
      command_prefix = '!G %d' % channel
      if i and existing_command.startswith(command_prefix):
        # Just replace it.
        logging.debug('Replacing command %s with %s', existing_command, command)
        self.command_queue[i] = (command, None)
        return

    # Didn't find an existing !G command to replace, so send a new one.
    self.sendCommand(command)

  def write_variable(self, variable, value, callback=None):
    """Writes a variable to user flash. This variable will be persisted across restarts."""
    self.sendCommand('^EE %d %d' % (variable, value), callback=callback)
    self.sendCommand('%eesav', callback=callback)

  def read_variable(self, variable, callback):
    """Reads a variable from user flash. Callback will be invoked with the integer value."""
    self.sendCommand('~ee %d' % variable, callback=lambda line: callback(int(line.split('=')[-1])))

  def _validate_value(self, value):
    assert value <= 1.0 and value >= -1.0, 'Invalid value: %d' % value

  def _validate_channel(self, channel):
    assert channel >= 1 and channel <= self.num_channels, 'Invalid channel: %d' % channel
