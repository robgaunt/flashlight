__author__ = 'Rob Gaunt (robgaunt@gmail.com)'

import logging
import math

SEARCHLIGHT_NAME_ALL = "all"
RADIANS_TO_DEGREES = 57.2957795
DEGREES_TO_RADIANS = 1 / RADIANS_TO_DEGREES
MAX_ELEVATION = 2000
RADIUS_OF_EARTH_METERS = 6373000  # At 40 degrees latitude.

# The motor controller channel which controls azimuth or elevation angle.
AZIMUTH_CHANNEL = 1
ELEVATION_CHANNEL = 2

POSITIONING_MODE_DIRECT = 'direct'
POSITIONING_MODE_MIRROR = 'mirror'  # Not yet implemented.
SUPPORTED_POSITIONING_MODES = (POSITIONING_MODE_DIRECT, POSITIONING_MODE_MIRROR)

ELEVATION_FACTOR = 1


class TargetGrid(object):
  """Helper class which performs an affine transformation from OSC xy grid to a target grid."""

  def __init__(self, upper_left, upper_right, lower_left):
    self.ul_lat, self.ul_lon = upper_left
    self.ur_lat, self.ur_lon = upper_right
    self.ll_lat, self.ll_lon = lower_left

  def transform(self, x, y):
    return (
        (self.ll_lat - self.ul_lat) * x + (self.ur_lat - self.ul_lat) * y + self.ul_lat,
        (self.ll_lon - self.ul_lon) * x + (self.ur_lon - self.ul_lon) * y + self.ul_lon)


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
  return RADIUS_OF_EARTH_METERS * c


def clamp_and_scale(value, min_value, max_value, scaled_min, scaled_max):
  if value < min_value:
    value = min_value
  elif value > max_value:
    value = max_value
  return (
      float(scaled_max - scaled_min) * (value - min_value) / (max_value - min_value) + scaled_min)


