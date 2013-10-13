#!/usr/bin/python

"""Executable script to write the searchlight configuration to the database."""

__author__ = 'robgaunt@gmail.com (Rob Gaunt)'

import argparse

import searchlight_config


def main():
  parser = argparse.ArgumentParser(
      description='OSC server to control some number of searchlights.')
  parser.add_argument('--database', type=str, help='File path to the sqlite database.',
                      required=True)
  parser.add_argument('--create_table', action='store_true',
                      help='Creates sqlite database. Will erase any current database contents.')

  args = parser.parse_args()
  store = searchlight_config.SearchlightConfigStore.create_with_sqlite_database(args.database)
  
  if args.create_table:
    store.create_config_table()

  # TODO(robgaunt): Read config values from file.
  config = searchlight_config.SearchlightConfig()
  config.name = u'1'
  config.azimuth_lower_bound = 0
  config.azimuth_upper_bound = 1
  config.elevation_lower_bound = 0
  config.elevation_upper_bound = 1
  store.add(config)

  config = searchlight_config.SearchlightConfig()
  config.name = u'2'
  config.azimuth_lower_bound = 0
  config.azimuth_upper_bound = 1
  config.elevation_lower_bound = 0
  config.elevation_upper_bound = 1
  store.add(config)

  store.commit()

if __name__ == '__main__':
  main()
