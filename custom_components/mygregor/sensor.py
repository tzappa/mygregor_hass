"""Platform for MyGregor Home Assistant integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Dict
from .mygregorpy import MyGregorApi
import voluptuous as vol

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import (
    STATE_CLASS_MEASUREMENT,
    PLATFORM_SCHEMA,
    SensorEntity,
)
from homeassistant.components.cover import (
    CoverEntity,
    DEVICE_CLASS_WINDOW,
    SUPPORT_OPEN,
    SUPPORT_CLOSE,
    # STATE_OPEN,
    STATE_CLOSED,
    STATE_OPENING,
    STATE_CLOSING,
)

# from homeassistant.helpers.entity import Entity
from homeassistant.const import (
    ATTR_BATTERY_LEVEL,
    ATTR_SW_VERSION,
    CONF_ACCESS_TOKEN,
    PERCENTAGE,
    STATE_OPEN,
    TEMP_CELSIUS,
    LIGHT_LUX,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    CONCENTRATION_PARTS_PER_MILLION,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_CO2,
    DEVICE_CLASS_ILLUMINANCE,
    DEVICE_CLASS_SIGNAL_STRENGTH,
    ENTITY_CATEGORY_DIAGNOSTIC,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import (
    DOMAIN,
    ATTR_HW_VER,
    ATTR_NOISE,
    ATTR_RADIATION,
)

_LOGGER = logging.getLogger(__name__)
# Time between updating data from api.mygregor.com
SCAN_INTERVAL = timedelta(seconds=60)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ACCESS_TOKEN): cv.string,
    }
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    access_token = config[CONF_ACCESS_TOKEN]
    # Setup connection with devices/cloud
    hub = MyGregorApi()
    hub.set_access_token(access_token)

    devices = await hass.async_add_executor_job(hub.get_devices, True, True)
    sensors = []
    for device in devices:
        if device.device_type == "Station":
            station = MyGregorStation(device, hub)
            sensors += [station]

            sensor = MyGRSSISensor(
                mac=device.mac, name=f"{device.name} RSSI", value=device.rssi
            )
            station.sensors[DEVICE_CLASS_SIGNAL_STRENGTH] = sensor
            sensors += [sensor]

            sensor = MyGTemperatureSensor(
                mac=device.mac,
                name=f"{device.name} Temperature",
                value=device.temperature,
            )
            station.sensors[DEVICE_CLASS_TEMPERATURE] = sensor
            sensors += [sensor]

            sensor = MyGHumiditySensor(
                mac=device.mac, name=f"{device.name} Humidity", value=device.humidity
            )
            station.sensors[DEVICE_CLASS_HUMIDITY] = sensor
            sensors += [sensor]

            sensor = MyGCO2Sensor(
                mac=device.mac,
                name=f"{device.name} CO₂",
                value=device.co2,
            )
            station.sensors[DEVICE_CLASS_CO2] = sensor
            sensors += [sensor]

            sensor = MyGLuminositySensor(
                mac=device.mac,
                name=f"{device.name} Luminosity",
                value=device.luminosity,
            )
            station.sensors[DEVICE_CLASS_ILLUMINANCE] = sensor
            sensors += [sensor]

            sensor = MyGNoiseSensor(
                mac=device.mac, name=f"{device.name} Noise", value=device.noise
            )
            station.sensors[ATTR_NOISE] = sensor
            sensors += [sensor]

            sensor = MyGRadiationSensor(
                mac=device.mac, name=f"{device.name} Radiation", value=device.radiation
            )
            station.sensors[ATTR_RADIATION] = sensor
            sensors += [sensor]

        elif device.device_type == "Drive":
            drive = MyGregorDrive(device, hub)
            sensors += [drive]

            sensor = MyGRSSISensor(
                mac=device.mac, name=f"{device.name} RSSI", value=device.rssi
            )
            drive.sensors[DEVICE_CLASS_SIGNAL_STRENGTH] = sensor
            sensors += [sensor]

            # sensor = MyGBatteryLevelSensor(mac=device.mac, name=f"{device.name} Battery", value=88)
            # drive.sensors[ATTR_BATTERY_LEVEL] = sensor
            # sensors += [sensor]

            sensor = MyGNoiseSensor(
                mac=device.mac, name=f"{device.name} Noise", value=device.noise
            )
            drive.sensors[ATTR_NOISE] = sensor
            sensors += [sensor]

    async_add_entities(sensors)


class MyGSensor(SensorEntity):
    """Representation of a MyGregor sensor."""

    def __init__(self, mac, name, device_class, value) -> None:
        """Initialize an Sensor."""
        self._name = name
        self._type = device_class
        self._value = value
        self._id = "MyGregor_" + mac.replace(":", "") + "_" + device_class
        self._available = True

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        return self._id

    @property
    def name(self) -> str:
        """Return the display name of the sensor."""
        return self._name

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def device_class(self) -> str:
        """Return the class of this device, from component DEVICE_CLASSES."""
        return self._type

    @property
    def native_value(self) -> int:
        """Return the value reported by the sensor."""
        return self._value

    def set_value(self, value):
        """Parent device is updating the state."""
        self._value = value
        if value is not None:
            self._available = True

    def set_avaliable(self, value: bool):
        """Parent device is setting availability on or off."""
        self._available = value

    def update(self) -> None:
        """Update does nothing since the device shall update the state."""


class MyGTemperatureSensor(MyGSensor):
    """Representation of a MyGregor temperature sensor."""

    def __init__(self, mac, name, value) -> None:
        """Initialize an Sensor."""
        super().__init__(mac, name, DEVICE_CLASS_TEMPERATURE, value)

    @property
    def state_class(self) -> str:
        """Return the class of this entity."""
        return STATE_CLASS_MEASUREMENT

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement of this entity."""
        return TEMP_CELSIUS


