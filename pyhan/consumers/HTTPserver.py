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
        if not "act_energy_pa_acu" in self.data:
            self.data["act_energy_pa_acu"] = 0.0
        if "act_energy_pa" in message.data:
            try:
                _LOGGER.info(f'meter: {message.data.get("act_energy_pa",0):10} acm2: {self.data.get("act_energy_pa_acu2",0.0):10.4f} diff: {message.data.get("act_energy_pa",0) - self.data.get("act_energy_pa_acu2",0.0):10.4f} usage: {message.data.get("act_energy_pa",0) - self.data.get("act_energy_pa_acu2",0.0):4.4f} acu: {self.data.get("act_energy_pa_acu",0.0)}')
            except Exception:
                print(Exception)
            self.data["act_energy_pa_acu"] = 0.0
            self.data["act_energy_pa_acu2"] = float(message.data["act_energy_pa"])
            self.data["act_energy_pa_offset"] = message.data["act_energy_pa"] - self.data["act_energy_pa_acu2"]
        else:
            self.data["act_energy_pa_acu"] += message.data["act_pow_pos"] / (3600/2)
            if "act_energy_pa_acu2" in self.data:
                self.data["act_energy_pa_acu2"] = self.data["act_energy_pa"] + self.data["act_energy_pa_acu"]
        self.data.update(message.data)
        pass
