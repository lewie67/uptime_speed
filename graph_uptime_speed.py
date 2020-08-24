import sqlite3
import time
import datetime
import random
import matplotlib.pyplot as plt 
import matplotlib.dates as mdates
from dateutil import parser
from matplotlib import style

import numpy as np
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Slider, TextInput
from bokeh.plotting import figure

style.use('fivethirtyeight')

conn = sqlite3.connect('uptime_speed.db')
c = conn.cursor()

def graph_data(y_axis_column):

  query = 'select epoch_time, ' + y_axis_column + ' from uptime_speed'
  c.execute(query)
  data = c.fetchall()

  dates = []
  values = []

  for row in data:
    dates.append(datetime.datetime.fromtimestamp(row[0]))
    values.append(row[1])

  source = ColumnDataSource(data=dict(x=dates, y=values))

  plot = figure(plot_height=400, plot_width=900, title="Speed Graph",
                tools="crosshair,pan,reset,save,wheel_zoom",
                x_axis_type='datetime')

  plot.line('x', 'y', source=source)
  return plot

down_speed = graph_data('down_speed')
up_speed = graph_data('up_speed')
ping_ms = graph_data('ping_ms')
curdoc().add_root(column(down_speed, up_speed, ping_ms))
curdoc().title = "Plot"