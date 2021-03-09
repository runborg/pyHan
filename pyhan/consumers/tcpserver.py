from . import BaseConsumer
import asyncio
import logging
import traceback
import json
from datetime import datetime
_LOGGER = logging.getLogger(__name__)


def _json_serializer(obj):
    if isinstance(obj, (datetime)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


class TCPserverPlugin(BaseConsumer):
    def __init__(self, app):
        self.app = app
        self.server = None
        self.clients = {}

        if 'tcpserver' not in app.config:
            raise ImportError('Plugin not configured')
        config = app.config['tcpserver']
        if isinstance(config, dict):
            self.host = config.get('host', 'localhost')
            self.port = config.get('port', 9000)
        else:
            self.host = 'localhost'
            self.port = 9000


    async def main(self):
        _LOGGER.info('Loaded module %s', self.__class__.__name__)
        self.server = asyncio.create_task(asyncio.start_server(self.client_loop, self.host, self.port), name="tcp-client-daemon")
        while True:
            await asyncio.sleep(10)

    async def client_loop(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        client_addr = writer.get_extra_info('peername')
        _LOGGER.debug(f'client {client_addr} connected')
        # Register broadcast writer
        self.clients[client_addr] = writer
        try:
            while True:
                try:
                    # Just read and forgett, we only send data anyways
                    # We need to do a read whonsi a while to catch client disconnects
                    await asyncio.wait_for(reader.read(), timeout=0.1)
                except asyncio.exceptions.TimeoutError:
                    pass

                # writer.write(b'BOO\n')
                await asyncio.sleep(1)

        except BrokenPipeError:
            # Client disconnected, abort task
            pass

        except Exception as E:
            _LOGGER.error(E)
            _LOGGER.error(traceback.format_exc())

        finally:
            _LOGGER.info('Client disconnected')
            del self.clients[client_addr]

    async def broadcast_reciever(self, message):
        # print(f'{self.__class__.__name__} got message {message!r}')
        for c, v in self.clients.items():
            jstr = json.dumps(message.data, default=_json_serializer)
            v.write(jstr.encode('utf-8'))
            v.write(b'\n')
        pass
