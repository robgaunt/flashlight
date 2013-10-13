"""Simple persistence layer for searchlight configuration."""

__author__ = 'Rob Gaunt (robgaunt@gmail.com)'

import storm.locals

_TABLE_NAME = 'searchlight_config'


class SearchlightConfigStore(storm.locals.Store):
  DROP_TABLE_SQL = 'DROP TABLE IF EXISTS %s' % _TABLE_NAME
  CREATE_TABLE_SQL = """
    CREATE TABLE %s (
    name VARCHAR PRIMARY KEY,
    azimuth_lower_bound FLOAT,
    azimuth_upper_bound FLOAT,
    elevation_lower_bound FLOAT,
    elevation_upper_bound FLOAT
    )
  """ % _TABLE_NAME

  def create_config_table(self):
    self.execute(self.DROP_TABLE_SQL)
    self.execute(self.CREATE_TABLE_SQL)

  def get_config_by_name(self, name):
    return self.find(SearchlightConfig, SearchlightConfig.name == name).one()

  def get_or_create_config_by_name(self, name):
    """Fetches config by name, or creates default config if none exists."""
    name = unicode(name)
    config = self.get_config_by_name(name)
    if not config:
      config = SearchlightConfig()
      config.name = name
      config.azimuth_lower_bound = 0
      config.azimuth_upper_bound = 1
      config.elevation_lower_bound = 0
      config.elevation_upper_bound = 1
      self.add(config)
      self.commit()
    return config

  @classmethod
  def create_with_sqlite_database(self, database_path):
    database = storm.locals.create_database('sqlite:%s' % database_path)
    return SearchlightConfigStore(database)


class SearchlightConfig(object):
  __storm_table__ = 'searchlight_config'
  name = storm.locals.Unicode(primary=True)
  azimuth_upper_bound = storm.locals.Float()
  azimuth_lower_bound = storm.locals.Float()
  elevation_upper_bound = storm.locals.Float()
  elevation_lower_bound = storm.locals.Float()
