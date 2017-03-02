import serial
from threading import Thread
import Tkinter as tk
import tkFont
from Queue import Queue as Queue_threading, Empty
from time import sleep, time
from collections import OrderedDict
from multiprocessing import Process, Queue
from ast import literal_eval


class MonitorFrame(tk.Frame):
  def __init__(self, parent, *args, **kwargs):
    """
    A frame that displays everything enters the serial port.
    Args:
      arduino: serial.Serial of arduino board.
      width: size of the text frame
      title: the title of the frame.
      fontsize: size of font inside the text frame.
    """
    tk.Frame.__init__(self, parent)
    self.grid()
    self.total_width = kwargs.get('width', 100 * 8 / 10)
    self.arduino = kwargs.get("arduino")
    self.queue = kwargs.get("queue")
    self.enabled_checkbox = tk.IntVar()
    self.enabled_checkbox.set(1)

    self.create_widgets(**kwargs)

  def create_widgets(self, **kwargs):
    """
    Widgets shown : the title with option
    """
    self.top_frame = tk.Frame(self)
    tk.Label(self.top_frame, text=kwargs.get('title', '')).grid(row=0, column=0)

    tk.Checkbutton(self.top_frame,
                   variable=self.enabled_checkbox,
                   text="Display?").grid(row=0, column=1)
    self.serial_monitor = tk.Text(self,
                                  relief="sunken",
                                  height=int(self.total_width / 10),
                                  width=int(self.total_width),
                                  font=tkFont.Font(size=kwargs.get("fontsize",
                                                                   13)))

    self.top_frame.grid(row=0)
    self.serial_monitor.grid(row=1)

  def update_widgets(self, *args):
    if self.enabled_checkbox.get():
      self.serial_monitor.insert("0.0", args[0])  # To insert at the top
    else:
      pass


class SubmitSerialFrame(tk.Frame):
  def __init__(self, parent, *args, **kwargs):
    tk.Frame.__init__(self, parent)
    self.grid()
    self.total_width = kwargs.get("width", 100)
    self.queue = kwargs.get("queue")

    self.create_widgets(**kwargs)

  def create_widgets(self, **kwargs):
    self.input_txt = tk.Entry(self,
                              width=self.total_width * 5 / 10,
                              font=tkFont.Font(size=kwargs.get("fontsize", 13)))
    self.submit_label = tk.Label(self, text='',
                                 width=1,
                                 font=tkFont.Font(
                                   size=kwargs.get("fontsize", 13)))
    self.submit_button = tk.Button(self,
                                   text='Submit',
                                   command=self.update_widgets,
                                   width=int(self.total_width * 0.5 / 10),
                                   font=tkFont.Font(
                                     size=kwargs.get("fontsize", 13)))

    self.input_txt.bind('<Return>', self.update_widgets)
    self.input_txt.bind('<KP_Enter>', self.update_widgets)

    # Positioning
    self.input_txt.grid(row=0, column=0, sticky=tk.W)
    self.submit_label.grid(row=0, column=1)
    self.submit_button.grid(row=0, column=2, sticky=tk.E)

  def update_widgets(self, *args):
    try:
      message = self.queue.get(block=False)
    except Empty:
      message = self.input_txt.get()
    self.input_txt.delete(0, 'end')
    if len(message) > int(self.total_width / 4):
      self.input_txt.configure(width=int(self.total_width * 5 / 10 - len(
        message)))
    else:
      self.input_txt.configure(width=int(self.total_width * 5 / 10))
    self.submit_label.configure(width=len(message))
    self.submit_label.configure(text=message)
    self.queue.put(message)


