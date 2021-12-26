"""Platform for MyGregor Home Assistant integration."""
from __future__ import annotations

import logging
from datetime import timedelta

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
from homeassistant.components.select import SelectEntity
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
from .sensor import MyGNoiseSensor, MyGRSSISensor, MyGBatteryLevelSensor

_LOGGER = logging.getLogger(__name__)
# Time between updating data from api.mygregor.com
SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    # config = hass.data[DOMAIN][config_entry.entry_id]
    # access_token = config[CONF_ACCESS_TOKEN]
    # # Setup connection with devices/cloud
    # api = MyGregorApi()
    # api.set_access_token(access_token)

    devices = hass.data[DOMAIN]["devices"][config_entry.entry_id]
    api = hass.data[DOMAIN]["api"][config_entry.entry_id]
    sensors = []
    for device in devices:
        if device.device_type == "Drive":
            drive = MyGregorDrive(device, api)
            sensors += [drive]

            sensor = MyGRSSISensor(
                mac=device.mac, name=f"{device.name} RSSI", value=device.rssi
            )
            drive.sensors[DEVICE_CLASS_SIGNAL_STRENGTH] = sensor
            sensors += [sensor]

            sensor = MyGBatteryLevelSensor(
                mac=device.mac, name=f"{device.name} Battery", value=88
            )
            drive.sensors[ATTR_BATTERY_LEVEL] = sensor
            sensors += [sensor]

            sensor = MyGNoiseSensor(
                mac=device.mac, name=f"{device.name} Noise", value=device.noise
            )
            drive.sensors[ATTR_NOISE] = sensor
            sensors += [sensor]

            option = MyGDriveOption(api=api, device=device)
            drive.sensors["option"] = option
            sensors += [option]

    async_add_entities(sensors)


class MyGregorDrive(MyGregorDevice, CoverEntity):
    """Representation of a MyGregor drive."""

    _attr_device_class = DEVICE_CLASS_WINDOW
    _supported_features: int = SUPPORT_OPEN | SUPPORT_CLOSE

    def __init__(self, device, myg) -> None:
        """Initialize drive."""
        super().__init__(device, myg)
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
        self._current_option = "auto"

    @property
    def device_info(self):
        return {
            # "config_entries": "", # Config entries that are linked to this device.
            # "configuration_url": "", # A URL on which the device or service can be configured, linking to paths inside the Home Assistant UI can be done by using homeassistant://<path>.
            # "connections": "", # A set of tuples of (connection_type, connection identifier). Connection types are defined in the device registry module.
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
            "manufacturer": "Rezon",  # The manufacturer of the device.
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

    # @property
    # def native_value(self) -> int:
    #     """Return the value reported by the sensor."""
    #     return self._value

    # @property
    # def is_on(self) -> bool:
    #     """Return true if sensor state is on."""
    #     return self._value == "Online"

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

    # @property
    # def device_class(self):
    #     """Describes the type/class of the cover. Must be None or one of the valid values from the table below."""
    #     return DEVICE_CLASS_WINDOW

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return self._supported_features

    # Only implement this method if the flag SUPPORT_OPEN is set.
    def open_cover(self, **kwargs):
        """Open the cover."""
        self.api.open(self._id)
        if self._curr_pos == 100:
            self._state = STATE_OPEN
        else:
            self._state = STATE_OPENING

    # Only implement this method if the flag SUPPORT_CLOSE is set.
    def close_cover(self, **kwargs):
        """Close cover."""
        self.api.close(self._id)
        if not self._curr_pos:
            self._state = STATE_CLOSED
        else:
            self._state = STATE_CLOSING

    def update(self) -> None:
        """Fetch new state data for this device.

        This is the only method that should fetch new data for Home Assistant.
        """
        device = self.api.get_device(self._id, include_data=True)
        self.extra_attrs[ATTR_HW_VER] = device.hardware_version
        self.extra_attrs[ATTR_SW_VERSION] = device.software_version
        self._curr_pos = device.position
        if not device.position:
            self._state = STATE_CLOSED
        else:
            self._state = STATE_OPEN

        if device.state == "Online":
            # self._state = "Online"
            self._available = True
            self.sensors[DEVICE_CLASS_SIGNAL_STRENGTH].set_value(device.rssi)
            self.sensors[ATTR_NOISE].set_value(device.noise)
        else:
            # self._state = "Offline"
            self._available = False
            self.sensors[DEVICE_CLASS_SIGNAL_STRENGTH].set_avaliable(False)
            self.sensors[ATTR_NOISE].set_avaliable(False)

    @property
    def current_option(self):
        "The current select option."
        return self._current_option

    def select_option(self, option: str) -> None:
        """Change the selected option."""
        self._current_option = option
        self.api.set_room_state(self.device.room_id, option)


class MyGDriveOption(SelectEntity):
    """Represents Drive (Room's) state - open/close/auto/airing/relax."""

    def __init__(self, api, device) -> None:
        """Initialize an Sensor."""
        self.api = api
        self._device = device
        self._unique_id = "MyGregor_" + device.mac.replace(":", "") + "_option"
        self._name = f"{device.name} Option"
        self._current_option = "auto"

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        return self._unique_id

    @property
    def name(self) -> str:
        """Return the display name of the sensor."""
        return self._name

    # @property
    # def available(self) -> bool:
    #     """Return True if entity is available."""
    #     return self._device.available

    @property
    def options(self):
        "A list of available options as string."
        return ("open", "close", "auto", "airing", "relax")

    @property
    def current_option(self):
        "The current select option."
        return self._current_option

    def select_option(self, option: str) -> None:
        """Change the selected option."""
        self._current_option = option
        self.api.set_room_state(self._device.room_id, option)
