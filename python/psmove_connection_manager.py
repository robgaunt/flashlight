import logging
import psmove

from twisted.internet import task

import psmove_controller

PSMOVE_CONNECT_INTERVAL = 5


class PSMoveConnectionManager(object):
  """Manages connecting and disconnecting PSMove controllers."""

  def __init__(self, reactor, controller_configs, name_to_searchlight):
    self.reactor = reactor
    self.name_to_searchlight_ = name_to_searchlight
    # As we connect PSMove controllers, we pop an element off of unconnected_configs_ and move it
    # over to serial_to_config_. As we disconnect them, we do the reverse. This assigns
    # configurations to the controllers in the order that they are connected.
    self.unconnected_configs_ = controller_configs
    # Maps PSMove serial (as string) to configuration dictionary.
    self.serial_to_config_ = {}
    # Maps PSMove serial (as string) to PSMoveController instance.
    self.serial_to_controller_ = {}
    # Set of serials for which we already attempted USB pairing. This is kept so that we don't
    # attempt to pair any controller more than once.
    self.paired_usb_serials_ = set()
    self.task_ = task.LoopingCall(self.connect_loop_)
    self.task_.start(PSMOVE_CONNECT_INTERVAL)

  def connect_loop_(self):
    connection_count = psmove.count_connected()
    connected_serials = set()
    logging.debug('Connected Moves: %d', connection_count)
    for psmove_id in xrange(connection_count):
      move = psmove.PSMove(psmove_id)
      serial = move.get_serial()
      logging.debug('Detected move %d serial %s connection %s',
                    psmove_id, serial, self.debug_connection_type_(move))
      connected_serials.add(serial)

      if move.connection_type == psmove.Conn_USB and serial not in self.paired_usb_serials_:
        self.pair_move_(serial, move)
        del move
      elif (move.connection_type == psmove.Conn_Bluetooth and
          serial not in self.serial_to_controller_ and
          self.unconnected_configs_):
        self.connect_move_(serial, move)
      else:
        del move

    self.remove_disconnected_controllers_(connected_serials)

  def pair_move_(self, serial, move):
    """Pairs a USB Move so that it may be connected via Bluetooth.

    It should only be necessary to execute this once each time the application is started. After
    that the Move should already be paired and connect automatically when you press the PS button.
    """
    logging.info('Pairing move: %s', serial)
    move.pair()
    # Turn LEDs green to signify pairing completion.
    move.set_leds(0, 255, 0)
    move.update_leds()
    self.paired_usb_serials_.add(serial)

  def connect_move_(self, serial, move):
    """Connects a Bluetooth Move by creating a PSMoveController instance for it."""
    move.enable_orientation(True)
    has_calibration = move.has_calibration()
    has_orientation = move.has_orientation()
    if has_calibration and has_orientation:
      config = self.unconnected_configs_.pop()
      logging.info('Connecting move: %s config: %s', serial, config)
      searchlights = [self.name_to_searchlight_[s] for s in config['searchlight_names']]
      self.serial_to_config_[serial] = config
      self.serial_to_controller_[serial] = psmove_controller.PSMoveController(
          self.reactor, move, serial, searchlights)
    else:
      logging.error('Unable to connect move: %s - missing calibration (%d) or orientation (%d)',
                    serial, has_calibration, has_orientation)
      # Turn LEDs red to signify connection error.
      move.set_leds(255, 0, 0)
      move.update_leds()

  def remove_disconnected_controllers_(self, connected_serials):
    missing_serials = [s for s in self.serial_to_controller_ if s not in connected_serials]
    for serial in missing_serials:
      logging.info('PSMove with serial %s went missing.', serial)
      self.paired_usb_serials_.discard(serial)
      self.unconnected_configs_.append(self.serial_to_config_.pop(serial))
      controller = self.serial_to_controller_.pop(serial)
      controller.disconnect()

  def debug_connection_type_(self, move):
    if move.connection_type == psmove.Conn_USB:
      return 'USB'
    else:
      return 'Bluetooth'
