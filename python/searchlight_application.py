__author__ = 'Rob Gaunt (robgaunt@gmail.com)'

import logging
from txosc import async
from txosc import dispatch

SEARCHLIGHT_NAME_ALL = "all"


class SearchlightApplication(object):
  """Serves as the wiring between the OSC server and motor controller.

  This registers OSC addresses with a txosc Receiver, and translates OSC commands to motor
  controller commands.

  All OSC addresses are of the form /<searchlight name>/<command>. Each searchlight registers for
  addresses using both its name and the name "all". This makes it possible to send OSC commands
  either to individual searchlights, or to all searchlights at the same time.
  """

  def __init__(self, reactor, motorController, name, address, listenPort):
    assert name != SEARCHLIGHT_NAME_ALL, 'Name %s is reserved' % SEARCHLIGHT_NAME_ALL
    self.name = name
    self.motorController = motorController
    self.oscReceiver = dispatch.Receiver()
    self.addOscCallback("go1", self.motor_1_go)
    self.addOscCallback("go2", self.motor_2_go)
    # TouchOSC sends /accxyz commands hundreds of times per second with the current phone
    # accelerometer readings. This is interesting, but currently causes a LOT of logspam, so
    # blackhole them.
    self.oscReceiver.addCallback("/accxyz", self.ignoreOscCommand)
    reactor.listenMulticast(
        listenPort,
        async.MulticastDatagramServerProtocol(self.oscReceiver, address),
        listenMultiple=True)

  def addOscCallback(self, callbackName, callback):
    self.oscReceiver.addCallback("/%s/%s" % (self.name, callbackName), callback)
    self.oscReceiver.addCallback("/%s/%s" % (SEARCHLIGHT_NAME_ALL, callbackName), callback)

  def unwrap_osc(func):
    """Decorator for all OSC handlers."""
    def handler(self, message, address):
      logging.debug('Searchlight %s received %s from %s', self.name, message, address)
      func(self, *message.getValues())
    return handler

  @unwrap_osc
  def motor_1_go(self, value):
    self.motorController.go(1, value)

  @unwrap_osc
  def motor_2_go(self, value):
    if 2 <= self.motorController.numChannels:
      self.motorController.go(2, value)
    else:
      logging.info('Searchlight %s ignoring command to motor channel 2', self.name)

  def ignoreOscCommand(self, message, address):
    pass
