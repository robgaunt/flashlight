#!/usr/bin/python

"""Executable script which runs an OSC server to control a single searchlight.

Example usage:
  ./searchlight_main.py --config_file ../configs/simple.yaml
"""

__author__ = 'robgaunt@gmail.com (Rob Gaunt)'

import argparse
import logging
import pprint
from txosc import dispatch
from twisted.internet import reactor
import yaml

from admin import admin_server
from motor_controller import MotorController
from psmove_connection_manager import PSMoveConnectionManager
from searchlight import Searchlight
from searchlight_config import SearchlightConfigStore
import logging_common
import osc_server


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
  config_store = SearchlightConfigStore.create_with_sqlite_database(
      config.get('configuration_database'))

  osc_receiver = dispatch.Receiver()
  reactor.listenMulticast(
      config['osc_server']['port'],
      osc_server.MulticastDatagramServerProtocol(
          osc_receiver, config['osc_server']['address']),
      listenMultiple=True)

  if not config.get('searchlights'):
    logging.error('Config file specifies no searchlights.')
    return

  name_to_searchlight = {}
  for config_values in config.get('searchlights'):
    motor_controller = MotorController(reactor, **config_values.pop('motor_controller'))
    searchlight = Searchlight(motor_controller, osc_receiver, config_store, **config_values)
    name_to_searchlight[searchlight.name] = searchlight

  psmove_connection_manager = None
  psmove_controller_configs = config.get('psmove_controllers', [])
  if psmove_controller_configs:
    psmove_connection_manager = PSMoveConnectionManager(
        reactor, psmove_controller_configs, name_to_searchlight)

  if not config.get('admin_server_port'):
    logging.error('Config file does not specify administration server port.')
    return
  reactor.listenTCP(
      config.get('admin_server_port'),
      admin_server.AdminServer(name_to_searchlight.values()))

  reactor.run()


if __name__ == '__main__':
  main()
