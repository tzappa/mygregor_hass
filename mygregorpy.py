""" Python wrapper for the MyGregor API."""

from datetime import datetime, timedelta
import json
import logging
import requests

BASE_URL = "https://api.mygregor.com"

_LOGGER = logging.getLogger(__name__)


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

        _LOGGER.debug(f"Accessing API {endpoint} for user {username} login")
        response = requests.request(
            "POST", url, data=json.dumps(payload), headers=headers
        )
        _LOGGER.debug(f"API {endpoint} response code: {response.status_code}")

        try:
            error_msg = json.loads(response.text)["message"]
        except Exception:
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
        return response["devices"]

    def get_device(self, device_id: int):
        """Returns device data."""
        response = self._exec_request(
            "GET", f"/v2/devices/{device_id}?include=device_data"
        )
        return response

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
        except Exception:
            error_msg = f"Error {response.status_code} executing {method} {endpoint} with {data}"

        if response.status_code == 401:
            raise UnauthorizedException(error_msg)
        if response.status_code == 404:
            raise MyGregorApiException(f"URL {url} Not Found")
        if response.status_code != 200:
            raise MyGregorApiException(response.status_code, error_msg)

        data = response.json()
        _LOGGER.debug(f"API {method} {endpoint} returned: {data}")

        return data


class UnauthorizedException(Exception):
    """Error to indicate there is invalid auth or the response code is 401."""


class MyGregorApiException(Exception):
    """Error to indicate global API Exception."""
