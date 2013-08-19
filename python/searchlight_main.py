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
import yaml

import logging_common
import motor_controller
import searchlight


def main():
  parser = argparse.ArgumentParser(
      description='OSC server to control some number of searchlights.')
  parser.add_argument('--config_file', type=argparse.FileType(), required=True,
                      help='YAML config file specifying how the searchlights are set up.')
  logging_common.add_logging_args(parser)
  args = parser.parse_args()

  logging_common.configure_logging_from_args(args)

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
