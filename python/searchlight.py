__author__ = 'Rob Gaunt (robgaunt@gmail.com)'

import logging
import math

SEARCHLIGHT_NAME_ALL = "all"
RADIANS_TO_DEGREES = 57.2957795
DEGREES_TO_RADIANS = 1 / RADIANS_TO_DEGREES
MAX_ELEVATION = 1000


class Grid(object):
  """Helper class for doing affine tranformations."""

  def __init__(self, upper_left, upper_right, lower_left):
    self.ul_lat = upper_left['latitude']
    self.ul_long = upper_left['longitude']
    self.ur_lat = upper_right['latitude']
    self.ur_long = upper_right['longitude']
    self.ll_lat = lower_left['latitude']
    self.ll_long = lower_left['longitude']

  def transform(self, x, y):
    return (
        (self.ll_lat - self.ul_lat) * x  + (self.ur_lat - self.ul_lat) * y + self.ul_lat,
        (self.ll_long - self.ul_long) * x + (self.ur_long - self.ul_long) * y + self.ul_long)


def haversine(lat1, lon1, lat2, lon2):
  """Returns the distance between points in meters using the Haversine formula."""
  lat1 *= DEGREES_TO_RADIANS
  lon1 *= DEGREES_TO_RADIANS
  lat2 *= DEGREES_TO_RADIANS
  lon2 *= DEGREES_TO_RADIANS
  dlon = lon2 - lon1
  dlat = lat2 - lat1
  a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * (math.sin(dlon / 2) ** 2)
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
  # Approximate radius of earth, in meters, at 40 degrees latitude.
  return 6373000 * c



class Searchlight(object):
  """Serves as the wiring between the OSC server and motor controller.

  This registers OSC addresses with a txosc Receiver, and translates OSC commands to motor
  controller commands.

  All OSC addresses are of the form /<searchlight name>/<command>. Each searchlight registers for
  addresses using both its name and the name "all". This makes it possible to send OSC commands
  either to individual searchlights, or to all searchlights at the same time.
  """

  def __init__(
      self, motor_controller, osc_receiver, name,
      position=None, zero_position=None, target_grid=None):
    """Initializes a Searchlight.

    Args:
      motor_controller: An instance of motor_controller.MotorController.
      osc_receiver: An instance of txosc.dispatch.Receiver.
      name: The name of this searchlight. Used to identify which OSC endpoints it responds to.
      position: The position of the searchlight - a dictionary containing 'latitude' and
        'longitude' floating point values representing degrees.
      zero_position: The position at which the searchlight points when the motor is at position
        zero.
      target_grid: A grid defined by upper_left, upper_right, lower_left positions.
    """
    assert name != SEARCHLIGHT_NAME_ALL, 'Name %s is reserved' % SEARCHLIGHT_NAME_ALL
    self.name = name
    self.motor_controller = motor_controller
    self.osc_receiver = osc_receiver
    self.add_osc_callback('go1', self.osc_go_one)
    self.add_osc_callback('go2', self.osc_go_two)
    # TouchOSC sends /accxyz commands hundreds of times per second with the current phone
    # accelerometer readings. This is interesting, but currently causes a LOT of logspam, so
    # blackhole them.
    self.osc_receiver.addCallback('/accxyz', self.osc_ignore)
    if position:
      self.pos_lat = position['latitude']
      self.pos_lon = position['longitude']
    if zero_position:
      self.zpos_lat = zero_position['latitude']
      self.zpos_lon = zero_position['longitude']
    if position and zero_position:
      self.distance_to_zero = haversine(self.pos_lat, self.pos_lon, self.zpos_lat, self.zpos_lon)
    if target_grid:
      self.target_grid = Grid(**target_grid)
      self.add_osc_callback('grid', self.osc_grid)
      self.add_osc_callback('grid_elevation', self.osc_grid_elevation)
      self.last_elevation = 0
      self.last_target_lat = self.zpos_lat
      self.last_target_lon = self.zpos_lon

  def add_osc_callback(self, callback_name, callback):
    self.osc_receiver.addCallback('/%s/%s' % (self.name, callback_name), callback)
    self.osc_receiver.addCallback('/%s/%s' % (SEARCHLIGHT_NAME_ALL, callback_name), callback)

  def target_position(self, latitude, longitude, altitude):
    """Aims the searchlight to target given position, specified by coordinates and altitude."""
    assert self.pos_lat and self.zpos_lat, (
        'Must know position and zero_position to compute angles to target.')
    a = haversine(self.zpos_lat, self.zpos_lon, latitude, longitude)
    b = self.distance_to_zero
    c = haversine(latitude, longitude, self.pos_lat, self.pos_lon)
    # Calculate sign of rotation angle by determining whether target is to the left or right of a
    # line drawn from position to zero_position.
    rotation_sign = latitude - self.pos_lat - (longitude - self.pos_lon) * (
        (self.zpos_lat - self.pos_lat) / (self.zpos_lon - self.pos_lon))
    # Law of Cosines
    rotation_angle = math.copysign(
        math.acos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c )), rotation_sign)
    elevation_angle = math.atan(altitude / c)
    self.target_angle(rotation_angle, elevation_angle)

  def target_angle(self, rotation, elevation):
    """Aims the searchlight at given rotation and elevation angle, relative to zero."""
    logging.debug(
        'target_angle: rotation %s elevation %s',
        RADIANS_TO_DEGREES * rotation, RADIANS_TO_DEGREES * elevation)
    # TODO - translate into motor command

  def unwrap_osc(func):
    """Decorator for all OSC handlers."""
    def handler(self, message, address):
      logging.debug('Searchlight %s received %s from %s', self.name, message, address)
      func(self, *message.getValues())
    return handler

  @unwrap_osc
  def osc_go_one(self, value):
    assert -1 <= value and value <= 1, 'Invalid osc_go_one value: %s' % value
    self.motor_controller.go(1, value)

  @unwrap_osc
  def osc_go_two(self, value):
    assert -1 <= value and value <= 1, 'Invalid osc_go_two value: %s' % value
    if 2 <= self.motor_controller.num_channels:
      self.motor_controller.go(2, value)
    else:
      logging.info('Searchlight %s ignoring command to motor channel 2', self.name)

  @unwrap_osc
  def osc_grid(self, x, y):
    assert 0 <= x and x <= 1, 'Invalid osc_grid x: %s' % x
    assert 0 <= y and y <= 1, 'Invalid osc_grid y: %s' % y
    self.last_target_lat, self.last_target_lon = self.target_grid.transform(x, y)
    self.target_position(self.last_target_lat, self.last_target_lon, self.last_elevation)

  @unwrap_osc
  def osc_grid_elevation(self, elevation):
    assert 0 <= elevation and elevation <= 1, 'Invalid osc_grid_elevation: %s' % elevation
    self.last_elevation = elevation * MAX_ELEVATION
    self.target_position(self.last_target_lat, self.last_target_lon, self.last_elevation)

  def osc_ignore(self, message, address):
    pass