class MinitensFrame(tk.Frame):
  def __init__(self, parent, *args, **kwargs):
    tk.Frame.__init__(self, parent)
    self.grid()
    self.mode = tk.IntVar()
    self.modes = [('stop', 0),
                  ('traction', 1),
                  ('compression', 2),
                  ('cycle', 3)]
    self.create_widgets(**kwargs)
    self.queue = kwargs.get("queue")

  def create_widgets(self, **kwargs):
    self.minitens_frame_radiobuttons = tk.Frame(self)
    for index, value in enumerate(self.modes):
      tk.Radiobutton(self.minitens_frame_radiobuttons, text=value[0],
                     value=value[1], variable=self.mode).grid(row=index,
                                                              sticky=tk.W)

    self.vitesse_frame = tk.Frame(self)
    self.vitesse_parameter = tk.Entry(self.vitesse_frame)
    self.vitesse_parameter.grid(row=1)
    tk.Label(self.vitesse_frame, text="Vitesse(0..255)").grid(row=0)

    self.boucle_frame = tk.Frame(self)
    self.boucle_parameter = tk.Entry(self.boucle_frame)
    self.boucle_parameter.grid(row=1)
    tk.Label(self.boucle_frame, text="Temps(ms)").grid(row=0)

    self.buttons_frame = tk.Frame(self)
    tk.Button(self.buttons_frame,
              text="SUBMIT",
              bg="green",
              relief="raised",
              height=4, width=10,
              command=lambda: self.update_widgets("SUBMIT")
              ).grid(row=0, column=0)

    tk.Button(self.buttons_frame,
              text="STOP",
              bg="red",
              relief="raised",
              height=4, width=10,
              command=lambda: self.update_widgets("STOP")
              ).grid(row=0, column=1)

    self.minitens_frame_radiobuttons.grid(row=0, column=0)
    self.vitesse_frame.grid(row=0, column=1)
    self.boucle_frame.grid(row=0, column=2)
    self.buttons_frame.grid(row=0, column=4)

  def update_widgets(self, *args):
    if args[0] == "STOP":
      message = str({"mode": 0,
                     "vitesse": 255,
                     "boucle": 0})
    else:
      message = str({"mode": self.mode.get(),
                     "vitesse": self.vitesse_parameter.get(),
                     "boucle": self.boucle_parameter.get()})

    self.queue.put(message)


class ArduinoHandler(object):
  def __init__(self, *args, **kwargs):
    def collect_serial(arduino, queue):
      while True:
        queue.put(arduino.readline())

    self.port = args[0]
    self.baudrate = args[1]
    self.queue_process = args[2]
    self.arduino_ser = serial.Serial(port=self.port,
                                     baudrate=self.baudrate)
    self.collect_serial_queue = Queue_threading()
    self.submit_serial_queue = Queue_threading()

    self.collect_serial_threaded = Thread(target=collect_serial,
                                          args=(self.arduino_ser,
                                                self.collect_serial_queue))
    self.collect_serial_threaded.daemon = True
    self.init_main_window()
    self.collect_serial_threaded.start()
    self.main_loop()

  def init_main_window(self):
    self.root = tk.Tk()
    self.root.resizable(width=False, height=False)
    self.root.title("Arduino Minitens Command")
    self.monitor_frame = MonitorFrame(self.root,
                                 title="Arduino on port %s "
                                       "baudrate %s" % (self.port,
                                                        self.baudrate))

    self.submit_frame = SubmitSerialFrame(self.root,
                                       queue=self.submit_serial_queue)
    self.minitens_frame = MinitensFrame(self.root,
                                       queue=self.submit_serial_queue)
    self.monitor_frame.grid()
    self.submit_frame.grid()
    self.minitens_frame.grid()
  def main_loop(self):
    while True:
      try:
        message = self.collect_serial_queue.get(block=False)
        self.monitor_frame.update_widgets(message)
        self.queue_process.put(message)
        to_send = self.submit_serial_queue.get(block=False)

        print('to send:', to_send)
        self.arduino_ser.write(to_send)

        self.root.update()
        sleep(0.01)
      except Empty:
        self.root.update()
        sleep(0.01)
      except KeyboardInterrupt:
        break


class Arduino(object):
  def __init__(self, *args, **kwargs):
    self.port = kwargs.get("port", "/dev/ttyACM0")
    self.baudrate = kwargs.get("baudrate", 9600)
    self.queue_get_data = Queue()
    self.arduino_handler = Process(target=ArduinoHandler,
                                   args=(self.port,
                                         self.baudrate,
                                         self.queue_get_data))
    self.arduino_handler.start()
    # Initialize the queue
    while True:
      try:
        print("glushing")
        getting = literal_eval(self.queue_get_data.get())
        if isinstance(getting, dict):
          break
      except:
        continue

  def get_data(self, mock=None):
    retrieved_from_arduino = literal_eval(self.queue_get_data.get())
    return time(), OrderedDict(retrieved_from_arduino)

  def close(self):
    self.arduino_handler.terminate()
