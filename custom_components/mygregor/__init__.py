"""MyGregor Home Assistant Integration."""
import logging

from homeassistant import config_entries, core
from homeassistant.const import CONF_ACCESS_TOKEN

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
    hass.data[DOMAIN]["api"] = {}

    # Setup connection with devices/cloud
    api = MyGregorApi()
    api.set_access_token(entry.data[CONF_ACCESS_TOKEN])
    _LOGGER.debug("Setting up online MyGregor device")
    devices = await hass.async_add_executor_job(api.get_devices, True, True)
    hass.data[DOMAIN]["devices"][entry.entry_id] = devices
    hass.data[DOMAIN]["api"][entry.entry_id] = api

    # hass.config_entries.async_setup_platforms(entry, RPC_PLATFORMS)

    # Forward the setup to the sensor platform.
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    # Forward the setup to the cover (driver) platform.
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "cover")
    )

    return True


# async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
#     """Set up the MyGregor HASS component from yaml configuration."""
#     hass.data.setdefault(DOMAIN, {})
#     return True
