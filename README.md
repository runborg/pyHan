# pyHan

Simple Python library to decode data from the HAN port on Norwegian electricity meters.

This library is based on the C library found here: https://drive.google.com/drive/folders/0B3ZvFI0Dg1TDbDBzMU02cnU0Y28


The library tries to make is realy easy to decode data on the HAN port.

Simple serial HAN decoder:
```python
from HAN import readHan
import serial

with serial.Serial('/dev/ttyUSB0', 2400, timeout=5) as ser:
    while True:
        han = readHan(ser)
        print("{} Watt".format(han.data["act_pow_pos"]))
``` 


Decode messages from file:
```python
from HAN import readHan
with open(file, "rb") as ser
    while True:
    try:
        han = readHan(ser)
        print("{} Watt".format(han.data["act_pow_pos"]))
    except EOFError as e:
        # End Of File
        break
    except Exception as e:
        # Unable to decode message
        continue

```
