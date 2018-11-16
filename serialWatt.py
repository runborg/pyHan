from HAN import readHan
import serial

with serial.Serial('/dev/ttyUSB0', 2400, timeout=5) as ser:
        while True:
            han = readHan(ser)
            print("{} Watt".format(han.data["act_pow_pos"]))
