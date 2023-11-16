# coding: utf-8

from time import time
from typing import Tuple, Optional
from numpy import ndarray
import logging
from .meta_camera import Camera
from .._global import OptionalModule

try:
  import cv2
except (ModuleNotFoundError, ImportError):
  cv2 = OptionalModule("opencv-python")


class CameraOpencv(Camera):
  """A basic class for reading images from a USB camera (including webcams).

  It relies on the OpenCv library. Note that it was purposely kept extremely
  simple as it is mainly used as a demo. See
  :class:`~crappy.camera.CameraOpencv` and
  :class:`~crappy.camera.CameraGstreamer` for classes giving a finer control
  over the camera.
  """

  def __init__(self) -> None:
    """Sets variables and adds the channels setting."""

    super().__init__()

    self._cap = None

    self.add_choice_setting(name="channels",
                            choices=('1', '3'),
                            default='1')

  def open(self, device_num: Optional[int] = 0, **kwargs) -> None:
    """Opens the video stream and sets any user-specified settings.

    Args:
      device_num: The index of the device to open, as an :obj:`int`.
      **kwargs: Any additional setting to set before opening the configuration
        window.
    """

    # Opening the videocapture device
    self.log(logging.INFO, "Opening the image stream from the camera")
    self._cap = cv2.VideoCapture(device_num)

    min_bright, max_bright = self._get_min_max(cv2.CAP_PROP_BRIGHTNESS)
    self.add_scale_setting(name='brightness',
                           lowest=min_bright,
                           highest=max_bright,
                           getter=self._get_brightness,
                           setter=self._set_brightness)

    min_cont, max_cont = self._get_min_max(cv2.CAP_PROP_CONTRAST)
    self.add_scale_setting(name='contrast',
                           lowest=min_cont,
                           highest=max_cont,
                           getter=self._get_contrast,
                           setter=self._set_contrast)

    min_hue, max_hue = self._get_min_max(cv2.CAP_PROP_HUE)
    self.add_scale_setting(name='hue',
                           lowest=min_hue,
                           highest=max_hue,
                           getter=self._get_hue,
                           setter=self._set_hue)

    min_sat, max_sat = self._get_min_max(cv2.CAP_PROP_SATURATION)
    self.add_scale_setting(name='saturation',
                           lowest=min_sat,
                           highest=max_sat,
                           getter=self._get_saturation,
                           setter=self._set_saturation)

    # Setting the kwargs if any
    self.set_all(**kwargs)

  def get_image(self) -> Tuple[float, ndarray]:
    """Grabs a frame from the videocapture object and returns it along with a
    timestamp."""

    # Grabbing the frame and the timestamp
    t = time()
    ret, frame = self._cap.read()

    # Checking the integrity of the frame
    if not ret:
      raise IOError("Error reading the camera")

    # Returning the image in the right format, and its timestamp
    if self.channels == '1':
      return t, cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
      return t, frame

  def close(self) -> None:
    """Releases the videocapture object."""

    if self._cap is not None:
      self.log(logging.INFO, "Closing the image stream from the camera")
      self._cap.release()

  def _get_min_max(self, prop_id: int) -> Tuple[int, int]:
    """Gets the min and max values of a parameter."""

    self._cap.set(prop_id, 99999)
    max_ = int(self._cap.get(prop_id))
    self._cap.set(prop_id, -99999)
    min_ = int(self._cap.get(prop_id))
    if min_ == max_:
      self._cap.set(prop_id, 0)
      min_ = int(self._cap.get(prop_id))
    return min_, max_

  def _get_brightness(self) -> int:
    """Gets the image brightness."""

    return int(self._cap.get(cv2.CAP_PROP_BRIGHTNESS))

  def _get_contrast(self) -> int:
    """Gets the image contrast."""

    return int(self._cap.get(cv2.CAP_PROP_CONTRAST))

  def _get_hue(self) -> int:
    """Gets the image hue."""

    return int(self._cap.get(cv2.CAP_PROP_HUE))

  def _get_saturation(self) -> int:
    """Gets the image saturation."""

    return int(self._cap.get(cv2.CAP_PROP_SATURATION))

  def _set_brightness(self, brightness: int) -> None:
    """Sets the image brightness."""

    self._cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)

  def _set_contrast(self, contrast: int) -> None:
    """Sets the image contrast."""

    self._cap.set(cv2.CAP_PROP_CONTRAST, contrast)

  def _set_hue(self, hue: int) -> None:
    """Sets the image hue."""

    self._cap.set(cv2.CAP_PROP_HUE, hue)

  def _set_saturation(self, saturation: int) -> None:
    """Sets the image saturation."""

    self._cap.set(cv2.CAP_PROP_SATURATION, saturation)
