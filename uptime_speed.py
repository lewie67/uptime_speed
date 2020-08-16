
# https://github.com/sivel/speedtest-cli
import speedtest as st
import pandas as pd
from datetime import datetime
import sqlite3
import time


def get_new_speeds():
  up = 1
  download_mbs = 0
  upload_mbs = 0
  speed_test = 0
  
  try:
    speed_test = st.Speedtest()
    speed_test.get_best_server()

   # Get ping (miliseconds)
    ping = speed_test.results.ping
    # Perform download and upload speed tests (bits per second)
    download = speed_test.download()
    upload = speed_test.upload()

    # Convert download and upload speeds to megabits per second
    download_mbs = round(download / (10**6), 2)
    upload_mbs = round(upload / (10**6), 2)
  except:
    up = 0
    download_mbs = 0
    upload_mbs = 0
    ping = 1800000

  return (up, ping, download_mbs, upload_mbs)


def update_db(internet_speeds):
  # Get today's date in the form Month/Day/Year
  #AML#date_today = datetime.today().strftime("%m/%d/%Y")
  curr_time = time.time()
  # File with the dataset
  #AML#csv_file_name = "internet_speeds_dataset.csv"
  conn = sqlite3.connect('uptime_speed.db')
  c = conn.cursor()

  insert_statement =  'INSERT INTO uptime_speed VALUES(' + \
                      str(curr_time) + ',' + \
                      str(internet_speeds[0]) + ',' + \
                      str(internet_speeds[1]) + ',' + \
                      str(internet_speeds[2]) + ',' + \
                      str(internet_speeds[3]) + ');'

  # Load the CSV to update
  try:
    print(insert_statement)
    c.execute(insert_statement)
    conn.commit()
    # If there's an error, assume the file does not exist and create\
    # the dataset from scratch
  except:
    create_table = 'create table uptime_speed(epoch_time real, up integer, ping_ms real, up_speed real, down_speed real);'
    c.execute(create_table)
    c.execute(insert_statement)
    conn.commit()


new_speeds = get_new_speeds()
update_db(new_speeds)
#AML#collect_internet_speeds.py hosted with ❤ by GitHub