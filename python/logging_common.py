"""Utilities for configuring logging parameters."""

__author__ = 'Rob Gaunt (robgaunt@gmail.com)'

import logging
from twisted.python import log


def configure_logging(logfile, level=logging.INFO, log_to_stderr=False):
  format = '%(asctime)s %(levelname)-8s %(message)s'
  logging.basicConfig(level=level,
                      format=format,
                      filename=logfile,
                      filemode='w')

  if log_to_stderr:
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(format))
    root_logger = logging.getLogger('')
    root_logger.addHandler(handler)

  # Configure Twisted to use our logger.
  observer = log.PythonLoggingObserver()
  observer.start()


def add_logging_args(argument_parser):
  argument_parser.add_argument('--logfile', type=str, default='/home/flashlight/flashlight.log')
  argument_parser.add_argument('--debug', action='store_true', help='Enable debug logging.')
  argument_parser.add_argument('--alsologtostderr', action='store_true',
                               help='Log output to stderr as well as a file.')


def configure_logging_from_args(args):
  level = logging.DEBUG if args.debug else logging.INFO
  configure_logging(
      args.logfile, level=level, log_to_stderr=args.alsologtostderr)
