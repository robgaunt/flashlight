__author__ = 'Rob Gaunt (robgaunt@gmail.com)'

import logging
from txosc import async
from txosc import dispatch


class SearchlightApplication(object):
  """Application which receives commands from OSC multicast."""

  def __init__(self, reactor, motorController, name, address, listenPort):
    self.name = name
    self.motorController = motorController
    self.oscReceiver = dispatch.Receiver()
    self.addOscCallback("go1", self.motor_1_go)
    self.addOscCallback("go2", self.motor_2_go)
    reactor.listenMulticast(
        listenPort,
        async.MulticastDatagramServerProtocol(self.oscReceiver, address),
        listenMultiple=True)

  def addOscCallback(self, callbackName, callback):
    self.oscReceiver.addCallback("/%s/%s" % (self.name, callbackName), callback)

  def unwrap_osc(func):
    """Decorator for all OSC handlers."""
    def handler(self, message, address):
      logging.debug('Searchlight %s received %s from %s', self.name, message, address)
      func(self, *message.getValues())
    return handler

  @unwrap_osc
  def motor_1_go(self, value):
    self.motorController.go(1, value * 1000)

  @unwrap_osc
  def motor_2_go(self, value):
    if 2 <= self.motorController.numChannels:
      self.motorController.go(2, value * 1000)
    else:
      logging.info('Searchlight %s ignoring command to motor channel 2', self.name)
