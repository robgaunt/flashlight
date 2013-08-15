__author__ = 'Rob Gaunt (robgaunt@gmail.com)'

import logging

SEARCHLIGHT_NAME_ALL = "all"


class Searchlight(object):
  """Serves as the wiring between the OSC server and motor controller.

  This registers OSC addresses with a txosc Receiver, and translates OSC commands to motor
  controller commands.

  All OSC addresses are of the form /<searchlight name>/<command>. Each searchlight registers for
  addresses using both its name and the name "all". This makes it possible to send OSC commands
  either to individual searchlights, or to all searchlights at the same time.
  """

  def __init__(self, motor_controller, osc_receiver, name):
    """Initializes a Searchlight.

    Args:
      motor_controller: An instance of motor_controller.MotorController.
      osc_receiver: An instance of txosc.dispatch.Receiver.
      name: The name of this searchlight. Used to identify which OSC endpoints it responds to.
    """
    assert name != SEARCHLIGHT_NAME_ALL, 'Name %s is reserved' % SEARCHLIGHT_NAME_ALL
    self.name = name
    self.motor_controller = motor_controller
    self.osc_receiver = osc_receiver
    self.add_osc_callback("go1", self.motor_one_go)
    self.add_osc_callback("go2", self.motor_two_go)
    # TouchOSC sends /accxyz commands hundreds of times per second with the current phone
    # accelerometer readings. This is interesting, but currently causes a LOT of logspam, so
    # blackhole them.
    self.osc_receiver.addCallback("/accxyz", self.ignore_osc_command)

  def add_osc_callback(self, callback_name, callback):
    self.osc_receiver.addCallback("/%s/%s" % (self.name, callback_name), callback)
    self.osc_receiver.addCallback("/%s/%s" % (SEARCHLIGHT_NAME_ALL, callback_name), callback)

  def unwrap_osc(func):
    """Decorator for all OSC handlers."""
    def handler(self, message, address):
      logging.debug('Searchlight %s received %s from %s', self.name, message, address)
      func(self, *message.getValues())
    return handler

  @unwrap_osc
  def motor_one_go(self, value):
    self.motor_controller.go(1, value)

  @unwrap_osc
  def motor_two_go(self, value):
    if 2 <= self.motor_controller.num_channels:
      self.motor_controller.go(2, value)
    else:
      logging.info('Searchlight %s ignoring command to motor channel 2', self.name)

  def ignore_osc_command(self, message, address):
    pass
