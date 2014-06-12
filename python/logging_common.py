"""Utilities for configuring logging parameters."""

__author__ = 'Rob Gaunt (robgaunt@gmail.com)'

import logging
from twisted.python import log


def configure_logging(logfile):
  logging.basicConfig(level=logging.INFO,
                      format='%(asctime)s %(levelname)-8s %(message)s',
                      filename=logfile,
                      filemode='w')
  # Configure Twisted to log to our logfile too.
  observer = log.PythonLoggingObserver()
  observer.start()


def add_logging_args(argument_parser):
  argument_parser.add_argument('--logfile', type=str, default='/tmp/searchlight.log')


def configure_logging_from_args(args):
  configure_logging(args.logfile)
