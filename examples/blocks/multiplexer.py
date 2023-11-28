# coding: utf-8

"""
This example demonstrates the use of the Multiplexer Block. It does not require
any specific hardware to run, but necessitates the matplotlib Python module to
be installed.

The Multiplexer Block takes inputs from several Blocks, and interpolates the
target labels so that their data is output on a common time basis. This is
especially useful for plotting one label from one Block vs another label from
a different Block. It is also useful for recording data coming from several
Block in a single file with the Recorder Block, as this Block can only save
data coming from one upstream Block at a time.

Here, the idea is to visually demonstrate how two signals with very different
data rates end up having a common time basis after interpolation by the
Multiplexer Block. Two labels are generated by two Generators at very different
frequencies, sent to a Multiplexer for interpolation, and the interpolated data
is sent to a Grapher for display.

After starting this script, just watch how the two interpolated labels are
displayed at the same frequency by the Grapher, whereas they have originally
very different frequencies. You can try to change the different frequencies and
see what the result is. This demo ends after 22s. You can also hit CTRL+C to
stop it earlier, but it is not a clean way to stop Crappy.
"""

import crappy

if __name__ == '__main__':

  # This Generator generates a Ramp signal at a high frequency and sends it to
  # the Multiplexer Block for interpolation
  gen_fast = crappy.blocks.Generator(
      # Generating an increasing Ramp signal with a speed of 1
      ({'type': 'Ramp', 'speed': 1, 'condition': 'delay=20', 
        'init_value': 0},),
      freq=50,  # This Generator outputs signal at a moderately high frequency
      cmd_label='cmd_slow',  # The label carrying the output signal

      # Sticking to default for the other arguments
  )

  # This Generator generates a Ramp signal at a low frequency and sends it to
  # the Multiplexer Block for interpolation
  gen_slow = crappy.blocks.Generator(
      # Generating a decreasing Ramp signal with a speed of -1
      ({'type': 'Ramp', 'speed': -1, 'condition': None, 'init_value': 0},),
      freq=3,  # This Generator outputs signal at a very low frequency
      cmd_label='cmd_fast',  # The label carrying the output signal

      # Sticking to default for the other arguments
  )

  # This Multiplexer Block interpolates the data it receives from the
  # Generators and outputs the interpolated values on a common time basis. This
  # way, both the 'cmd_slow' and 'cmd_fast' labels that originally have very
  # different data rates are now available on a common time basis
  multi = crappy.blocks.Multiplexer(
      # The names of the labels to process and output, all the other labels are
      # dropped
      out_labels=('cmd_slow', 'cmd_fast'),
      interp_freq=30,  # The target data rate of the interpolated values
      freq=20,  # The looping frequency of the Block, useless to set it higher
      # than the interpolation frequency

      # Sticking to default for the other arguments
  )

  # This Grapher displays the interpolated data transmitted by the Multiplexer
  # Block. The data rates of the 'cmd_slow' and 'cmd_fast' labels are now
  # identical, whereas they were originally very different !
  graph = crappy.blocks.Grapher(
      # The names of the labels to plot on the graph
      ('t(s)', 'cmd_slow'), ('t(s)', 'cmd_fast'),
      freq=2,  # Updating the graph twice per second
      interp=False,  # Displaying the data points only, no lines, to clearly
      # distinguish them
      length=100,  # Only displaying the last 100 received values, so that the
      # data points remain always clearly visible

      # Sticking to default for the other arguments
  )

  # Linking the Block so that the information is correctly sent and received
  crappy.link(gen_slow, multi)
  crappy.link(gen_fast, multi)
  crappy.link(multi, graph)

  # Mandatory line for starting the test, this call is blocking
  crappy.start()
