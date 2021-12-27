"""MyGregor Home Assistant Integration."""
from dataclasses import dataclass
import logging

from homeassistant import config_entries, core
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.helpers.device_registry import format_mac

from .const import DOMAIN
from .mygregorpy import MyGregorApi

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data
    hass.data[DOMAIN]["devices"] = {}
    hass.data[DOMAIN]["registry"] = {}

    # Setup connection with devices/cloud
    api = MyGregorApi()
    api.set_access_token(entry.data[CONF_ACCESS_TOKEN])
    _LOGGER.debug("Setting up online MyGregor device")
    devices = await hass.async_add_executor_job(api.get_devices, True, True)
    hass.data[DOMAIN]["devices"][entry.entry_id] = devices
    hass.data[DOMAIN]["registry"][entry.entry_id] = MyGregorRegistry(api)

    # Forward the setup to the cover (driver) platform.
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "cover")
    )
    # Forward the setup to the sensor platform.
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return True


class MyGregorRegistry:
    """Register for sensors and devices."""

    def __init__(self, api) -> None:
        """Create registry."""
        self.sensors = {}
        self._api = api

    def add_sensor(self, device_mac, sensor) -> None:
        """Add a sensor to the list with unique ID."""
        _id = format_mac(device_mac) + "_" + sensor.device_class
        self.sensors[_id] = sensor

    def get_sensor(self, device_mac, device_class):
        """Returns registered sensor or None if the sensor is not present."""
        _id = format_mac(device_mac) + "_" + device_class
        return self.sensors[_id] if _id in self.sensors else None

    @property
    def api(self):
        """Access MyGregor API."""
        return self._api
