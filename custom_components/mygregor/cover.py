"""MyGregor drive integration for Home Assistant."""
from __future__ import annotations

import logging

from homeassistant.components.cover import (
    CoverEntity,
    DEVICE_CLASS_WINDOW,
    SUPPORT_OPEN,
    SUPPORT_CLOSE,
    STATE_OPEN,
    STATE_CLOSED,
    STATE_OPENING,
    STATE_CLOSING,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_SW_VERSION,
    DEVICE_CLASS_SIGNAL_STRENGTH,
    ATTR_BATTERY_LEVEL,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import format_mac

from .const import DOMAIN, ATTR_HW_VER, ATTR_NOISE
from .entity import MyGregorDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""

    devices = hass.data[DOMAIN]["devices"][config_entry.entry_id]
    registry = hass.data[DOMAIN]["registry"][config_entry.entry_id]
    drives = []
    for device in devices:
        if device.device_type == "Drive":
            drive = MyGregorDrive(device, registry)
            drives += [drive]

    if not drives:
        return

    async_add_entities(drives)


class MyGregorDrive(MyGregorDevice, CoverEntity):
    """Representation of a MyGregor drive."""

    _attr_device_class = DEVICE_CLASS_WINDOW  # Describes the type/class of the cover.
    _supported_features: int = SUPPORT_OPEN | SUPPORT_CLOSE

    def __init__(self, device, registry) -> None:
        """Initialize drive."""
        super().__init__(device)
        self.registry = registry
        self._id = int(device.unique_id)
        self._unique_id = "MyGregorDrive_" + format_mac(device.mac)
        if device.state == "Online":
            self._available = True
        else:
            self._available = False
        self._curr_pos = device.position
        if not device.position:
            self._state = STATE_CLOSED
        else:
            self._state = STATE_OPEN
        self.extra_attrs[ATTR_HW_VER] = device.hardware_version
        self.extra_attrs[ATTR_SW_VERSION] = device.software_version
        self.extra_attrs[DEVICE_CLASS_SIGNAL_STRENGTH] = device.rssi

    @property
    def device_info(self):
        return {
            # "config_entries": "", # Config entries that are linked to this device.
            # "configuration_url": "", # A URL on which the device or service can be configured, linking to paths inside the Home Assistant UI can be done by using homeassistant://<path>.
            "connections": self._connections,  # A set of tuples of (connection_type, connection identifier). Connection types are defined in the device registry module.
            # "default_name": self.device.device_type,  # Default name of this device, will be overridden if name is set. Useful for example for an integration showing all devices on the network.
            # "default_manufacturer": "",  # The manufacturer of the device, will be overridden if manufacturer is set. Useful for example for an integration showing all devices on the network.
            # "default_model": "",  # The model of the device, will be overridden if model is set. Useful for example for an integration showing all devices on the network.
            # "entry_type": "",  # The type of entry. Possible values are None and DeviceEntryType enum members.
            "identifiers": {
                # Set of (DOMAIN, identifier) tuples. Identifiers identify the device in the outside world. An example is a serial number.
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.unique_id),
                ("mac", self.device.mac),
            },
            "name": self.device.name,  # Name of this device.
            "manufacturer": "Bulinfo",  # The manufacturer of the device.
            "model": self.device.model,  # The model of the device.
            "suggested_area": self.device.room_name,  # The suggested name for the area where the device is located.
            "sw_version": self.device.software_version,  # The firmware version of the device.
            "hw_version": self.device.hardware_version,  # The hardware version of the device.
        }

    @property
    def name(self) -> str:
        """Return the display name of the Device."""
        return self.device.name

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        return self._unique_id

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def current_cover_position(self):
        """The current position of cover where 0 means closed and 100 is fully open. Required with SUPPORT_SET_POSITION."""
        return self._curr_pos

    @property
    def is_opening(self) -> bool:
        """If the cover is opening or not. Used to determine state."""
        return self._state == STATE_OPENING

    @property
    def is_closing(self) -> bool:
        """If the cover is closing or not. Used to determine state."""
        return self._state == STATE_CLOSING

    @property
    def is_closed(self):
        """If the cover is closed or not. if the state is unknown, return None. Used to determine state."""
        # STATE_CLOSED
        return self._curr_pos == 0

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return self._supported_features

    def open_cover(self, **kwargs):
        """Open the cover."""
        self.registry.api.open(self._id)
        if self._curr_pos == 100:
            self._state = STATE_OPEN
        else:
            self._state = STATE_OPENING

    def close_cover(self, **kwargs):
        """Close cover."""
        self.registry.api.close(self._id)
        if not self._curr_pos:
            self._state = STATE_CLOSED
        else:
            self._state = STATE_CLOSING

    def update(self) -> None:
        """Fetch new state data for this device.

        This is the only method that should fetch new data for Home Assistant.
        """
        device = self.registry.api.get_device(
            self._id, include_data=True, include_room=False
        )
        self.extra_attrs[ATTR_HW_VER] = device.hardware_version
        self.extra_attrs[ATTR_SW_VERSION] = device.software_version
        self.extra_attrs[DEVICE_CLASS_SIGNAL_STRENGTH] = device.rssi
        self._curr_pos = device.position
        if not device.position:
            self._state = STATE_CLOSED
        else:
            self._state = STATE_OPEN

        mac = self.device.mac
        if device.state == "Online":
            self._available = True
            sensor = self.registry.get_sensor(mac, DEVICE_CLASS_SIGNAL_STRENGTH)
            if sensor:
                sensor.set_value(device.rssi)
                sensor.set_avaliable(True)
            sensor = self.registry.get_sensor(mac, ATTR_NOISE)
            if sensor:
                sensor.set_value(device.noise)
                sensor.set_avaliable(True)
            sensor = self.registry.get_sensor(mac, ATTR_BATTERY_LEVEL)
            if sensor:
                sensor.set_value(device.battery_level)
                sensor.set_avaliable(True)
            sensor = self.registry.get_sensor(mac, "position")
            if sensor:
                sensor.set_value(device.position)
                sensor.set_avaliable(True)
        else:
            self._available = False
            sensor = self.registry.get_sensor(mac, DEVICE_CLASS_SIGNAL_STRENGTH)
            if sensor:
                sensor.set_avaliable(False)
            sensor = self.registry.get_sensor(mac, ATTR_NOISE)
            if sensor:
                sensor.set_avaliable(False)
            sensor = self.registry.get_sensor(mac, ATTR_BATTERY_LEVEL)
            if sensor:
                sensor.set_avaliable(False)
            sensor = self.registry.get_sensor(mac, "position")
            if sensor:
                sensor.set_avaliable(False)
