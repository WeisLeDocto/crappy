# coding: utf-8

"""
This example demonstrates the instantiation of a custom Camera object in
Crappy, with the integration of a trigger setting. This example is based
on the custom_camera_basic.py, that should first be read for a better
understanding. It does not require any hardware to run, but necessitates the
Pillow and opencv-python Python modules to be installed.

In Camera objects, Crappy offers the possibility to easily implement a trigger
setting. Using this setting, the user can choose in the configuration window
between the free run mode, the hardware trigger mode, or to set the hardware
trigger mode after closing the configuration window. With this latter option,
the camera can be tuned in free run mode and be ready for the test in hardware
trigger mode. The addition of a trigger setting only requires calling one
method, as demonstrated in this example.

Here, a very simple Camera object is instantiated, and driven by a Camera Block
that displays the acquired images. The Camera object features a trigger
setting, that lets the user select the trigger mode in the configuration
window. Because there's no actual hardware involved, the hardware trigger mode
is emulated by only allowing one image acquisition per second. The goal here is
to show how to implement a trigger setting in Camera objects.

After starting this script, a configuration window appears in which you can see
the generated images. You can only tune the trigger mode setting. Select one
and close the configuration window to start the test and see what its effect
is. In Free run mode, the image rate should be close to 30 FPS both in the
configuration window and in the displayer windows, no trigger is applied. In
Hardware trigger mode, the configuration window should be unresponsive and only
update once every second, same with the displayer window : the hardware trigger
mode is always applied. And in Hdw after config trigger mode, the configuration
window should run normally at ~30 FPS, but the displayer window should only
update at ~1 Hz. The Free run mode remains active until the configuration
window is closed, and the Camera is then switched to Hardware trigger mode.
This demo never ends and must be stopped by hitting CTRL+C.
"""

import crappy
import numpy as np
import numpy.random as rd
from typing import Tuple
from time import time, sleep


class CustomCam(crappy.camera.Camera):
  """This class demonstrates the instantiation of a custom Camera object in
  Crappy, with the instantiation of a trigger setting.

  In the open method, the add_trigger_setting method is called for adding a
  trigger setting to the Camera object. By tuning this setting in the
  configuration window, the user can choose to let the camera run in free run
  mode, to switch it to hardware trigger mode after closing the configuration
  window, or to directly switch it to hardware trigger mode.

  This class is based on the one defined in custom_camera_basic.py, please
  refer to that example for more information.
  """

  def __init__(self) -> None:
    """Almost the same as in custom_camera_basic.py.

    Here, we define a buffer and a flag that serve later for emulating the
    trigger hardware setting being set on a camera.
    """

    # Mandatory line usually at the very beginning of the __init__ method
    super().__init__()

    self._trigger_mode: str = 'Free run'
    self._run: bool = True

  def open(self, **kwargs) -> None:
    """Compared to the custom_camera_basic.py example, we define here a
    trigger setting using the add_trigger_setting method.

    Unlike the settings defined in the custom_camera_settings.py example, the
    trigger setting is handled internally and in a standardized way.

    It is possible to either choose to let the camera run in free run mode, or
    to have it run in the hardware trigger mode, or to only switch to the
    hardware trigger mode after the configuration window is closed. With this
    latter option, it is easier for the user to adjust the settings even if the
    trigger frequency is low. Or if the trigger signal is generated by Crappy,
    in which case it only starts after the configuration window is closed !

    Since this example is designed to run without hardware, the hardware
    trigger is just replaced by a delay of 1s to simulate a hardware trigger
    signal running at 1Hz.
    """

    # Adding a trigger setting, handled differently by Crappy than the other
    # types of settings
    self.add_trigger_setting(getter=self._get_trigger_mode,
                             setter=self._set_trigger_mode)

    # This line is mandatory here for first applying the trigger setting
    self.set_all(**kwargs)

  def get_image(self) -> Tuple[float, np.ndarray]:
    """Compared to the one in custom_camera_basic.py, this method returns the
    same images but with a delay if in Hardware trigger mode.

    Since this example runs without any hardware, it emulates the hardware
    trigger by only allowing one image per second in Hardware trigger mode.
    """

    # If not in a free run mode, assuming a hardware trig is issued each ~1s
    if not self._run:
      sleep(1)

    return time(), rd.randint(low=0, high=256, size=(480, 640), dtype='uint8')

  def close(self) -> None:
    """Same as in custom_camera_basic.py, nothing to do here."""

    pass

  def _set_trigger_mode(self, mode: str) -> None:
    """This method sets the current trigger mode.

    Normally it would set this parameter directly on hardware, but this demo
    was designed to run completely virtually.
    """

    # Setting the flag telling whether the camera should return images
    if mode in ('Free run', 'Hdw after config'):
      self._run = True
    else:
      self._run = False

    # Storing the selected mode
    self._trigger_mode = mode

  def _get_trigger_mode(self) -> str:
    """This method returns the current trigger mode.

    Normally it would read this parameter directly from hardware, but this demo
    was designed to run completely virtually.
    """

    return self._trigger_mode


if __name__ == '__main__':

  # This Camera Block drives the CustomCam Camera object that we just created.
  # It acquires images and displays them in a dedicated Displayer window. The
  # user can choose in which trigger mode the Camera runs.
  cam = crappy.blocks.Camera(
      'CustomCam',  # The name of the custom Camera that was just written
      config=True,  # easier to set it to True when possible
      display_images=True,  # Displaying the images to show how they look
      displayer_framerate=30,  # Setting same framerate as acquisition
      freq=30,  # Lowering the frequency because it's just a demo
      save_images=False,  # No need to record images in this example

      # Sticking to default for the other arguments
  )

  # Mandatory line for starting the test, this call is blocking
  crappy.start()