class Searchlight(object):
  """Serves as the wiring between the OSC server and motor controller.

  This registers OSC addresses with a txosc Receiver, and translates OSC commands to motor
  controller commands.

  All OSC addresses are of the form /<searchlight name>/<command>. Each searchlight registers for
  addresses using both its name and the name "all". This makes it possible to send OSC commands
  either to individual searchlights, or to all searchlights at the same time.
  """

  def __init__(
      self, motor_controller, osc_receiver, name, positioning_mode,
      position=None, zero_position=None, target_grid=None, draw_grid=None,
      direct_positioning=None, mirror_positioning=None):
    """Initializes a Searchlight.

    Args:
      motor_controller: An instance of motor_controller.MotorController.
      osc_receiver: An instance of txosc.dispatch.Receiver.
      name: The name of this searchlight. Used to identify which OSC endpoints it responds to.
      position: A latitude, longitude pair (in floating-point degrees) representing the position
        of the searchlight.
      zero_position: The position at which the searchlight points when the motor is at position
        zero.
      target_grid: A grid defined by upper_left, upper_right, lower_left positions.
    """
    assert name != SEARCHLIGHT_NAME_ALL, 'Name %s is reserved' % SEARCHLIGHT_NAME_ALL
    self.name = name
    self.motor_controller = motor_controller
    self.osc_receiver = osc_receiver

    # Add standard OSC callbacks.
    self.add_osc_callback('raw_elevation', self.osc_raw_elevation)
    self.add_osc_callback('raw_azimuth', self.osc_raw_azimuth)
    self.osc_receiver.setFallback(self.osc_ignore)

    assert positioning_mode in SUPPORTED_POSITIONING_MODES, 'Invalid mode %s' % positioning_mode
    self.positioning_mode = positioning_mode
    self.direct_positioning = direct_positioning
    self.mirror_positioning = mirror_positioning

    # The rest of the configuration parameters are optional.
    # position and zero_psition are needed if you want to target a specific location.
    if position:
      self.pos_lat, self.pos_lon = position
    if zero_position:
      self.zpos_lat, self.zpos_lon = zero_position
    if position and zero_position:
      self.distance_to_zero = haversine(self.pos_lat, self.pos_lon, self.zpos_lat, self.zpos_lon)

    # target_grid is needed if you want to map the OSC target grid to a real location, so we only
    # add the appropriate OSC callbacks if it is specified.
    if target_grid:
      self.target_grid = TargetGrid(**target_grid)
      self.add_osc_callback('grid', self.osc_grid)
      self.add_osc_callback('grid_elevation', self.osc_grid_elevation)
      self.last_elevation = 0
      self.last_target_lat = self.zpos_lat
      self.last_target_lon = self.zpos_lon

    if draw_grid:
      self.draw_grid = draw_grid
      self.add_osc_callback('draw_grid', self.osc_draw_grid)
      # TouchOSC is a bit weird in that its grid control sends (y, x) instead of (x, y).
      self.add_osc_callback('draw_grid_yx', self.osc_draw_grid_yx)

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

  def target_angle(self, azimuth, elevation):
    """Aims the searchlight at given azimuth and elevation angle, relative to zero."""
    azimuth_degrees = azimuth * RADIANS_TO_DEGREES
    elevation_degrees = elevation * RADIANS_TO_DEGREES
    logging.debug('target_angle: azimuth %s elevation %s', azimuth_degrees, elevation_degrees)
    if self.positioning_mode == POSITIONING_MODE_DIRECT:
      azimuth_degrees_min, azimuth_degrees_max = self.direct_positioning['azimuth_angle_bound']
      elevation_degrees_min, elevation_degrees_max = self.direct_positioning['elevation_angle_bound']      
      # TODO(robgaunt): Azimuth motor position is inverted because the controllers aren't set up right.
      azimuth_motor_position = clamp_and_scale(
          azimuth_degrees, azimuth_degrees_min, azimuth_degrees_max, 1, -1)
      self.motor_controller.go(AZIMUTH_CHANNEL, azimuth_motor_position)
      elevation_motor_position = clamp_and_scale(
          elevation_degrees, elevation_degrees_min, elevation_degrees_max, -1, 1)
      self.motor_controller.go(ELEVATION_CHANNEL, elevation_motor_position)
    elif self.positioning_mode == POSITIONING_MODE_MIRROR:
      azimuth_degrees_min, azimuth_degrees_max = self.mirror_positioning['azimuth_angle_bound']
      elevation_degrees_min, elevation_degrees_max = self.mirror_positioning['elevation_angle_bound']      
      degrees_at_zero = self.mirror_positioning['degrees_at_zero_position']
      actual_azimuth_degrees = degrees_at_zero + azimuth_degrees
      # Divide by zero because each change of 1 degree in rotation angle causes a 2 degree change
      # in beam position because it changes the plane of reflection and the angle of incidence.
      azimuth_motor_position = clamp_and_scale(
          actual_azimuth_degrees / 2.0, azimuth_degrees_min, azimuth_degrees_max, 1, -1)
      # TODO(robgaunt): Azimuth motor position is inverted because the controllers aren't set up right.
      self.motor_controller.go(AZIMUTH_CHANNEL, azimuth_motor_position)
      # TODO(robgaunt): This is wrong - we need to know the height that the searchlight sits above
      # the mirror in order to actually calculate this. But good enough for now.
      elevation_motor_position = clamp_and_scale(
          elevation_degrees, elevation_degrees_min, elevation_degrees_max, -1, 1)
      self.motor_controller.go(ELEVATION_CHANNEL, elevation_motor_position)
    else:
      raise AssertionError('Invalid positioning mode.')

  def add_osc_callback(self, callback_name, callback):
    self.osc_receiver.addCallback('/%s/%s' % (self.name, callback_name), callback)
    self.osc_receiver.addCallback('/%s/%s' % (SEARCHLIGHT_NAME_ALL, callback_name), callback)

  def unwrap_osc(func):
    """Decorator for all OSC handlers."""
    def handler(self, message, address):
      logging.debug('Searchlight %s received %s from %s', self.name, message, address)
      func(self, *message.getValues())
    return handler

  @unwrap_osc
  def osc_raw_elevation(self, value):
    assert 0 <= value and value <= 1, 'Invalid osc_raw_elevation value: %s' % value
    self.motor_controller.go(ELEVATION_CHANNEL, clamp_and_scale(value, 0, 1, -1, 1))

  @unwrap_osc
  def osc_raw_azimuth(self, value):
    assert 0 <= value and value <= 1, 'Invalid osc_raw_azimuth value: %s' % value
    self.motor_controller.go(AZIMUTH_CHANNEL, clamp_and_scale(value, 0, 1, -1, 1))

  @unwrap_osc
  def osc_grid(self, y, x):
    assert 0 <= x and x <= 1, 'Invalid osc_grid x: %s' % x
    assert 0 <= y and y <= 1, 'Invalid osc_grid y: %s' % y
    self.last_target_lat, self.last_target_lon = self.target_grid.transform(x, y)
    self.target_position(self.last_target_lat, self.last_target_lon, self.last_elevation)

  @unwrap_osc
  def osc_grid_elevation(self, elevation):
    assert 0 <= elevation and elevation <= 1, 'Invalid osc_grid_elevation: %s' % elevation
    self.last_elevation = elevation * MAX_ELEVATION
    self.target_position(self.last_target_lat, self.last_target_lon, self.last_elevation)

  def _osc_draw_grid(self, x, y):
    x -= 0.5
    azimuth_angle = math.atan(x / y)
    elevation_angle = math.atan(ELEVATION_FACTOR / math.sqrt(x * x + y * y))
    self.target_angle(azimuth_angle, elevation_angle)

  @unwrap_osc
  def osc_draw_grid(self, x, y):
    self._osc_draw_grid(x, y)

  @unwrap_osc
  def osc_draw_grid_yx(self, y, x):
    self._osc_draw_grid(x, y)

  def osc_ignore(self, message, address):
    pass
