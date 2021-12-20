"""Platform for MyGregor Home Assistant integration."""
from __future__ import annotations

import logging

from homeassistant.components.__mygregor_hass.mygregorpy import (
    MyGregorApi,
    UnauthorizedException,
)
import voluptuous as vol

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.light import PLATFORM_SCHEMA
from homeassistant.const import (
    TEMP_CELSIUS,
    CONF_API_TOKEN,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_CO2,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_TOKEN): cv.string,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Awesome Light platform."""
    # Assign configuration variables.
    # The configuration check takes care they are present.
    api_token = config[CONF_API_TOKEN]

    # Setup connection with devices/cloud
    hub = MyGregorApi()
    hub.set_access_token(api_token)

    # Verify that passed in configuration works
    try:
        hub.my_account()
    except UnauthorizedException:
        _LOGGER.error(
            "Could not connect to MyGregor hub. Access token expired or invalid"
        )
        return

    # Add devices
    add_entities(
        Station(device, hub)
        for device in hub.get_devices(include_data=True)
        if device["type"] == "Station"
    )


class Station(SensorEntity):
    """Representation of a sensor."""

    def __init__(self, light, hub) -> None:
        """Initialize an Station."""
        self._hub = hub
        self._name = "Station " + light["name"] + " Temperature"
        self._id = int(light["id"])
        self._state = None
        self._attr_native_unit_of_measurement = TEMP_CELSIUS
        if "sensors_raw" in light and "temperature" in light["sensors_raw"]:
            self._state = light["sensors_raw"]["temperature"]

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        return self._id

    @property
    def name(self) -> str:
        """Return the display name of the station."""
        return self._name

    @property
    def device_class(self) -> str:
        """Return the class of this device, from component DEVICE_CLASSES."""
        return DEVICE_CLASS_TEMPERATURE

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement of this entity."""
        return TEMP_CELSIUS

    @property
    def state(self):
        """The state"""
        return self._state

    def update(self) -> None:
        """Fetch new state data for this light.

        This is the only method that should fetch new data for Home Assistant.
        """
        data = self._hub.get_device(self._id)
        if "sensors_raw" in data and "temperature" in data["sensors_raw"]:
            self._state = data["sensors_raw"]["temperature"]
