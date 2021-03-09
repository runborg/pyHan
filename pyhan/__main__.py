from typing import Dict
from .consumers import BaseConsumer
from . import consumers
import pkgutil
import importlib
import inspect
import asyncio
from pprint import pprint
import logging
import traceback
import serial_asyncio
import HAN
import yaml
import signal

_LOGGER = logging.getLogger('pyhan')
_STDOUT = logging.StreamHandler()
_STDOUT.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_STDOUT.setFormatter(formatter)
_LOGGER.addHandler(_STDOUT)
_LOGGER.setLevel(logging.DEBUG)
print(_LOGGER)


def load_plugins() -> Dict[str, BaseConsumer]:
    """Load all plugins defined within the plugin directory
    All python files are loaded, and a dict containing all sub-classes of
    BaseConsumer is returned

    return: dict[str, class]
    """
    plugins = {}
    # Itterate over all modules inside consumers
    for _, module_name, _ in pkgutil.iter_modules(consumers.__path__):
        # Load each submodule and collect all BaseConsumer subclasses
        mod = importlib.import_module(f'.consumers.{module_name}', package='pyhan')
        for cname, cls in inspect.getmembers(mod, inspect.isclass):
            # Only load subclasses of BaseConsumer(and not BaseConsumer itself)
            if cls == BaseConsumer or not issubclass(cls, BaseConsumer):
                continue
            plugins[cname] = cls
    return plugins


async def _keep_coro_running(coro, *args, **kwargs) -> None:
    task = asyncio.current_task()
    while True:
        try:
            await coro(*args, **kwargs)
        except asyncio.CancelledError:
            break
        except Exception:
            _LOGGER.critical('Exception executing task %r  \n%s',
                             task.get_name() if task else 'UNKNOWN',
                             traceback.format_exc())
            await asyncio.sleep(5)

        _LOGGER.error('Task %r reached its end, waiting 5sec and respowning',
                      task.get_name() if task else 'UNKNOWN')
        await asyncio.sleep(5)


async def _ensure_coro_logging(coro, *args, **kwargs) -> None:
    task = asyncio.current_task()
    try:
        await coro(*args, **kwargs)
    except asyncio.CancelledError:
        raise
    except Exception:
        _LOGGER.critical('Exception executing task %r  \n%s',
                         task.get_name() if task else 'UNKNOWN',
                         traceback.format_exc())



class Application():
    def __init__(self,):
        with open('config.yml') as _f:
            self.config = yaml.load(_f, Loader=yaml.FullLoader)

        self.consumers = {}
        consumers = load_plugins()
        # initiate all plugin objects
        for x in consumers:
            try:
                self.consumers[x] = consumers[x](self)
            except ImportError as E:
                _LOGGER.info('Module %s not configured: %s', x, E)

        self.tasks = {}

    def main(self,):
        asyncio.run(self.async_main())

    def _shutdown_handler(self):
        _LOGGER.info("Stopping application")
        loop = asyncio.get_running_loop()
        for task in asyncio.all_tasks():
            _LOGGER.info('Stopping task: %s', task.get_name())
            task.cancel()
        # loop.run_until_complete(asyncio.gather(*asyncio.all_tasks()))
        # loop.stop()


    async def async_main(self):
        # Catch signals
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, self._shutdown_handler)
        # Start the main task in eack consumer
        for t in self.consumers:
            c = self.consumers[t]
            task = asyncio.create_task(_keep_coro_running(c.main), name=f'consumer-{t}-name')

            self.tasks[t] = task
        await _keep_coro_running(self.async_serial_generator)
        # await self.async_random_generator()

    async def async_serial_generator(self):
        # Try to open a serial connection
        _LOGGER.debug('Opening serial connection')
        reader, writer = await serial_asyncio.open_serial_connection(url='/dev/ttyUSB0', baudrate=2400)
        while True:
            pkg = await HAN.async_readHan(reader)
            await self.broadcast_message(pkg)

    async def async_random_generator(self):
        nr = 0
        while True:
            await asyncio.sleep(1)
            # Generate Random message
            nr += 1
            msg = f'RANDOM MESSAGE {nr}'
            print(f'Generated message {msg}')
            for c, v in self.consumers.items():
                if hasattr(v, 'broadcast_reciever'):
                    _x = getattr(v, 'broadcast_reciever')
                    await asyncio.create_task(_ensure_coro_logging(_x, msg))

    async def broadcast_message(self, message):
        for c, v in self.consumers.items():
            if hasattr(v, 'broadcast_reciever'):
                _x = getattr(v, 'broadcast_reciever')
                await _x(message)


if __name__ == '__main__':
    _APP = Application()
    _APP.main()
