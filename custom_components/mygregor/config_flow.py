"""Configurations for MyGregor in Home Assistant."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.data_entry_flow import FlowResult

from .mygregorpy import (
    MyGregorApi,
    UnauthorizedException,
)
from homeassistant import config_entries, core
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_MAC

import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

AUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ACCESS_TOKEN): cv.string,
        vol.Required(CONF_MAC): cv.string,
    }
)


async def validate_auth(access_token: str, hass: core.HomeAssistant):
    """Validates a MyGregor access token.

    Raises a ValueError if the auth token is invalid.
    """
    # Setup connection with devices/cloud
    hub = MyGregorApi()
    hub.set_access_token(access_token)

    # Verify that passed in configuration works
    try:
        await hass.async_add_executor_job(hub.my_account)
    except UnauthorizedException as err:
        raise ValueError from err

    return hub


async def validate_device(mac: str, hub: MyGregorApi, hass: core.HomeAssistant):
    """Validate user's device MAC address.

    Raises a ValueError if the device is not available."""
    found = None
    devices = await hass.async_add_executor_job(hub.get_devices)
    if devices is None:
        raise ValueError("No devices found")
    for device in devices:
        if device.mac == mac:
            found = device
            break
    if found is None:
        raise ValueError("Device not found")

    return found


class MyGregorHassConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """MyGregor Hass config flow."""

    data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Invoked when a user initiates a flow via the user interface."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                hub = await validate_auth(user_input[CONF_ACCESS_TOKEN], self.hass)
            except ValueError:
                errors["base"] = "auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_MAC])
                self._abort_if_unique_id_configured({CONF_MAC: user_input[CONF_MAC]})
                try:
                    device = await validate_device(user_input[CONF_MAC], hub, self.hass)
                except ValueError:
                    errors["base"] = "unknown_device"

            if not errors:
                # Input is valid, set data.
                # self.data = user_input
                return self.async_create_entry(
                    title=device.name,
                    data={
                        **user_input,
                        "device_id": device.unique_id,
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=AUTH_SCHEMA, errors=errors
        )
