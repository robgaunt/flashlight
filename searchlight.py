#!/usr/bin/python

"""Executable script which runs an OSC server to control a single searchlight.

Example usage:
  ./searchlight.py --osc_name 1 --osc_address 224.0.0.1 --osc_listen_port 8888 \
                   --serial_address /dev/ttyUSB1
"""

__author__ = 'Rob Gaunt (robgaunt@gmail.com)'

import argparse
import logging
from twisted.internet import reactor

import motor_controller
import searchlight_application


def configure_logging(logfile):
  # TODO(robgaunt)
  logging.basicConfig(level=logging.DEBUG,
                      format='%(asctime)s %(levelname)-8s %(message)s',
                      datefmt='%m-%d %H:%M',
                      filename=logfile,
                      filemode='w')


def main():
  parser = argparse.ArgumentParser(description='OSC server to control a single searchlight.')
  parser.add_argument('--osc_address', type=str, required=True,
                      help='Multicast address to listen for OSC messages.')
  parser.add_argument('--osc_listen_port', type=int, required=True,
                      help='Port to listen for OSC messages.')
  parser.add_argument('--osc_name', type=str, required=True,
                      help='Prefix name for all OSC endpoints.')
  parser.add_argument('--serial_address', type=str, required=True,
                      help='Address of serial device to communicate with the controller.')
  parser.add_argument('--controller_channels', type=int, default=1,
                      help='Number of motor control channels supported by the controller.')
  parser.add_argument('--logfile', type=str, default='/tmp/searchlight.log')
  args = parser.parse_args()

  configure_logging(args.logfile)

  controller = motor_controller.MotorController(
      reactor, args.serial_address, args.controller_channels)
  searchlight_application.SearchlightApplication(
      reactor, controller, args.osc_name, args.osc_address, args.osc_listen_port)
  reactor.run()


if __name__ == '__main__':
  main()
