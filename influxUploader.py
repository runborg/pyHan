from influxdb import InfluxDBClient
from HAN import readHan
from time import sleep
import traceback
import serial
import sys
from pprint import pprint
import datetime
import argparse


parser = argparse.ArgumentParser(prog='serialInflux')
parser.add_argument('--serialport', default='/dev/ttyUSB0')
parser.add_argument('--influxserver', default='127.0.0.1')
parser.add_argument('--username', default='amsreader')
parser.add_argument('--password', default='amsreader')
parser.add_argument('--database', default='amsreader')
parser.add_argument('--meterid', default='ams')
args = parser.parse_args()

with serial.Serial(args.serialport, 2400, timeout=5) as ser:
        influx = InfluxDBClient(host=args.influxserver, 
                                port=8086, 
                                use_udp=False,
                                database=args.database, 
                                username=args.username, 
                                password=args.password)
        while True:
            try:
                print("Reading HAN")
                han = readHan(ser)

                #measure = [{"measurement": "amsReadout",
                #           "tags": { "user": "runar"},
                #           "time": int(han.data["timestamp"].strftime("%s")),
                #           "fields": { "watt": han.data["act_pow_pos"]},
                #           }]
                #   "time": "{:%Y-%m-%dT%H:%M:%SZ}".format(han.data["timestamp"]),
                measure = [{"measurement": "amsReadout",
                            "tags": { "meter": args.meterid},
                            "time": int(datetime.datetime.now().strftime("%s")),
                            "fields": { "watt": han.data["act_pow_pos"]},
                           }]
                        
                pprint(measure)
                print("Sending to Influx")
                influx.write_points(measure, time_precision='s')
            except (KeyboardInterrupt, SystemExit):
                break
            except Exception as e:
                sys.stderr.write(traceback.format_exc())
                sleep(1)
                continue
