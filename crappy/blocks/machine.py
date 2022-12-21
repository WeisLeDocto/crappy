# coding: utf-8

from time import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, fields

from .block import Block
from ..actuator import actuator_list, Actuator


@dataclass
class Actuator_instance:
  """"""

  actuator: Actuator
  speed: Optional[float] = None
  position_label: Optional[str] = None
  speed_label: Optional[str] = None
  mode: str = 'speed'
  cmd_label: str = 'cmd'
  speed_cmd_label: Optional[str] = None


class Machine(Block):
  """This block is meant to drive one or several :ref:`Actuators`.

  The possibility to drive several Actuators from a unique block is given so
  that they can be driven in a synchronized way. If synchronization is not
  needed, it is preferable to drive the Actuators from separate Machine blocks.
  """

  def __init__(self,
               actuators: List[Dict[str, Any]],
               common: Optional[Dict[str, Any]] = None,
               time_label: str = 't(s)',
               spam: bool = False,
               freq: float = 200,
               verbose: bool = False) -> None:
    """Sets the args and initializes the parent class.

    Args:
      actuators: The :obj:`list` of all the :ref:`Actuators` this block needs
        to drive. It contains one :obj:`dict` for every Actuator, with
        mandatory and optional keys. The keys providing information on how to
        drive the Actuator are listed below. Any other key will be passed to
        the Actuator object as argument when instantiating it.
      common: The keys of this :obj:`dict` will be common to all the Actuators.
        If it conflicts with an existing key for an Actuator, the common one
        will prevail.
      time_label: If reading speed or position from one or more Actuators, the
        time information will be carried by this label.
      spam: If :obj:`True`, a command is sent to the Actuators on each loop of
        the block, else it is sent every time a new command is received.
      freq: The block will try to loop at this frequency.
      verbose: If :obj:`True`, prints the looping frequency of the block.

    Note:
      - ``actuators`` keys:

        - ``type``: The name of the Actuator class to instantiate. This key is
          mandatory.
        - ``cmd_label``: The label carrying the command for driving the
          Actuator. It defaults to `'cmd'`.
        - ``mode``: Can be either `'speed'` or `'position'`. Will either call
          :meth:`set_speed` or :meth:`set_position` to drive the actuator. When
          driven in `'position'` mode, the speed of the actuator can also be
          adjusted, see the ``speed_cmd_label`` key. The default mode is
          `'speed'`.
        - ``speed``: If mode is `'position'`, the speed at which the Actuator
          should move. This speed is passed as second argument to the
          :meth:`set_position` method of the Actuator. If the
          ``speed_cmd_label`` key is not specified, this speed will remain the
          same for the entire test. This key is not mandatory.
        - ``position_label``: If given, the block will return the value of
          :meth:`get_position` under this label. This key is not mandatory.
        - ``speed_label``: If given, the block will return the value of
          :meth:`get_speed` under this label. This key is not mandatory.
        - ``speed_cmd_label``: The label carrying the speed to set when driving
          in position mode. Each time a value is received, the stored speed
          value is updated. It will also overwrite the ``speed`` key if given.

    """

    super().__init__()
    self.freq = freq
    self.verbose = verbose

    self._time_label = time_label
    self._spam = spam

    # No extra information to add to the main dicts
    if common is None:
      common = dict()

    # Updating the settings with the common information
    for actuator in actuators:
      actuator.update(common)

    # Making sure all the dicts contain the 'type' key
    if not all('type' in dic for dic in actuators):
      raise ValueError("The 'type' key must be provided for all the "
                       "actuators !")

    # The names of the possible settings, to avoid typos and reduce verbosity
    actuator_settings = [field.name for field in fields(Actuator_instance)
                         if field.type is not Actuator]

    # The list of all the Actuator types to instantiate
    types = [actuator['type'] for actuator in actuators]

    if not all(type_ in actuator_list for type_ in types):
      unknown = tuple(type_ for type_ in types if type_ not in actuator_list)
      raise ValueError(f"[Machine] Unknown actuator type(s) : {unknown}\n"
                       f"The possible types are : {actuator_list}")

    # The settings that won't be passed to the Actuator objects
    settings = [{key: value for key, value in actuator.items()
                 if key in actuator_settings}
                for actuator in actuators]

    # The settings that will be passed as kwargs to the Actuator objects
    actuators_kw = [{key: value for key, value in actuator.items()
                     if key not in ('type', *actuator_settings)}
                    for actuator in actuators]

    # Instantiating the actuators and storing them
    self._actuators = [Actuator_instance(
      actuator=actuator_list[type_](**actuator_kw), **setting)
      for type_, setting, actuator_kw in zip(types, settings, actuators_kw)]

  def prepare(self) -> None:
    """Checks the validity of the linking and initializes all the Actuator
    objects to drive."""

    # Checking the consistency of the linking
    if not self.inputs and not self.outputs:
      raise IOError("The Machine block isn't linked to any other block !")

    # Opening each actuator
    for actuator in self._actuators:
      actuator.actuator.open()

  def loop(self) -> None:
    """Receives the commands from upstream blocks, sets them on the actuators
    to drive, and sends the read positions and speed to the downstream
    blocks."""

    # Receiving the latest command
    if self._spam:
      recv = self.get_last(blocking=False)
    else:
      recv = self.recv_all_last()

    # Iterating over the actuators for setting the commands
    if recv:
      for actuator in self._actuators:
        # Setting the speed attribute if it was received
        if actuator.speed_cmd_label is not None and \
            actuator.speed_cmd_label in recv:
          actuator.speed = recv[actuator.speed_cmd_label]

        # Setting only the commands that were received
        if actuator.cmd_label in recv:
          # Setting the speed command
          if actuator.mode == 'speed':
            actuator.actuator.set_speed(recv[actuator.cmd_label])
          # Setting the position command
          else:
            actuator.actuator.set_position(recv[actuator.cmd_label],
                                           actuator.speed)

    to_send = {}

    # Iterating over the actuators to get the speeds and the positions
    for actuator in self._actuators:
      if actuator.position_label is not None:
        position = actuator.actuator.get_position()
        if position is not None:
          to_send[actuator.position_label] = position
      if actuator.speed_label is not None:
        speed = actuator.actuator.get_speed()
        if speed is not None:
          to_send[actuator.speed_label] = speed

    # Sending the speed and position values if any
    if to_send:
      to_send[self._time_label] = time() - self.t0
      self.send(to_send)

  def finish(self) -> None:
    """Stops and closes all the actuators to drive."""

    for actuator in self._actuators:
      actuator.actuator.stop()
    for actuator in self._actuators:
      actuator.actuator.close()
