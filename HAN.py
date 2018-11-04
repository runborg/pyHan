from time import sleep
from datetime import datetime as dt
from struct import unpack
from pprint import pprint
import sys
class HAN_message():
    def __init__(self, buff):
        if buff[0]  != 0x09:
            raise ValueError("Unknown message type")
        # Message header
        self._headerlen = buff[1] 
        self._year = int.from_bytes(buff[2:4], byteorder='big')
        self._month = buff[4]
        self._day = buff[5]
        self._hour = buff[7]
        self._min = buff[8]
        self._sec = buff[9]
        self.timestamp = dt(self._year, self._month, self._day, self._hour, self._min, self._sec)
        
        self.header = buff[0:self._headerlen]
        message_start = self._headerlen + 2

        self._data = ()
        if buff[message_start] == 0x02:
            self._numitems = buff[message_start +1]
        else:
            raise ValueError("Unable to detect number of items in message")

        offset = message_start + 2
        
        self.items = []
        #while offset < len(buff):
        nr = 0
        while nr < self._numitems:
            nr += 1
            #print("BUFFPOS: %d/%d  %d/%d" % (nr, self._numitems, offset, len(buff)))
            if buff[offset] == 0x09:
                numbytes = buff[offset+1]
                try:
                    #print(repr(buff[offset+2:offset+2+numbytes]))
                    if self._numitems == 18 and nr == 14:
                       self.items.append(dt(int.from_bytes(buff[offset+2:offset+4], byteorder='big'),  # Year
                                            buff[offset+4],           # Month
                                            buff[offset+5],           # Day
                                            buff[offset+7],           # Hour
                                            buff[offset+8],           # Minute
                                            buff[offset+9]))          # Second
                       #print(self.items[-1])
                    else:
                        self.items.append(buff[offset+2:offset+2+numbytes].decode() )
                except UnicodeDecodeError as e:
                    print("Unable to decode string: nr: %d/%d len: %d %s" % (nr, self._numitems, numbytes, hexprint(buff[offset+2:offset+2+numbytes])))
                    self.items.append("")
                offset += 2+numbytes

            elif buff[offset] == 0x06:
                self.items.append(int.from_bytes(buff[offset+1:offset+5], byteorder='big'))
                offset += 1+4
            
            else:
                #print("unknown value: %s" % hex(buff[offset]))

                raise ValueError("Unable to fetch value from segment nr %d/%d (%s) \n%s" % (nr, self._numitems, hexprint(buff[offset]) ,hexprint(buff, header="BUFF")))
            #print("collected element %s" % self.items[-1])

        if self._numitems == 1:
            self.type = 1
            self.data = dict(zip(["act_pow_pos"], self.items))

        elif self._numitems ==9:
            self.type = 2
            self.data = dict(zip(["obis_list_version", "gs1", "meter_model", 
                                  "act_pow_pos","act_pow_neg", 
                                  "react_pow_pos", "react_pow_neg", 
                                  "curr_l1", 
                                  "volt_l1"],self.items))
            self.data["curr_l2"] = None
            self.data["curr_l3"] = None
            self.data["volt_l2"] = None
            self.data["volt_l3"] = None
        elif self._numitems == 13:
            self.type = 2
            self.data = dict(zip(["obis_list_version", "gs1", "meter_model",
                                  "act_pow_pos", "act_pow_neg", 
                                  "react_pow_pos", "react_pow_neg", 
                                  "curr_l1", "curr_l2", "curr_l3", 
                                  "volt_l1", "volt_l2", "volt_l3"],self.items))
        elif self._numitems == 14:
            self.type = 2
            self.data = dict(zip(["obis_list_version", "gs1", "meter_model",
                                  "act_pow_pos", "act_pow_neg",
                                  "react_pow_pos", "react_pow_neg",
                                  "curr_l1",
                                  "volt_l1", 
                                  "datetime",
                                  "act_energy_pos", "act_energy_neg",
                                  "react_energy_pos", "react_energy_neg"],self.items))
        elif self._numitems== 18:
            self.type = 2
            self.data = dict(zip(["obis_list_version", "gs1", "meter_model",
                                  "act_pow_pos", "act_pow_neg",
                                  "react_pow_pos", "react_pow_neg",
                                  "curr_l1", "curr_l2", "curr_l3",
                                  "volt_l1", "volt_l2", "volt_l3",
                                  "datetime", 
                                  "act_energy_pa", "act_energy_ma", "act_energy_pr", "act_energy_mr"],self.items))
        else:
            raise Exception("Unknown message type %d" % self._numitems)
        self.data["timestamp"] = self.timestamp        

