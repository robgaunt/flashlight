__author__ = 'Rob Gaunt (robgaunt@gmail.com)'

import base64

from txosc import async
from txosc import osc
import logging


def _try_fixing_invalid_osc_data(data):
  parts = data.split(',', 1)
  if len(parts) != 2:
    return None
  message = parts[0]
  try:
    decoded_message = base64.b64decode(message)
    if decoded_message:
      decoded_message += '\x00'
      pad_bytes = (4 - len(decoded_message)) % 4
      decoded_message += '\x00' * pad_bytes
      return data.replace(message, decoded_message)
  except TypeError:
    pass  # Couldn't base64 decode, give up.


def _patched_elementFromBinary(data):
  if data[0] == "/":
    element, data = osc.Message.fromBinary(data)
  elif data[0] == "#":
    element, data = osc.Bundle.fromBinary(data)
  else:
    fixedData = _try_fixing_invalid_osc_data(data)
    if fixedData:
      element = osc._elementFromBinary(fixedData)
    else:
      raise osc.OscError("Error parsing OSC data: " + data)
  return element


class MulticastDatagramServerProtocol(async.MulticastDatagramServerProtocol):
  """A special OSC protocol which uses a different _elementFromBinary to handle bad message names.
  This works around a compatibility issue where new versions of the touch OSC editor base64
  encode all message names, but old versions of the client don't unencode them before sending,
  causing a parse error in txosc.
  """

  def datagramReceived(self, data, (host, port)):
    element = _patched_elementFromBinary(data)
    self.receiver.dispatch(element, (host, port))

