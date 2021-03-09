from . import BaseConsumer
import asyncio
import logging
from aiohttp import web
import json
from datetime import datetime
_LOGGER = logging.getLogger(__name__)


def _json_serializer(obj):
    if isinstance(obj, (datetime)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


class HTTPserverPlugin(BaseConsumer):
    def __init__(self, app):
        self.data = {}
        self.app = app

        if 'http' not in app.config:
            raise ImportError('Plugin not configured')
        config = app.config['http']
        if isinstance(config, dict):
            self.server = config.get('host', '127.0.0.1')
            self.port = config.get('port', 9001)
        else:
            self.server = 'localhost'
            self.port = 9001

    async def main(self):
        _LOGGER.info('Loaded module %s', self.__class__.__name__)
        server = web.Server(self.web_handler)
        runner = web.ServerRunner(server)
        await runner.setup()
        site = web.TCPSite(runner, self.server, self.port)
        await site.start()

        while True:
            await asyncio.sleep(10)

    async def web_handler(self, request: web.Request):
        _LOGGER.info("Serving client %s", request.remote)
        jstr = json.dumps(self.data, default=_json_serializer, indent=4)
        return web.Response(text=jstr)

    async def broadcast_reciever(self, message):
        # print(f'{self.__class__.__name__} got message {message!r}')
        self.data.update(message.data)
        pass