class obis_header():

    # 0     7e                                                     : Flag (0x7e)
    # 1-2   a0 87                                                  : Frame Format Field
    # 3-4   01 02                                                  : Source Address
    # 5     01                                                     : Destination Address
    # 6     10                                                     : Control Field = R R R P/F S S S 0 (I Frame)
    # 7-8   9e 6d                                                  : HCS
    # 9-11  e6 e7 00                                               : DLMS/COSEM LLC Addresses
    # 12-16 0f 40 00 00 00                                         : DLMS HEADER?
    # 17+   09 0c 07 d0 01 03 01 0e 00 0c ff 80 00 03              : Information
    #       02 0e                                                  : Information
    #       09 07 4b 46 4d 5f 30 30 31                             : Information
    #       09 10 36 39 37 30 36 33 31 34 30 30 30 30 30 39 35 30  : Information
    #       09 08 4d 41 31 30 35 48 32 45                          : Information
    #       06 00 00 00 00                                         : Information
    #       06 00 00 00 00                                         : Information
    #       06 00 00 00 00                                         : Information
    #       06 00 00 00 00                                         : Information
    #       06 00 00 00 0e                                         : Information
    #       06 00 00 09 01                                         : Information
    #       09 0c 07 d0 01 03 01 0e 00 0c ff 80 00 03              : Information
    #       06 00 00 00 00                                         : Information
    #       06 00 00 00 00                                         : Information
    #       06 00 00 00 00                                         : Information
    #       06 00 00 00 00                                         : Information
    # l-3-2 97 35                                                  : FCS
    # l-1   7e                                                     : Flag
    def __init__(self, buff):
        # Byte 0   Header start byte
        if not buff[0] == 0x7E:
            #print("Not detected header flag byte")
            raise ValueError("Unable to detect start frame byte")
        # Byte -1  Message end byte
        #if not buff[-1] == 0x7E:
        #    print("Not detected end flag byte")
        #    raise ValueError("Unable to detect end frame byte")

        if len(buff) <= 20:
            raise ValueError("Message is to short")
        
        # Byte 1-2 Frame Format Field
        self.FFF = FrameFormatField(buff[1:3])
        # Byte 3-4 Source
        self.source = int.from_bytes(buff[3:5], byteorder='big')
        # Byte 5 Destination
        self.destination = buff[5]
        # Byte 6 Control Field
        self.control_field = buff[6]
        # Byte 7-8 HCS
        self.HCS = buff[7:9]
        # Byte 9-11 DLMS / COSEM LLC Addresses
        self.cosem = buff[9:12]
        # Byte 12-16 DLMS Header
        self.dlsm = buff[12:17]
        # Byte 17+ DATA
        self.data = buff[17:len(buff)-2]
        # Byte -3, -2 FCS
        self.fcs  = buff[-3:-1]
        # Save Header
        self.header = buff[1:17]

class FrameFormatField():
    # 2 byte Frame Format Field
    # 16 BITS: "TTTTSLLLLLLLLLLL"
    # - T=Type bits: TTTT = 0101 (0xa0) = Type 3
    # - S=Segmentation=0 (Segment = 1)
    # - L=11 Length Bits
    def __init__(self, message):
        FFF = btoi(message)
        self.type = (FFF & 0xF000) >> 12
        self.segment = bool(FFF & 0x800)
        self.length = FFF & 0x7FF
    def __repr__(self):
        return "FrameFormat(%s,%s,%s)" % (hex(self.type), self.segment, self.length)

def hexprint(h, header="", split=32):
    if isinstance(h, int):
        return "%02X" % h
    b = ""
    if header:
        hdr = "%s:" % header
        b += hdr
        for i,a in enumerate(h):
            b +=" %02X" % a
            if not (i+1) % split:
                b += "\n"
                b +=" " * len(hdr)
        return b


    for i,a in enumerate(h):
        b +=" %02X" % a
        if not (i+1) % split:
            b += "\n"
    return b





def btoi(bytestring):
    return int.from_bytes(bytestring, byteorder='big') 


def readObisPacket(ser):
    buff = bytes()
    while True:
        buff = ser.read(1)

        if not buff:
            raise EOFError("reached end of file")

        if buff[0] == 0x7e:
            # I Think we have a header here 0x7e
            buff += ser.read(2)
            FFF = int.from_bytes(buff[1:3], byteorder='big')
            Ftype = (FFF & 0xF000) >> 12
            Fsegment = bool(FFF & 0x800)
            Flength = FFF & 0x7FF
            #print(hexprint(FFF))

            if Ftype == 0xA and Fsegment == 0x00:
                break
    # We have detected a frame, going on
    bytes_to_go = Flength - 1  # Flength + 2x Flags 0x7e - 3 bytes read)


    if len(buff) < Flength:
        b = ser.read(bytes_to_go)
        if not b:
            sleep(0.1)
        buff += b

    return buff

def readHan(ser):
    pkg = readObisPacket(ser)
    obis = obis_header(pkg)
    return HAN_message(obis.data)
