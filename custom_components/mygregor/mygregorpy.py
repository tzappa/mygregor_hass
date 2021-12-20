""" Python wrapper for the MyGregor API."""

from datetime import datetime, timedelta
import json
import logging
import requests

BASE_URL = "https://api.mygregor.com"

_LOGGER = logging.getLogger(__name__)


class MyGregorDevice:
    """MyGregor Device interface."""

    def __init__(self, unique_id: int, device_type: str, name: str, mac: str) -> None:
        """MyGregorDevice constructor. Set all required properties."""
        self._id = unique_id
        self._type = device_type
        self._name = name
        self._mac = mac
        self._sensors = {}
        # typical sensors for WiFi devices
        self.enable_sensor("rssi", "dB", "RSSI")
        # not exactly sensors but attributes
        self.enable_sensor("hw_version", "", "Hardware Version")
        self.enable_sensor("sw_version", "", "Software Version")
        self.enable_sensor("state", "", "State")  # Online/Offline

    @property
    def unique_id(self) -> str:
        """Gets the ID of device."""
        return self._id

    @property
    def name(self) -> str:
        """Gets the name of device."""
        return self._name

    @property
    def mac(self) -> str:
        """Gets the MAC address of the device."""
        return self._mac

    @property
    def device_type(self) -> str:
        """Gets device type."""
        return self._type

    @property
    def state(self):
        """Gets device state - online or offline. None value is also possible for "N/A"."""
        return self.get_value("state")

    @property
    def rssi(self):
        """Get RSSI value."""
        return self.get_value("rssi")

    @property
    def hardware_version(self):
        """Get hardware version"""
        return self.get_value("hw_version")

    @property
    def software_version(self):
        """Get software version"""
        return self.get_value("sw_version")

    def enable_sensor(self, sensor: str, measurement: str, title=None):
        """Enable some sensors."""
        if title is None:
            title = sensor
        self._sensors[sensor] = {
            "title": title,
            "measurement": measurement,
            "value": None,
        }

    def get_sensors(self, active_only=True):
        """Returns a list of available sensors.

        On active_only=False the sensors without values will be added in the list also.
        """
        if active_only:
            result = {}
            for sensor in self._sensors:
                if self._sensors[sensor]["value"] is not None:
                    result[sensor] = self._sensors[sensor]
            return result
        else:
            return self._sensors

    def get_value(self, sensor: str):
        """Get the sensor value."""
        return self._sensors[sensor]["value"]

    def set_value(self, sensor: str, value):
        """Set some sensor value. The type of the sensor must be as the type of the measurement is."""
        if sensor not in self._sensors:
            raise Exception(f"Unknown sensor {sensor}")

        self._sensors[sensor]["value"] = value


class MyGregorStation(MyGregorDevice):
    """MyGregor Station interface."""

    def __init__(self, unique_id: int, name: str, mac: str) -> None:
        """Constructor needs the name of the station."""
        super().__init__(unique_id, "Station", name, mac=mac)
        self.enable_sensor("co2", "ppm", "CO₂")
        self.enable_sensor("temperature", "℃", "Temperature")
        self.enable_sensor("humidity", "%", "Humidity")
        self.enable_sensor("noise", "dBA", "Noise")
        self.enable_sensor("luminosity", "lx", "Luminosity")
        self.enable_sensor("radiation", "µSv/h", "Radiation")

    @property
    def temperature(self):
        """Gets the temperature sensor value."""
        return self.get_value("temperature")

    @property
    def humidity(self):
        """Gets the humidity sensor value."""
        return self.get_value("humidity")

    @property
    def co2(self):
        """Gets the carbon dioxide sensor value."""
        return self.get_value("co2")

    @property
    def noise(self):
        """Gets the noise sensor value."""
        return self.get_value("noise")

    @property
    def luminosity(self):
        """Gets the light sensor value."""
        return self.get_value("luminosity")

    @property
    def radiation(self):
        """Gets the radiation sensor value."""
        return self.get_value("radiation")


class MyGregorDrive(MyGregorDevice):
    """MyGregor Drive interface."""

    def __init__(self, unique_id: int, name: str, mac: str) -> None:
        super().__init__(unique_id, "Drive", name, mac=mac)
        self.enable_sensor("noise", "dBA", "Noise")
        self.enable_sensor("voltage", "V", "Battery voltage")
        self.enable_sensor("battery_level", "%", "Battery level")

    @property
    def noise(self):
        """Gets the noise sensor value."""
        return self.get_value("noise")

    @property
    def voltage(self):
        """Gets the voltage sensor value."""
        return self.get_value("voltage")

    @property
    def battery_level(self):
        """Gets the battery level sensor value."""
        return self.get_value("battery_level")


