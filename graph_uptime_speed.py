#pylint: disable=W0614
import sqlite3
import time
import datetime
from datetime import timedelta, date
import numpy as np
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

# Generate current date for display
now = datetime.datetime.now()
curr_time = now.strftime("%H:%M:%S")
stats = PreText(text=f"Updated: {curr_time}", width=500)

# Query database for date boundries for slider
def get_date_boundaries():

  # Pull last 24 hours worth
  query = "select min(epoch_time), max(epoch_time) from uptime_speed"
  c.execute(query)
  data = c.fetchall()
  return data[0][0], data[0][1]
    
# Query database and load source with latest data
def update_speed_data():

  # Pull last 24 hours worth
  today = datetime.datetime.now()
  yesterday = today - timedelta(days=1)
  query = f"select epoch_time, ping_ms, up_speed, down_speed from uptime_speed where epoch_time between {yesterday.timestamp()} and {today.timestamp()} order by epoch_time asc"
  c.execute(query)
  data = c.fetchall()

  dates = []
  ping_speed = []
  up_speed = []
  down_speed = []


  # Put each series into an array 
  for row in data:
    dates.append(datetime.datetime.fromtimestamp(row[0]))
    ping_speed.append(row[1])
    up_speed.append(row[2])
    down_speed.append(row[3])

  # Generate numpy arrays for series and averages for trend line
  window_size = 5
  window = np.ones(window_size)/float(window_size)
  np_down_speed = np.array(down_speed)
  np_down_speed_avg = np.convolve(np_down_speed, window, 'valid')
  np_up_speed = np.array(up_speed)
  np_up_speed_avg = np.convolve(np_up_speed, window, 'valid')
  np_ping_speed = np.array(ping_speed)
  np_ping_speed_avg = np.convolve(np_ping_speed, window, 'valid')


  # Set source data
  source.data['x'] = np.array(dates)
  source.data['y0'] = np_down_speed
  source.data['y1'] = np_down_speed_avg
  source.data['y2'] = np_up_speed
  source.data['y3'] = np_up_speed_avg
  source.data['y4'] = np_ping_speed
  source.data['y5'] = np_ping_speed_avg

  # Update current time
  now = datetime.datetime.now()
  curr_time = now.strftime("%H:%M:%S")
  stats.text = f"Updated: {curr_time}"
  
  # End function

# Generate first dataset
update_speed_data()
# Tools for each graph
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

# Plot download datapoints
down_speed_plot.circle('x', 'y0', source=source, selection_color="orange", alpha=0.2)
# Plot download trendline
down_speed_plot.line('x', 'y1', source=source, selection_color="orange")
# Plot upload datapoints
up_speed_plot.circle('x', 'y2', source=source, selection_color="orange", alpha=0.2)
# Plot upload trendline
up_speed_plot.line('x', 'y3', source=source, selection_color="orange")
# Plot ping datapoints
ping_speed_plot.circle('x', 'y4', source=source, selection_color="orange", alpha=0.2)
# Plot ping trendline
ping_speed_plot.line('x', 'y5', source=source, selection_color="orange")

# Callback to update every 10 seconds
curdoc().add_periodic_callback(update_speed_data, 10000)

earliest, latest = get_date_boundaries()
today = datetime.datetime.now()
yesterday = today - timedelta(days=1)

date_range_slider = DateRangeSlider(  value = (yesterday, today),
                                      start = datetime.datetime.fromtimestamp(earliest),
                                      end = datetime.datetime.fromtimestamp(latest))

date_range_slider.js_on_change("value", CustomJS( code = """
  console.log('date_range_slider: value=' + this.value, this.toString())
"""))

# Generate layout
stats_controls = column(stats, date_range_slider)
plots = column(down_speed_plot, up_speed_plot, ping_speed_plot)
pl_layout = layout([
          [plots, stats_controls],
         ])
curdoc().add_root(pl_layout)
curdoc().title = "Download, Upload, and Ping Speeds"