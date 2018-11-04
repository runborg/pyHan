from HAN import hexprint, readHan
import serial
import json
import datetime

def default_serializer(o):
      if type(o) is datetime.date or type(o) is datetime.datetime:
              return o.isoformat()

buff = {}
with serial.Serial('/dev/ttyUSB0', 2400, timeout=5) as ser:
    try:
        while True:
            han = readHan(ser)
            for item in han.data:
                buff[item] = han.data[item]
            print("\033[H\033[J")
            print(json.dumps(buff, 
                            indent=4,
                            default=default_serializer))
    except EOFError as e:
            # We are on serial.. EOF meens no data, but it might come? :) 
            print("EOF")
            pass
