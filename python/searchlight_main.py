#!/usr/bin/python

"""Executable script which runs an OSC server to control a single searchlight.

Example usage:
  ./searchlight_main.py --config_file ../configs/simple.yaml
"""

__author__ = 'robgaunt@gmail.com (Rob Gaunt)'

import argparse
import logging
import pprint
from txosc import async
from txosc import dispatch
from twisted.internet import reactor
from twisted.web import resource
from twisted.web import server
import yaml

from admin import admin_server
import logging_common
import motor_controller
import searchlight
import searchlight_config


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

  if not config.get('configuration_database'):
    logging.error('Config file does not specify a searchlight configuration database.')
    return
  config_store = searchlight_config.SearchlightConfigStore.create_with_sqlite_database(
      config.get('configuration_database'))

  osc_receiver = dispatch.Receiver()
  reactor.listenMulticast(
      config['osc_server']['port'],
      async.MulticastDatagramServerProtocol(osc_receiver, config['osc_server']['address']),
      listenMultiple=True)

  if not config.get('searchlights'):
    logging.error('Config file specifies no searchlights.')
    return

  searchlights = []
  for config_values in config.get('searchlights'):
    controller_config = config_values.pop('motor_controller')
    controller = motor_controller.MotorController(reactor, **controller_config)
    searchlights.append(searchlight.Searchlight(controller,  osc_receiver, config_store, **config_values))

  if not config.get('admin_server_port'):
    logging.error('Config file does not specify administration server port.')
    return
  reactor.listenTCP(
      config.get('admin_server_port'),
      admin_server.AdminServer(searchlights))

  reactor.run()


if __name__ == '__main__':
  main()
