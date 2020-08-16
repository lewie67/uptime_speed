import sqlite3
import time
import datetime
import random
import matplotlib.pyplot as plt 
import matplotlib.dates as mdates
from dateutil import parser
from matplotlib import style
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
    #AML#epoch_date = parser.parse(str(row[0]))
    epoch_date= row[0]
    date_string = str(datetime.datetime.fromtimestamp(epoch_date).strftime('%Y-%m-%d %H:%M:%S'))
    dates.append(date_string)
    values.append(row[1])
  
  plt.plot_date(dates, values, '-')
  plt.ion()
  plt.draw()
  plt.pause(0.001)

columns = ['ping_ms', 'down_speed', 'up_speed']
for column in columns:
  graph_data(column)
input("Press [enter] to continue.")