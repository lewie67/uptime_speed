
# https://github.com/sivel/speedtest-cli
import speedtest as st
import sqlite3
import time
import syslog


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
    ping = 0

  return (up, ping, download_mbs, upload_mbs)


def update_db(internet_speeds):
  # Get today's date in the form Month/Day/Year
  curr_time = time.time()
  # Connect to sqlite3 db
  conn = sqlite3.connect('/home/alewis/projects/uptime_speed/uptime_speed.db')
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


syslog.syslog("Running uptime_speed")
new_speeds = get_new_speeds()
syslog.syslog("Updating Database from uptime_speed")
update_db(new_speeds)
syslog.syslog("Finished running uptime_speed")