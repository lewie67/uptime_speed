import sqlite3
import time
import datetime
from datetime import timedelta
#AML#import random
#AML#import matplotlib.pyplot as plt 
#AML#import matplotlib.dates as mdates
#AML#from dateutil import parser
#AML#from matplotlib import style

import numpy as np
import array
from bokeh.io import curdoc
from bokeh.layouts import column, row, layout
from bokeh.models import ColumnDataSource, PreText
from bokeh.plotting import *

#AML#style.use('fivethirtyeight')

conn = sqlite3.connect('uptime_speed.db')
c = conn.cursor()
source = ColumnDataSource(data=dict(  x = np.empty(2), 
                                      y0 = np.empty(2), 
                                      y1 = np.empty(2),
                                      y2 = np.empty(2), 
                                      y3 = np.empty(2),
                                      y4 = np.empty(2),
                                      y5 = np.empty(2)))
now = datetime.datetime.now()
curr_time = now.strftime("%H:%M:%S")
stats = PreText(text=f"Updated: {curr_time}", width=500)

def update_speed_data():

  #AML#query = 'select epoch_time, ping_ms, up_speed, down_speed from uptime_speed'
  today = datetime.datetime.now()
  yesterday = today - timedelta(days=1)
  query = f"select epoch_time, ping_ms, up_speed, down_speed from uptime_speed where epoch_time between {yesterday.timestamp()} and {today.timestamp()} order by epoch_time asc"
  c.execute(query)
  data = c.fetchall()

  dates = []
  ping_speed = []
  up_speed = []
  down_speed = []


  for row in data:
    dates.append(datetime.datetime.fromtimestamp(row[0]))
    ping_speed.append(row[1])
    up_speed.append(row[2])
    down_speed.append(row[3])

  window_size = 5
  window = np.ones(window_size)/float(window_size)
  np_down_speed = np.array(down_speed)
  np_down_speed_avg = np.convolve(np_down_speed, window, 'valid')
  np_up_speed = np.array(up_speed)
  np_up_speed_avg = np.convolve(np_up_speed, window, 'valid')
  np_ping_speed = np.array(ping_speed)
  np_ping_speed_avg = np.convolve(np_ping_speed, window, 'valid')


  source.data['x'] = np.array(dates)
  source.data['y0'] = np_down_speed
  source.data['y1'] = np_down_speed_avg
  source.data['y2'] = np_up_speed
  source.data['y3'] = np_up_speed_avg
  source.data['y4'] = np_ping_speed
  source.data['y5'] = np_ping_speed_avg
  now = datetime.datetime.now()
  curr_time = now.strftime("%H:%M:%S")
  stats.text = f"Updated: {curr_time}"

update_speed_data()
TOOLS = "crosshair,pan,reset,save,wheel_zoom,xbox_select"
down_speed_plot = figure( tools=TOOLS, height=250, width=800, 
                          x_axis_type='datetime', 
                          tooltips=[("Download (Mbps)", "@y0")],
                          title="Download Speed")
down_speed_plot.xaxis.axis_label = 'Date/Time'
down_speed_plot.yaxis.axis_label = 'Mbps'
up_speed_plot = figure(   tools=TOOLS, height=250, width=800, 
                          x_axis_type='datetime', 
                          x_range=down_speed_plot.x_range,
                          tooltips=[("Upload (Mbps)", "@y2")],
                          title="Upload Speed")
up_speed_plot.xaxis.axis_label = 'Date/Time'
up_speed_plot.yaxis.axis_label = 'Mbps'
ping_speed_plot = figure( tools=TOOLS, height=250, width=800, 
                          x_axis_type='datetime', 
                          x_range=down_speed_plot.x_range,
                          tooltips=[("Ping (ms)", "@y4")],
                          title="Ping Speed")
ping_speed_plot.xaxis.axis_label = 'Date/Time'
ping_speed_plot.yaxis.axis_label = 'ms'
down_speed_plot.circle('x', 'y0', source=source, selection_color="orange", alpha=0.2)
down_speed_plot.line('x', 'y1', source=source, selection_color="orange")
up_speed_plot.circle('x', 'y2', source=source, selection_color="orange", alpha=0.2)
up_speed_plot.line('x', 'y3', source=source, selection_color="orange")
ping_speed_plot.circle('x', 'y4', source=source, selection_color="orange", alpha=0.2)
ping_speed_plot.line('x', 'y5', source=source, selection_color="orange")

curdoc().add_periodic_callback(update_speed_data, 10000)
#AML#while True:
#AML#widgets = column(stats)
plots = column(down_speed_plot, up_speed_plot, ping_speed_plot)
pl_layout = layout([
          [plots, stats],
         ])
curdoc().add_root(pl_layout)
curdoc().title = "Download, Upload, and Ping Speeds"