import asyncio
import aiohttp
import logging
import sys
import signal

import pysma

VAR = {}
_LOGGER = logging.getLogger(__name__)





class SMA:
    def __init__(self, ip, user, password):
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        loop = asyncio.get_event_loop()

        self.sensor = 'pv_power'
        self._running = False

        def _shutdown(*_):
            self._running = False
            # asyncio.ensure_future(sma.close_session(), loop=loop)

        signal.signal(signal.SIGINT, _shutdown)
        # loop.add_signal_handler(signal.SIGINT, shutdown)
        # signal.signal(signal.SIGINT, signal.SIG_DFL)
        loop.run_until_complete(
            self.main_loop(loop, user=user, password=password, ip=ip)
        )

    async def main_loop(self, loop, password, user, ip):  # pylint: disable=invalid-name
        """Main loop."""
        async with aiohttp.ClientSession(loop=loop, connector=aiohttp.TCPConnector(ssl=False)) as session:
            self.client = pysma.SMA(session, ip, password=password, group=user)
            await self.client.new_session()
            if self.client.sma_sid is None:
                _LOGGER.info("No session ID")
                self.client.close_session()
                return

            _LOGGER.info("NEW SID: %s", VAR["sma"].sma_sid)

            self._running = True
            while self._running:
                await asyncio.sleep(2)
                pass

            await self.client.close_session()

    def get_readings(self, sensor):
        readings = self.client.read([pysma.Sensors()[sensor]])
        return [
            {
                'measurement': 'balena-sense',
                'fields': {
                    'power': float(next(readings).value),
                }
            }
        ]


if __name__ == "__main__":
    sma = SMA(ip="192.168.1.112", user="installer", password="fronius66")
    print(sma.get_readings(sma.sensor))