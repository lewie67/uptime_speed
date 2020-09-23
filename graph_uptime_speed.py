#pylint: disable=W0614
import sqlite3
import time
import datetime
from datetime import timedelta, date
import numpy as np
import pandas as pd
import array
from bokeh.io import curdoc
from bokeh.layouts import column, row, layout
from bokeh.models import ColumnDataSource, PreText, CustomJS, DateRangeSlider
from bokeh.plotting import * 

# Connect to DB
conn = sqlite3.connect('uptime_speed.db')
c = conn.cursor()
# Setup empty source to be shared. Allows for linked brushing
source = ColumnDataSource(data=dict(  x = np.empty(2), 
                                      y0 = np.empty(2), 
                                      y1 = np.empty(2),
                                      y2 = np.empty(2), 
                                      y3 = np.empty(2),
                                      y4 = np.empty(2),
                                      y5 = np.empty(2)))

today = datetime.datetime.now()
yesterday = today - timedelta(days=1)
date_range_slider = DateRangeSlider(  value = (yesterday, today),
                                      start = yesterday,
                                      end = today,
                                      step = 1000*60*60
)


# Generate current date for display
now = datetime.datetime.now()
curr_time = now.strftime("%H:%M:%S")
status = PreText(text=f"Updated: {curr_time}", width=500)
selected_data = PreText(text=f"Selected Graph Data")

# Query database for date boundries for slider
def update_date_boundaries():
  """Update the start and end datetimes for the date slider

  Queries the database and returns min and max datestamps available
  """
  # Pull last 24 hours worth
  query = "select min(epoch_time), max(epoch_time) from uptime_speed"
  c.execute(query)
  data = c.fetchall()
  date_range_slider.start = datetime.datetime.fromtimestamp(data[0][0])
  date_range_slider.end = datetime.datetime.fromtimestamp(data[0][1])
  
    
# Query database and load source with latest data
def update_speed_data():
  """Update the source data from the database for the graphs

  """

  ts = time.time()
  print("Running update_speed_data")
  start = date_range_slider.value_as_datetime[0]
  end = date_range_slider.value_as_datetime[1]
  query = f"select epoch_time, ping_ms, up_speed, down_speed from uptime_speed where epoch_time between {start.timestamp()} and {end.timestamp()} order by epoch_time asc"
  c.execute(query)
  data = pd.read_sql(query, con=conn, parse_dates=['epoch_time'])

  # Generate numpy arrays for series and averages for trend line
  window_size = 5
  window = np.ones(window_size)/float(window_size)


  # Set source data
  source.data['x'] = data['epoch_time']
  source.data['y0'] = data['down_speed']
  source.data['y1'] = np.convolve(data['down_speed'], window, 'valid')
  source.data['y2'] = data['up_speed']
  source.data['y3'] = np.convolve(data['up_speed'], window, 'valid')
  source.data['y4'] = data['ping_ms']
  source.data['y5'] = np.convolve(data['ping_ms'], window, 'valid')
  ts2 = time.time()
  print(f"Took {ts2-ts}")

  query = f"select count(*) from uptime_speed where epoch_time between {start.timestamp()} and {end.timestamp()}"
  c.execute(query)
  data = c.fetchall()
  selected_samples = data[0][0]

  query = f"select count(*) from uptime_speed"
  c.execute(query)
  data = c.fetchall()
  total_samples = data[0][0]
  # Update current time
  now = datetime.datetime.now()
  curr_time = now.strftime("%H:%M:%S")
  status.text = f"Updated: {curr_time}\nTotal Samples: {total_samples}\nSamples in Date Range: {selected_samples}"
  
  # End function

def selection_change(attrname, old, new):
  """Update text area with selected data from graphs

  """
  selected = source.selected.indices
  #AML#print(selected)
  text_output = u"Time Stamp\t\t\t\u2193 Mbps\t\u2191 Mbps\tRTT (ms)\n"
  for index in selected:
    text_output = text_output + f"{source.data['x'][index]}\t"
    text_output = text_output + f"{source.data['y0'][index]}\t"
    text_output = text_output + f"{source.data['y2'][index]}\t"
    text_output = text_output + f"{source.data['y4'][index]}\t\n"

  selected_data.text = text_output


update_date_boundaries()
# Generate first dataset
update_speed_data()

TOOLS = "crosshair,pan,reset,save,wheel_zoom,xbox_select"

# Generate download speed graph figure
down_speed_plot = figure( tools=TOOLS, height=250, width=800, 
                          x_axis_type='datetime', 
                          tooltips=[("Download (Mbps)", "@y0")],
                          title="Download Speed")
down_speed_plot.xaxis.axis_label = 'Date/Time'
down_speed_plot.yaxis.axis_label = 'Mbps'

# Generate upload speed graph figure
up_speed_plot = figure(   tools=TOOLS, height=250, width=800, 
                          x_axis_type='datetime', 
                          x_range=down_speed_plot.x_range,
                          tooltips=[("Upload (Mbps)", "@y2")],
                          title="Upload Speed")
up_speed_plot.xaxis.axis_label = 'Date/Time'
up_speed_plot.yaxis.axis_label = 'Mbps'

# Generate ping speed graph figure
ping_speed_plot = figure( tools=TOOLS, height=250, width=800, 
                          x_axis_type='datetime', 
                          x_range=down_speed_plot.x_range,
                          tooltips=[("Ping (ms)", "@y4")],
                          title="Ping Speed")
ping_speed_plot.xaxis.axis_label = 'Date/Time'
ping_speed_plot.yaxis.axis_label = 'ms'
#pylint: disable=E1121


# Plot datapoints and trendlines
down_speed_plot.circle('x', 'y0', source=source, selection_color="orange", alpha=0.2)
down_speed_plot.line('x', 'y1', source=source, selection_color="orange")
up_speed_plot.circle('x', 'y2', source=source, selection_color="orange", alpha=0.2)
up_speed_plot.line('x', 'y3', source=source, selection_color="orange")
ping_speed_plot.circle('x', 'y4', source=source, selection_color="orange", alpha=0.2)
ping_speed_plot.line('x', 'y5', source=source, selection_color="orange")

# Callback to update every 10 seconds
curdoc().add_periodic_callback(update_speed_data, 10000)

date_range_slider.on_change("value", lambda attr, old, new: update_speed_data)
source.selected.on_change("indices", selection_change)

# Generate layout
stats_controls = column(status, date_range_slider, selected_data)
plots = column(down_speed_plot, up_speed_plot, ping_speed_plot)
pl_layout = layout([
          [plots, stats_controls],
         ])
curdoc().add_root(pl_layout)
curdoc().title = "Download, Upload, and Ping Speeds"