class MyGHumiditySensor(MyGSensor):
    """Representation of a MyGregor humidity sensor."""

    def __init__(self, mac, name, value) -> None:
        """Initialize an Sensor."""
        super().__init__(mac, name, DEVICE_CLASS_HUMIDITY, value)

    @property
    def state_class(self) -> str:
        """Return the class of this entity."""
        return STATE_CLASS_MEASUREMENT

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement of this entity."""
        return PERCENTAGE


class MyGCO2Sensor(MyGSensor):
    """Representation of a MyGregor CO2 sensor."""

    def __init__(self, mac, name, value) -> None:
        """Initialize an Sensor."""
        super().__init__(mac, name, DEVICE_CLASS_CO2, value)

    @property
    def state_class(self) -> str:
        """Return the class of this entity."""
        return STATE_CLASS_MEASUREMENT

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""
        return "mdi:gauge"

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement of this entity."""
        return CONCENTRATION_PARTS_PER_MILLION


class MyGRadiationSensor(MyGSensor):
    """Representation of a MyGregor CO₂ sensor."""

    def __init__(self, mac, name, value) -> None:
        """Initialize an Sensor."""
        super().__init__(mac, name, ATTR_RADIATION, value)

    @property
    def state_class(self) -> str:
        """Return the class of this entity."""
        return STATE_CLASS_MEASUREMENT

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""
        return "mdi:radioactive"

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement of this entity."""
        return "µSv/h"


class MyGNoiseSensor(MyGSensor):
    """Representation of a MyGregor noise sensor."""

    def __init__(self, mac, name, value) -> None:
        """Initialize an Sensor."""
        super().__init__(mac, name, ATTR_NOISE, value)

    @property
    def state_class(self) -> str:
        """Return the class of this entity."""
        return STATE_CLASS_MEASUREMENT

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement of this entity."""
        return "dBA"

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""
        return "mdi:ear-hearing"


