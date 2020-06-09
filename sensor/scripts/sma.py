import json
import os
import logging
import sys

import requests
import jmespath
import pysma

VAR = {}
_LOGGER = logging.getLogger(__name__)


class _SMA_noasync:
    """Class to connect to the SMA webconnect module and read parameters."""

    def __init__(self, url, password, group="user", uid=None):
        """Init SMA connection."""
        if group not in pysma.USERS:
            raise KeyError("Invalid user type: {}".format(group))
        if len(password) > 12:
            _LOGGER.warn('Password should not exceed 12 characters')
        self._new_session_data = {"right": pysma.USERS[group], "pass": password}
        self._url = url.rstrip("/")
        if not url.startswith("http"):
            self._url = "http://" + self._url
        self.sma_sid = None
        self.sma_uid = uid
        self.new_session()

    def _fetch_json(self, url, payload):
        """Fetch json data for requests."""
        params = {
            "data": json.dumps(payload),
            "headers": {"content-type": "application/json", "content-length": str(len(json.dumps(payload)))},
            "params": {"sid": self.sma_sid} if self.sma_sid else None,
            "verify": False,
        }
        resp = requests.post(self._url + url, **params)
        return resp.json()

    def new_session(self):
        """Establish a new session."""
        body = self._fetch_json(pysma.URL_LOGIN, self._new_session_data)
        self.sma_sid = jmespath.search("result.sid", body)
        if self.sma_sid:
            return True

        err = body.pop("err", None)
        msg = "Could not start session, %s, got {}".format(body)

        if err:
            if err == 503:
                _LOGGER.error(msg, "Max amount of sessions reached")
            else:
                _LOGGER.error(msg, err)
        else:
            _LOGGER.error(msg, "Session ID expected [result.sid]")
        return False

    def close_session(self):
        """Close the session login."""
        if self.sma_sid is None:
            return
        try:
            self._fetch_json(pysma.URL_LOGOUT, {})
        finally:
            self.sma_sid = None

    def read(self, sensors):
        """Read a set of keys."""
        payload = {"destDev": [], "keys": list(set([s.key for s in sensors]))}
        if self.sma_sid is None:
            self.new_session()
            if self.sma_sid is None:
                return False
        body = self._fetch_json(pysma.URL_VALUES, payload=payload)

        # On the first error we close the session which will re-login
        err = body.get("err")
        if err is not None:
            _LOGGER.warning(
                "%s: error detected, closing session to force another login attempt, got: %s",
                self._url,
                body,
            )
            self.close_session()
            return False

        if not isinstance(body, dict) or "result" not in body:
            _LOGGER.warning("No 'result' in reply from SMA, got: %s", body)
            return False

        if self.sma_uid is None:
            # Get the unique ID
            self.sma_uid = next(iter(body["result"].keys()), None)

        result_body = body["result"].pop(self.sma_uid, None)

        if body != {"result": {}}:
            _LOGGER.warning(
                "Unexpected body %s, extracted %s",
                json.dumps(body),
                json.dumps(result_body),
            )

        notfound = []
        for sen in sensors:
            if sen.key in result_body:
                sen.extract_value(result_body)
                continue

            notfound.append(f"{sen.name} [{sen.key}]")

        if notfound:
            _LOGGER.warning(
                "No values for sensors: %s. Response from inverter: %s",
                ",".join(notfound),
                result_body,
            )

        return True


class SMA:
    def __init__(self, ip, user, password, sensor_id='pv_power'):
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        self.sensor = sensor_id if sensor_id else 'pv_power'
        self.ip = ip
        self.user = user
        self.password = password
        self._running = False
        self.client = _SMA_noasync(url=self.ip, password=self.password, group=self.user)
        self.sensors = pysma.Sensors()

    def get_readings(self, sensor):
        if self.client.sma_sid is None:
            _LOGGER.info("No session ID")
            return
        self.client.read(pysma.Sensors())
        if sensor not in pysma.Sensors():
            _LOGGER.warning("specified sensor '%s' is not available" % sensor)
            return []
        else:
            return [{'measurement': 'sma-solar',
                    'fields': {
                        'power': float(pysma.Sensors()[sensor].value or 0),
                        }}]


if __name__ == "__main__":
    sma = SMA(ip=os.getenv("BALENASENSE_SOLAR_IP"),
              user=os.getenv("BALENASENSE_SOLAR_USER"),
              password=os.getenv("BALENASENSE_SOLAR_PASSWORD"))
    print(sma.get_readings(sma.sensor))
