# coding: utf-8
# Blocks are classes, running indefinitely in a single process.
# Some of them are already implemented (see the reference manual),
# but you can also implement your own.

from .autoDrive import AutoDrive
from .camera import Camera
from .client import Client
from .dashboard import Dashboard
from .discorrel import DISCorrel
from .displayer import Displayer
from .disve import DISVE
from .drawing import Drawing
from .fake_machine import Fake_machine
from .generator import Generator
from .gpucorrel import GPUCorrel
from .gpuve import GPUVE
from .grapher import Grapher
from .gui import GUI
from .hdf_saver import Hdf_saver
from .ioblock import IOBlock
from .machine import Machine
from .masterblock import MasterBlock
from .mean import Mean
from .multiplex import Multiplex
from .pid import PID
from .reader import Reader
from .saver import Saver
from .server import Server
from .sink import Sink
from .videoExtenso import Video_extenso