class MyGLuminositySensor(MyGSensor):
    """Representation of a MyGregor luminosity sensor."""

    def __init__(self, mac, name, value) -> None:
        """Initialize an Sensor."""
        super().__init__(mac, name, DEVICE_CLASS_ILLUMINANCE, value)

    @property
    def state_class(self) -> str:
        """Return the class of this entity."""
        return STATE_CLASS_MEASUREMENT

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement of this entity."""
        return LIGHT_LUX


class MyGRSSISensor(MyGSensor):
    """Representation of a MyGregor RSSI sensor."""

    def __init__(self, mac, name, value) -> None:
        """Initialize an Sensor."""
        super().__init__(mac, name, DEVICE_CLASS_SIGNAL_STRENGTH, value)
        # default availability is Off. User can activate this
        self._attr_entity_registry_enabled_default = False

    @property
    def state_class(self) -> str:
        """Return the class of this entity."""
        return STATE_CLASS_MEASUREMENT

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement of this entity."""
        return SIGNAL_STRENGTH_DECIBELS_MILLIWATT

    @property
    def entity_category(self):
        return ENTITY_CATEGORY_DIAGNOSTIC


# This shall be a sensor to a Battery Device, not Drive
class MyGBatteryLevelSensor(MyGSensor):
    """Representation of a MyGregor battery sensor."""

    def __init__(self, mac, name, value) -> None:
        """Initialize an Sensor."""
        super().__init__(mac, name, ATTR_BATTERY_LEVEL, value)

    @property
    def state_class(self) -> str:
        """Return the class of this entity."""
        return STATE_CLASS_MEASUREMENT

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement of this entity."""
        return PERCENTAGE

    @property
    def entity_category(self):
        return ENTITY_CATEGORY_DIAGNOSTIC


class MyGregorStation(SensorEntity):
    """Representation of a MyGregor station device."""

    def __init__(self, device, myg) -> None:
        """Initialize an Device."""
        self.myg = myg
        self._device = device
        self._id = int(device.unique_id)
        self._value = device.state
        self._unique_id = (
            "MyGregor" + device.device_type + "_" + device.mac.replace(":", "")
        )
        if device.state == "Online":
            self._state = "Online"
            self._available = True
        else:
            self._state = "Offline"
            self._available = False
        self.extra_attrs: Dict[str, Any] = {}
        self.sensors: Dict[str, Any] = {}

    @property
    def device_info(self):
        return {
            # "config_entries": "", # Config entries that are linked to this device.
            # "configuration_url": "", # A URL on which the device or service can be configured, linking to paths inside the Home Assistant UI can be done by using homeassistant://<path>.
            # "connections": "", # A set of tuples of (connection_type, connection identifier). Connection types are defined in the device registry module.
            # "default_name": self._device.device_type,  # Default name of this device, will be overridden if name is set. Useful for example for an integration showing all devices on the network.
            # "default_manufacturer": "",  # The manufacturer of the device, will be overridden if manufacturer is set. Useful for example for an integration showing all devices on the network.
            # "default_model": "",  # The model of the device, will be overridden if model is set. Useful for example for an integration showing all devices on the network.
            # "entry_type": "",  # The type of entry. Possible values are None and DeviceEntryType enum members.
            "identifiers": {
                # Set of (DOMAIN, identifier) tuples. Identifiers identify the device in the outside world. An example is a serial number.
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.unique_id),
                ("mac", self._device.mac),
            },
            "name": self._device.name,  # Name of this device.
            "manufacturer": "Rezon",  # The manufacturer of the device.
            "model": self._device.model,  # The model of the device.
            "suggested_area": self._device.room_name,  # The suggested name for the area where the device is located.
            "sw_version": self._device.software_version,  # The firmware version of the device.
            "hw_version": self._device.hardware_version,  # The hardware version of the device.
        }

    @property
    def name(self) -> str:
        """Return the display name of the Device."""
        return self._device.name

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        return self._unique_id

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        return self.extra_attrs

    @property
    def native_value(self) -> int:
        """Return the value reported by the sensor."""
        return self._value

    @property
    def is_on(self) -> bool:
        """Return true if sensor state is on."""
        return self._value == "Online"

    def update(self) -> None:
        """Fetch new state data for this device.

        This is the only method that should fetch new data for Home Assistant.
        """
        device = self.myg.get_device(self._id, include_data=True)
        self.extra_attrs[ATTR_HW_VER] = device.hardware_version
        self.extra_attrs[ATTR_SW_VERSION] = device.software_version

        if device.state == "Online":
            self._state = "Online"
            self._available = True

            self.sensors[DEVICE_CLASS_SIGNAL_STRENGTH].set_value(device.rssi)
            self.sensors[DEVICE_CLASS_TEMPERATURE].set_value(device.temperature)
            self.sensors[DEVICE_CLASS_HUMIDITY].set_value(device.humidity)
            self.sensors[DEVICE_CLASS_CO2].set_value(device.co2)
            self.sensors[DEVICE_CLASS_ILLUMINANCE].set_value(device.luminosity)
            self.sensors[ATTR_NOISE].set_value(device.noise)
            self.sensors[ATTR_RADIATION].set_value(device.radiation)
        else:
            self._state = "Offline"
            self._available = False
            self.sensors[DEVICE_CLASS_SIGNAL_STRENGTH].set_avaliable(False)
            self.sensors[DEVICE_CLASS_TEMPERATURE].set_avaliable(False)
            self.sensors[DEVICE_CLASS_HUMIDITY].set_avaliable(False)
            self.sensors[DEVICE_CLASS_CO2].set_avaliable(False)
            self.sensors[DEVICE_CLASS_ILLUMINANCE].set_avaliable(False)
            self.sensors[ATTR_NOISE].set_avaliable(False)
            self.sensors[ATTR_RADIATION].set_avaliable(False)


class MyGregorDrive(CoverEntity):
    """Representation of a MyGregor drive."""

    _attr_device_class = DEVICE_CLASS_WINDOW
    _supported_features: int = SUPPORT_OPEN | SUPPORT_CLOSE

    def __init__(self, device, myg) -> None:
        """Initialize an Device."""
        self.myg = myg
        self._device = device
        self._id = int(device.unique_id)
        self._unique_id = "MyGregorDrive_" + device.mac.replace(":", "")
        if device.state == "Online":
            self._available = True
        else:
            self._available = False
        self._curr_pos = device.position
        if not device.position:
            self._state = STATE_CLOSED
        else:
            self._state = STATE_OPEN
        self.extra_attrs: Dict[str, Any] = {}
        self.sensors: Dict[str, Any] = {}

    @property
    def device_info(self):

        return {
            # "config_entries": "", # Config entries that are linked to this device.
            # "configuration_url": "", # A URL on which the device or service can be configured, linking to paths inside the Home Assistant UI can be done by using homeassistant://<path>.
            # "connections": "", # A set of tuples of (connection_type, connection identifier). Connection types are defined in the device registry module.
            # "default_name": self._device.device_type,  # Default name of this device, will be overridden if name is set. Useful for example for an integration showing all devices on the network.
            # "default_manufacturer": "",  # The manufacturer of the device, will be overridden if manufacturer is set. Useful for example for an integration showing all devices on the network.
            # "default_model": "",  # The model of the device, will be overridden if model is set. Useful for example for an integration showing all devices on the network.
            # "entry_type": "",  # The type of entry. Possible values are None and DeviceEntryType enum members.
            "identifiers": {
                # Set of (DOMAIN, identifier) tuples. Identifiers identify the device in the outside world. An example is a serial number.
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.unique_id),
                ("mac", self._device.mac),
            },
            "name": self._device.name,  # Name of this device.
            "manufacturer": "Rezon",  # The manufacturer of the device.
            "model": self._device.model,  # The model of the device.
            "suggested_area": self._device.room_name,  # The suggested name for the area where the device is located.
            "sw_version": self._device.software_version,  # The firmware version of the device.
            "hw_version": self._device.hardware_version,  # The hardware version of the device.
        }

    @property
    def name(self) -> str:
        """Return the display name of the Device."""
        return self._device.name

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        return self._unique_id

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        return self.extra_attrs

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
        self.myg.open(self._id)
        if self._curr_pos == 100:
            self._state = STATE_OPEN
        else:
            self._state = STATE_OPENING

    # Only implement this method if the flag SUPPORT_CLOSE is set.
    def close_cover(self, **kwargs):
        """Close cover."""
        self.myg.close(self._id)
        if not self._curr_pos:
            self._state = STATE_CLOSED
        else:
            self._state = STATE_CLOSING

    def update(self) -> None:
        """Fetch new state data for this device.

        This is the only method that should fetch new data for Home Assistant.
        """
        device = self.myg.get_device(self._id, include_data=True)
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
