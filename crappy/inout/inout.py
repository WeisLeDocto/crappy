# coding: utf-8

from time import time, sleep
from typing import Optional, Dict, Any, Union

from .._global import DefinitionError


class MetaIO(type):
  """Metaclass ensuring that two InOuts don't have the same name, and that all
  InOuts define the required methods. Also keeps track of all the InOut
  classes, including the custom user-defined ones."""

  classes = {}
  needed_methods = ["open", "close"]

  def __new__(mcs, name: str, bases: tuple, dct: dict) -> type:
    return super().__new__(mcs, name, bases, dct)

  def __init__(cls, name: str, bases: tuple, dct: dict) -> None:
    super().__init__(name, bases, dct)

    # Checking that an InOut with the same name doesn't already exist
    if name in cls.classes:
      raise DefinitionError(f"The {name} class is already defined !")

    # Gathering all the defined methods
    defined_methods = list(dct.keys())
    defined_methods += [base.__dict__.keys() for base in bases]

    # Checking for missing methods
    missing_methods = [meth for meth in cls.needed_methods
                       if meth not in defined_methods]

    # Raising if there are unexpected missing methods
    if missing_methods and name != "InOut":
      raise DefinitionError(
        f'Class {name} is missing the required method(s): '
        f'{", ".join(missing_methods)}')

    # Otherwise, saving the class
    if name != 'InOut':
      cls.classes[name] = cls


class InOut(metaclass=MetaIO):
  """Base class for all InOut objects. Implements methods shared by all the
  these objects, and ensures their dataclass is MetaIO."""

  def __init__(self) -> None:
    """Sets the attributes."""

    self._compensations = list()

  def get_data(self) -> Optional[Union[list, Dict[str, Any]]]:
    """This method should acquire data from a device and return it in a
    :obj:`list` along with a timestamp.

    The timestamp must always be the first returned value, and there can be any
    number of other acquired channels. The same number of values should always
    be returned, and they should be in the same order.

    Alternatively, the values can be returned in a :obj:`dict`. In that case,
    the ``labels`` argument of the IOBlock is ignored and the returned labels
    correspond to the keys of the dict.

    It is alright for this method to return :obj:`None` if there's no data to
    acquire.
    """

    print(f"WARNING ! The InOut {type(self).__name__} has downstream links but"
          f" its get_data method is not defined !\nNo data sent to downstream "
          f"links.")
    sleep(1)
    return

  def set_cmd(self, *_) -> None:
    """This method should handle commands received from the upstream blocks.

    Usually the command is meant to be set on a device, but any other behavior
    is possible. The commands will be passed to this method as `args` (not
    `kwargs`), in the same order as the ``cmd_labels`` are given in the
    IOBlock.

    If the expected number of commands is always the same, you can simply put
    as many `args` to your ``set_cmd`` method as there are commands. For
    example for three commands:
    ::

      def set_cmd(self, cmd0, cmd1, cmd2):
        ...

    Alternatively, or if the number of commands may vary from one test to
    another, you can get all the commands at once in a :obj:`tuple` by putting
    a single unpacking argument. Example:
    ::

      def set_cmd(self, *cmds):
        number_of_commands = len(cmds)
        cmd0 = cmds[0]
        ...

    """

    print(f"WARNING ! The InOut {type(self).__name__} has incoming links but"
          f" its set_cmd method is not defined !\nThe data received from the "
          f"incoming links is discarded.")
    sleep(1)
    return

  def start_stream(self) -> None:
    """This method should start the acquisition of the stream."""

    print(f"WARNING ! The InOut {type(self).__name__} does not define the "
          f"start_stream method !")

  def get_stream(self) -> Optional[Union[list, Dict[str, Any]]]:
    """This method should acquire a stream as a numpy array, and return it in a
    :obj:`list` along with an array carrying the timestamps.

    The time array must be the first element of the list, the stream array the
    second element. The time array should have only one column, the stream
    array can have any number of columns representing the different channels
    acquired.

    It is also possible to return the two arrays in a :obj:`dict`, in which
    case the ``labels`` argument is ignored and the keys of the dict set the
    returned labels.

    It is alright for this method to return :obj:`None` if there's no data to
    acquire.
    """

    print(f"WARNING ! The InOut {type(self).__name__} has downstream links but"
          f" its get_stream method is not defined !\nNo data sent to "
          f"downstream links.")
    sleep(1)
    return

  def stop_stream(self) -> None:
    """This method should stop the acquisition of the stream."""

    print(f"WARNING ! The InOut {type(self).__name__} does not define the "
          f"stop_stream method !")

  def make_zero(self, delay: float) -> None:
    """Acquires data over a given number of points or for a given delay,
    averages it for each channel, and stores the average. Does not work for
    streams.

    The average values will then be used to remove the offset of the acquired
    data during the test.
    """

    buf = []
    t0 = time()

    # Acquiring data for a given delay
    while time() < t0 + delay:
      data = self.get_data()
      if data is not None and len(data) > 1:
        buf.append(data[1:])

    # Averaging the values and storing them
    for values in zip(*buf):
      try:
        self._compensations.append(-sum(values) / len(values))
      except TypeError:
        # If something goes wrong, just forget about the offsetting
        self._compensations = list()
        print(f"WARNING ! Cannot calculate the offset for the InOut "
              f"{type(self).__name__} !\nPossible reasons are that it doesn't"
              f"return only numbers, or that it returns a dict instead of the "
              f"expected list.")
        return

  def return_data(self) -> Optional[Union[list, Dict[str, Any]]]:
    """Returns the data from :meth:`get_data`, corrected by an offset if the
    ``make_zero`` argument of the IOBlock is set."""

    data = self.get_data()

    # If there's no offsetting, just return the data
    if data is None or not self._compensations:
      return data

    # Otherwise, offset the acquired data except for time
    elif len(data[1:]) == len(self._compensations):
      try:
        return [data[0]] + [val + comp for val, comp in
                            zip(data[1:], self._compensations)]
      # Shouldn't happen but doesn't harm to be careful
      except TypeError:
        return data

    # Should also not happen
    else:
      raise ValueError("The number of offsets doesn't match the number of "
                       "acquired values.")

  def eval_offset(self, delay: float = 2) -> list:
    """Method formerly used for offsetting the output of an InOut object.
    Kept for backwards-compatibility reason only.

    Acquires data for a given delay and returns for each label the opposite of
    the average of the acquired values. It is then up to the user to use this
    output to offset the data.
    """

    if not hasattr(self, 'get_data'):
      raise IOError("The eval_offset method cannot be called by an InOut that "
                    "doesn't implement the get_data method.")

    t0 = time()
    buf = []

    # Acquiring data for a given delay
    while time() < t0 + delay:
      buf.append(self.get_data()[1:])

    # Averaging the acquired values
    ret = []
    for label_values in zip(*buf):
      ret.append(-sum(label_values) / len(label_values))

    return ret
