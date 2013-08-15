#!/usr/bin/python

"""Executable script which runs an OSC server to control a single searchlight.

Example usage:
  ./searchlight_main.py --config_file ../configs/simple.yaml
"""

__author__ = 'Rob Gaunt (robgaunt@gmail.com)'

import argparse
import logging
import pprint
from txosc import async
from txosc import dispatch
from twisted.internet import reactor
from twisted.python import log
import yaml

import motor_controller
import searchlight


def configure_logging(logfile):
  logging.basicConfig(level=logging.DEBUG,
                      format='%(asctime)s %(levelname)-8s %(message)s',
                      filename=logfile,
                      filemode='w')
  # Configure Twisted to log to our logfile too.
  observer = log.PythonLoggingObserver()
  observer.start()


def main():
  parser = argparse.ArgumentParser(
      description='OSC server to control some number of searchlights.')
  parser.add_argument('--config_file', type=argparse.FileType(), required=True,
                      help='YAML config file specifying how the searchlights are set up.')
  parser.add_argument('--logfile', type=str, default='/tmp/searchlight.log')
  args = parser.parse_args()

  configure_logging(args.logfile)

  config = yaml.load(args.config_file)
  logging.info('Got config file: %s', pprint.pformat(config))

  osc_receiver = dispatch.Receiver()
  reactor.listenMulticast(
      config['osc_server']['port'],
      async.MulticastDatagramServerProtocol(osc_receiver, config['osc_server']['address']),
      listenMultiple=True)

  if not config.get('searchlights'):
    logging.error('Config file specifies no searchlights.')
    return

  searchlights = []
  for searchlight_config in config.get('searchlights'):
    controller_config = searchlight_config.pop('motor_controller')
    controller = motor_controller.MotorController(reactor, **controller_config)
    searchlights.append(searchlight.Searchlight(controller,  osc_receiver, **searchlight_config))

  reactor.run()


if __name__ == '__main__':
  main()
