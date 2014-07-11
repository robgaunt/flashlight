import logging
import math
import psmove
import time

from twisted.internet import task

PSMOVE_CONTROL_LOOP_INTERVAL = 0.2


class PSMoveController(object):
  """Acts as an interface between a PSMove controller and searchlights."""
  def __init__(self, reactor, move, serial, searchlights):
    """Creates a PSMove controller.

    Args:
      reactor: The twisted.internet.reactor module.
      move: A PSMove instance.
      serial: The serial number of the move, as a string.
      searchlights: A list of searchlight.Searchlight instances that this controls.
    """
    self.reactor = reactor
    self.move = move
    self.serial = serial
    self.searchlights = searchlights
    self.set_orientation_enabled_(False)
    self.reactor.addSystemEventTrigger('before', 'shutdown', self.before_shutdown_)
    self.task_ = task.LoopingCall(self.control_loop_)
    self.task_.start(PSMOVE_CONTROL_LOOP_INTERVAL)

  def disconnect(self):
    self.task_.stop()
    del self.move
    self.move = None

  def control_loop_(self):
    """Main control loop which gets orientation and sends commands."""
    if self.move.poll():
      pressed, released = self.move.get_button_events()
      if pressed & psmove.Btn_START:
        logging.info('Resetting PSMove %s orientation.', self.serial)
        self.move.reset_orientation()
        self.set_orientation_enabled_(True)

      if pressed & psmove.Btn_SELECT:
        self.set_orientation_enabled_(False)

      if self.orientation_enabled:
        self.update_searchlight_from_orientation_()

    # This must be called periodically to keep the LEDs on, even if we do not change the values.
    self.update_leds_()

  def before_shutdown_(self):
    if self.move:
      self.disconnect()

  def set_orientation_enabled_(self, orientation_enabled):
    self.orientation_enabled = orientation_enabled
    self.update_leds_()

  def update_leds_(self):
    # For some unknown reason, if you always tell the move to change to a single color, it doesn't
    # work. (Even if you turn off rate limiting). It seems that you need to make gradual changes
    # to the color over time to make it stick. That doesn't seem right, so I must be missing
    # something.
    scale = 0.8 + 0.2 * math.sin(int(10 * time.time()) / 10.0)
    if self.orientation_enabled:
      self.move.set_leds(0, int(scale * 255), 0)  # Green
    else:
      self.move.set_leds(int(scale * 255), int(scale * 255), 0)  # Yellow
    self.move.update_leds()

  def update_searchlight_from_orientation_(self):
    qw, qx, qy, qz = self.move.get_orientation()
    # Convert quaternion to euler-angle.
    # Formulas from:
    # http://www.euclideanspace.com/maths/geometry/rotations/conversions/quaternionToEuler/
    # but note that all values are negated.
    azimuth = 0
    elevation = 0
    test = qx * qy + qz * qw
    roll = math.asin(2 * test)
    if test > 0.499:
      azimuth = -2 * math.atan2(qx, qw)
      elevation = math.pi / 2
    elif test < -0.499:
      azimuth = 2 * math.atan2(qx, qw)
      elevation = 0
    else:
      azimuth = -math.atan2(2 * qy * qw - 2 * qx * qz,
                            1 - 2 * qy * qy - 2 * qz * qz)
      elevation = math.atan2(2 * qx * qw - 2 * qy * qz ,
                             1 - 2 * qx * qx - 2 * qz * qz)
    for searchlight in self.searchlights:
      # print 'az %.2f el %.2f roll %.2f' % (
      #     azimuth * 57.2957795, elevation * 57.2957795, roll * 57.2957795)
      searchlight.target_angle(azimuth, elevation)

