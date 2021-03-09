from influxdb import InfluxDBClient
from influxdb.client import InfluxDBClientError
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

args = parser.parse_args()

with serial.Serial(args.serialport, 2400, timeout=5, 
                   bytesize=serial.EIGHTBITS,
                   parity=serial.PARITY_EVEN,
                   stopbits=serial.STOPBITS_ONE
                   ) as ser:
        influx = InfluxDBClient(host=args.influxserver, 
                                port=8086, 
                                use_udp=False,
                                database=args.database, 
                                username=args.username, 
                                password=args.password)
        while True:
            try:
                #print("Reading HAN")
                han = readHan(ser)

                #measure = [{"measurement": "amsReadout",
                #           "tags": { "user": "runar"},
                #           "time": int(han.data["timestamp"].strftime("%s")),
                #           "fields": { "watt": han.data["act_pow_pos"]},
                #           }]
                #   "time": "{:%Y-%m-%dT%H:%M:%SZ}".format(han.data["timestamp"]),
                measure = [{"measurement": "amsReadout",
                           "tags": { "user": "runar"},
                           "time": int(datetime.datetime.now().strftime("%s")),
                           "fields": { "watt": han.data["act_pow_pos"]},
                           }]
                        
                #pprint(measure)
                #pprint(han.data)
                #print("Sending to Influx")
                influx.write_points(measure, time_precision='s')

                fields = dict(han.data)
                ts = fields["timestamp"]
                del fields["timestamp"]
                if "datetime" in fields:
                    del fields["datetime"] 
                if "curr_l1" in fields:
                    fields["curr_l1"] = float(fields["curr_l1"]) / 1000
                if "curr_l2" in fields:
                    fields["curr_l2"] = float(fields["curr_l2"]) / 1000
                if "curr_l3" in fields:
                    fields["curr_l3"] = float(fields["curr_l3"]) / 1000
                if "volt_l1" in fields:
                    fields["volt_l1"] = float(fields["volt_l1"]) / 10
                if "volt_l2" in fields:
                    fields["volt_l2"] = float(fields["volt_l2"]) / 10
                if "volt_l3" in fields:
                    fields["volt_l3"] = float(fields["volt_l3"]) / 10
                if "act_pow_neg" in fields:
                    fields["act_pow_neg"] = float(fields["act_pow_neg"] / 1000)
                if "act_pow_pos" in fields:
                    fields["act_pow_pos"] = float(fields["act_pow_pos"] / 1000)
                if "react_pow_neg" in fields:
                    fields["react_pow_neg"] = float(fields["react_pow_neg"] / 1000)
                if "react_pow_pos" in fields:
                    fields["react_pow_pos"] = float(fields["react_pow_pos"] / 1000)
                if "act_energy_pa" in fields:
                    fields["act_energy_pa"] = float(fields["act_energy_pa"] / 1000)
                m = [{"measurement": "AMS",
                      "tags": { "user": "runar"},
                      "fields": fields,
                      }]
                #"time": int(ts.strftime("%s")),
                #pprint(m)
                #pprint(datetime.datetime.now())
                #pprint(ts)
                influx.write_points(m, time_precision='s')
                #print("OK")
            except (KeyboardInterrupt, SystemExit):
                break
            except InfluxDBClientError as e:
                print(datetime.datetime.now())
                sys.stderr.write(traceback.format_exc())
                print("han.data:")
                pprint(han.data)
            except Exception as e:
                sys.stderr.write(traceback.format_exc())
                sleep(1)
                continue
