#!/usr/bin/python

__author__ = 'Rob Gaunt (robgaunt@gmail.com)'

import argparse
import logging

from twisted.internet import reactor

import logging_common
import gps_receiver


def gps_callback(gps_data):
  logging.info('gps_callback: %s', gps_data)


def main():
  parser = argparse.ArgumentParser(description='GPS Example.')
  parser.add_argument('--serial_port', required=True,
                      help='Address of GPS serial port.')
  logging_common.add_logging_args(parser)
  args = parser.parse_args()

  logging_common.configure_logging_from_args(args)
  receiver = gps_receiver.GpsReceiver(reactor, args.serial_port)
  receiver.add_callback(gps_callback)
  reactor.run()


if __name__ == '__main__':
  main()
