"""Configurations for MyGregor in Home Assistant."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .mygregorpy import (
    MyGregorApi,
    UnauthorizedException,
)
from homeassistant import config_entries, core
from homeassistant.const import CONF_ACCESS_TOKEN

import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

AUTH_SCHEMA = vol.Schema({vol.Required(CONF_ACCESS_TOKEN): cv.string})


async def validate_auth(access_token: str, hass: core.HomeAssistant) -> None:
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


class MyGregorHassConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """MyGregor Hass config flow."""

    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            try:
                await validate_auth(user_input[CONF_ACCESS_TOKEN], self.hass)
            except ValueError:
                errors["base"] = "auth"
            if not errors:
                # Input is valid, set data.
                self.data = user_input
                # User is done adding repos, create the config entry.
                return self.async_create_entry(title="MyGregor HASS", data=self.data)

        return self.async_show_form(
            step_id="user", data_schema=AUTH_SCHEMA, errors=errors
        )