class MyGregorApi:
    """Interface class for the MyGregor API."""

    def __init__(self) -> None:
        """Constructor for MyGregor API class."""
        self._username = None
        self._password = None
        self._access_token = None
        self._token_expires_at = None

    def set_access_token(self, access_token: str, expires_in: int = 0) -> None:
        """Sets the token to access user's protected content."""
        self._access_token = access_token
        if expires_in > 0:
            self._token_expires_at = datetime.now() + timedelta(0, expires_in)
        else:
            self._token_expires_at = None
        _LOGGER.debug("Access token ***** set, expires at %s", self._token_expires_at)

    def get_access_token(self):
        """Returns obtained or previously set access_token"""
        return self._access_token

    def login(self, username: str, password: str) -> bool:
        """Try to obtain access_token."""
        headers = {
            "Content-Type": "application/json",
        }
        payload = {
            "email": username,
            "password": password,
        }

        endpoint = "/v2/auth"
        url = BASE_URL + "/v2/auth"

        _LOGGER.debug("Accessing API %s for user %s login", endpoint, username)
        response = requests.request(
            "POST", url, data=json.dumps(payload), headers=headers
        )
        _LOGGER.debug("API %s response code: %s", endpoint, response.status_code)

        try:
            error_msg = json.loads(response.text)["message"]
        except json.JSONDecodeError:
            error_msg = f"Error {response.status_code} on login"

        if response.status_code == 400:
            raise UnauthorizedException(error_msg)
        if response.status_code != 200:
            raise MyGregorApiException(error_msg)

        data = response.json()
        _LOGGER.debug("API %s returned: %s", endpoint, data)
        self._username = username
        self._password = password
        self.set_access_token(data["token"], int(data["token_expires_after"]))

        return True

    def my_account(self):
        """Returns logged in user info."""
        response = self._exec_request("GET", "/v2/accounts/me")
        return response

    def get_devices(self, include_data: bool = False):
        """Returns list of all user's devices."""
        if include_data:
            response = self._exec_request("GET", "/v2/devices?include=device_data")
        else:
            response = self._exec_request("GET", "/v2/devices")

        devices = []
        for device in response["devices"]:
            devices.append(self._set_device(device))

        return devices

    def get_device(self, device_id: int):
        """Returns device data."""
        response = self._exec_request(
            "GET", f"/v2/devices/{device_id}?include=device_data"
        )

        return self._set_device(response)

    def _set_device(self, data) -> MyGregorDevice:
        if data["type"] == "Station":
            device = MyGregorStation(data["id"], data["name"], data["mac"])
        elif data["type"] == "Drive":
            device = MyGregorDrive(data["id"], data["name"], data["mac"])
        if "hardware_version" in data:
            device.set_value("hw_version", data["hardware_version"])
        if "software_version" in data:
            device.set_value("sw_version", data["software_version"])
        if "status" in data:
            device.set_value("state", data["status"])
        else:
            device.set_value("state", "Offline")
        if "sensors_raw" in data:
            sensors = data["sensors_raw"]
            if "co2" in sensors:
                device.set_value("co2", sensors["co2"])
            if "temperature" in sensors:
                device.set_value("temperature", sensors["temperature"])
            if "humidity" in sensors:
                device.set_value("humidity", sensors["humidity"])
            if "rssi" in sensors:
                device.set_value("rssi", sensors["rssi"])
            if "noise" in sensors:
                device.set_value("noise", sensors["noise"])
            if "light" in sensors:
                device.set_value("luminosity", sensors["light"])
            if "radiation" in sensors:
                device.set_value("radiation", sensors["radiation"])
            if "battery_voltage" in sensors:
                device.set_value("voltage", sensors["battery_voltage"])
            if "battery_perc" in sensors:
                device.set_value("battery_level", sensors["battery_perc"])

        return device

    def get_rooms(self, include_image: bool = False):
        """Returns user's rooms."""
        if include_image:
            response = self._exec_request("GET", "/v2.1/rooms?include=image")
        else:
            response = self._exec_request("GET", "/v2.1/rooms")
        return response["rooms"]

    def get_room_info(self, room_id: int):
        """Returns all available info about specific user's room."""
        response = self._exec_request(
            "GET",
            f"/v2/rooms/{room_id}?include=image,power_profile,room_data,devices,device_data",
        )
        return response

    def set_room_state(self, room_id: int, state: str):
        """open/close or set another action for specific room"""
        available_states = ("auto", "open", "close", "airing", "relax")
        if state not in available_states:
            raise MyGregorApiException(
                f"Room state can be one of the following {available_states}. Unknown state '{state}' is given."
            )
        response = self._exec_request("PUT", f"/v2/rooms/{room_id}", {"state": state})
        return response

    def _exec_request(self, method, endpoint, payload={}):
        """Executes request against MyGregor API."""

        if not self._access_token:
            raise UnauthorizedException("Access token not set")

        url = BASE_URL + endpoint
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self._access_token,
        }
        data = None
        if (method in ["POST", "PUT"]) and payload:
            data = json.dumps(payload)

        _LOGGER.debug("Accessing API %s with token", endpoint)
        response = requests.request(method, url, data=data, headers=headers)
        _LOGGER.debug("API %s response code: %s", endpoint, response.status_code)

        try:
            error_msg = json.loads(response.text)["message"]
        except json.JSONDecodeError:
            error_msg = f"Error {response.status_code} executing {method} {endpoint} with {data}"
        except KeyError:
            error_msg = f"Error {response.status_code} executing {method} {endpoint} with {data}"

        if response.status_code == 401:
            raise UnauthorizedException(error_msg)
        if response.status_code == 404:
            raise MyGregorApiException(f"URL {url} Not Found")
        if response.status_code != 200:
            raise MyGregorApiException(response.status_code, error_msg)

        data = response.json()
        _LOGGER.debug("API %s %s returned: %s", method, endpoint, data)

        return data


class UnauthorizedException(Exception):
    """Error to indicate there is invalid auth or the response code is 401."""


class MyGregorApiException(Exception):
    """Error to indicate global API Exception."""
