from . import BaseConsumer
import asyncio
import re
from collections import deque
from datetime import datetime
import aioinflux
import logging
import traceback
import aiohttp
_LOGGER = logging.getLogger(__name__)


class InfluxPlugin(BaseConsumer):
    def __init__(self, app):
        self.app = app
        self.queue: deque = deque(maxlen=10)
        if 'influx' not in app.config:
            raise ImportError('Plugin not configured')
        config = app.config['influx']
        if isinstance(config, dict):
            self.server = config.get('server', 'localhost')
            self.port = config.get('port', 8086)
            self.username = config.get('username', 'default')
            self.password = config.get('password', 'default')
            self.database = config.get('database', 'ams')
        else:
            self.server = 'localhost'
            self.port = 8086
            self.username = 'default'
            self.password = 'default'
            self.database = 'ams'

    async def main(self):
        _LOGGER.info('Loaded module %s', self.__class__.__name__)

        influx = aioinflux.InfluxDBClient(host=self.server,
                                          port=self.port,
                                          database=self.database,
                                          username=self.username,
                                          password=self.password)

        while True:
            if not self.queue:
                await asyncio.sleep(0.1)
                continue
            # Get the oldest item from the list
            item = self.queue[0]
            time, han = item

            # Generate message
            measure = [{"measurement": "amsReadout",
                        "tags": {"user": "runar"},
                        "time": int(time.strftime("%s")),
                        "fields": {"watt": han.data["act_pow_pos"]},
                        }]

            try:
                await influx.write(measure)
            except aiohttp.client_exceptions.ClientConnectorError as E:
                _LOGGER.error('Unable to communicate with %s: %s', self.server, E)
                await asyncio.sleep(10)
                continue
            except Exception as E:
                _LOGGER.error(E)
                _LOGGER.error(traceback.format_exc())
                await asyncio.sleep(10)
                continue

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
                fields["react_pow_neg"] = float(
                    fields["react_pow_neg"] / 1000)
            if "react_pow_pos" in fields:
                fields["react_pow_pos"] = float(
                    fields["react_pow_pos"] / 1000)
            if "act_energy_pa" in fields:
                fields["act_energy_pa"] = float(
                    fields["act_energy_pa"] / 1000)
            m = [{"measurement": "AMS",
                  "tags": {"user": "runar"},
                  "fields": fields,
                  }]

            try:
                await influx.write(m)
            except aiohttp.client_exceptions.ClientConnectorError as E:
                _LOGGER.error(
                    'Unable to communicate with %s: %s', self.server, E)
                await asyncio.sleep(10)
                continue
            except Exception as E:
                _LOGGER.error(E)
                _LOGGER.error(traceback.format_exc())
                await asyncio.sleep(10)
                continue

            if self.queue[0] == item:
                # We are finished processing
                # Remove element from queue if the buffer has not overflown
                self.queue.popleft()
            else:
                _LOGGER.info('Current item has been overflown from the buffer')

    async def broadcast_reciever(self, message):
        if len(self.queue) == self.queue.maxlen:
            _LOGGER.info('Queue is full, oldest element will be dropped')
        self.queue.append((datetime.now(), message))
