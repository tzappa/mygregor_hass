"""Platform for MyGregor Home Assistant integration."""
from __future__ import annotations

import logging
from datetime import timedelta

import voluptuous as vol

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_SW_VERSION,
    DEVICE_CLASS_CO2,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_ILLUMINANCE,
    DEVICE_CLASS_SIGNAL_STRENGTH,
    DEVICE_CLASS_TEMPERATURE,
    CONF_ACCESS_TOKEN,
    PERCENTAGE,
    TEMP_CELSIUS,
    LIGHT_LUX,
    # SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    CONCENTRATION_PARTS_PER_MILLION,
    # ENTITY_CATEGORY_DIAGNOSTIC,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import (
    STATE_CLASS_MEASUREMENT,
    SensorEntity,
)
from .const import DOMAIN, ATTR_RADIATION, ATTR_HW_VER, ATTR_NOISE

from .entity import MyGregorDevice

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
    async_add_entities: AddEntitiesCallback,
):
    """Setup sensors from a config entry created in the integrations UI."""

    registry = hass.data[DOMAIN]["registry"][config_entry.entry_id]
    api_devices = [registry.api_devices]
    sensors = []
    for device in api_devices:
        if device.device_type == "Drive":
            sensor = MyGNoiseSensor(
                mac=device.mac, name=f"{device.name} Noise", value=device.noise
            )
            registry.add_sensor(device.mac, sensor)
            sensors += [sensor]

            sensor = MyGPositionSensor(
                mac=device.mac, name=f"{device.name} Position", value=device.position
            )
            registry.add_sensor(device.mac, sensor)
            sensors += [sensor]

        elif device.device_type == "Station":
            station = MyGregorStation(device, registry)
            sensors += [station]

            sensor = MyGTemperatureSensor(
                mac=device.mac,
                name=f"{device.name} Temperature",
                value=device.temperature,
            )
            registry.add_sensor(device.mac, sensor)
            sensors += [sensor]

            sensor = MyGHumiditySensor(
                mac=device.mac, name=f"{device.name} Humidity", value=device.humidity
            )
            registry.add_sensor(device.mac, sensor)
            sensors += [sensor]

            sensor = MyGCO2Sensor(
                mac=device.mac,
                name=f"{device.name} CO₂",
                value=device.co2,
            )
            registry.add_sensor(device.mac, sensor)
            sensors += [sensor]

            sensor = MyGLuminositySensor(
                mac=device.mac,
                name=f"{device.name} Luminosity",
                value=device.luminosity,
            )
            registry.add_sensor(device.mac, sensor)
            sensors += [sensor]

            sensor = MyGNoiseSensor(
                mac=device.mac, name=f"{device.name} Noise", value=device.noise
            )
            registry.add_sensor(device.mac, sensor)
            sensors += [sensor]

            sensor = MyGRadiationSensor(
                mac=device.mac, name=f"{device.name} Radiation", value=device.radiation
            )
            registry.add_sensor(device.mac, sensor)
            sensors += [sensor]

    async_add_entities(sensors)


class MyGregorStation(MyGregorDevice, SensorEntity):
    """Representation of a MyGregor station device."""

    def __init__(self, device, registry) -> None:
        """Initialize station."""
        super().__init__(device)
        self.registry = registry
        self._id = int(device.unique_id)
        self._value = device.state
        self._unique_id = "MyGregor" + device.device_type + "_" + format_mac(device.mac)
        if device.state == "Online":
            self._value = "Online"
            self._available = True
        else:
            self._value = "Offline"
            self._available = False

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
            "manufacturer": "Rezon",  # The manufacturer of the device.
            "model": self.device.model,  # The model of the device.
            "suggested_area": self.device.zone_name,  # The suggested name for the area where the device is located.
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
        device = self.registry.api.get_device(self._id, include_data=True)
        self.extra_attrs[ATTR_HW_VER] = device.hardware_version
        self.extra_attrs[ATTR_SW_VERSION] = device.software_version
        self.extra_attrs[DEVICE_CLASS_SIGNAL_STRENGTH] = device.rssi

        mac = self.device.mac
        if device.state == "Online":
            self._value = "Online"
            self._available = True
            self.registry.set_sensor_value(
                mac, DEVICE_CLASS_TEMPERATURE, device.temperature
            )
            self.registry.set_sensor_value(mac, DEVICE_CLASS_HUMIDITY, device.humidity)
            self.registry.set_sensor_value(mac, DEVICE_CLASS_CO2, device.co2)
            self.registry.set_sensor_value(
                mac, DEVICE_CLASS_ILLUMINANCE, device.luminosity
            )
            self.registry.set_sensor_value(mac, ATTR_NOISE, device.noise)
            self.registry.set_sensor_value(mac, ATTR_RADIATION, device.radiation)
        else:
            self._value = "Offline"
            self._available = False
            self.registry.set_sensor_value(mac, DEVICE_CLASS_TEMPERATURE, None)
            self.registry.set_sensor_value(mac, DEVICE_CLASS_HUMIDITY, None)
            self.registry.set_sensor_value(mac, DEVICE_CLASS_CO2, None)
            self.registry.set_sensor_value(mac, DEVICE_CLASS_ILLUMINANCE, None)
            self.registry.set_sensor_value(mac, ATTR_NOISE, None)
            self.registry.set_sensor_value(mac, ATTR_RADIATION, None)


class MyGSensor(SensorEntity):
    """Representation of a MyGregor sensor."""

    def __init__(self, mac, name, device_class, value) -> None:
        """Initialize an Sensor."""
        self._name = name
        self._type = device_class
        self._value = value
        self._id = "MyGregor_" + format_mac(mac) + "_" + device_class
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

    @property
    def state_class(self) -> str:
        """Return the class of this entity."""
        return STATE_CLASS_MEASUREMENT

    def set_value(self, value):
        """Parent device is updating the state."""
        self._value = value
        if value is not None:
            self._available = True

    def set_available(self, value: bool):
        """Parent device is setting availability on or off."""
        self._available = value

    def update(self) -> None:
        """Update does nothing since the device shall update the state."""


class MyGNoiseSensor(MyGSensor):
    """Representation of a MyGregor noise sensor."""

    def __init__(self, mac, name, value) -> None:
        """Initialize an Sensor."""
        super().__init__(mac, name, ATTR_NOISE, value)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement of this entity."""
        return "dBA"

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""
        return "mdi:ear-hearing"


class MyGTemperatureSensor(MyGSensor):
    """Representation of a MyGregor temperature sensor."""

    def __init__(self, mac, name, value) -> None:
        """Initialize an Sensor."""
        super().__init__(mac, name, DEVICE_CLASS_TEMPERATURE, value)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement of this entity."""
        return TEMP_CELSIUS


class MyGPositionSensor(MyGSensor):
    """Representation of a MyGregor position sensor."""

    def __init__(self, mac, name, value) -> None:
        """Initialize an Sensor."""
        super().__init__(mac, name, "position", value)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement of this entity."""
        return PERCENTAGE

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""
        return "mdi:angle-acute"


class MyGHumiditySensor(MyGSensor):
    """Representation of a MyGregor humidity sensor."""

    def __init__(self, mac, name, value) -> None:
        """Initialize an Sensor."""
        super().__init__(mac, name, DEVICE_CLASS_HUMIDITY, value)

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
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""
        return "mdi:radioactive"

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement of this entity."""
        return "µSv/h"


class MyGLuminositySensor(MyGSensor):
    """Representation of a MyGregor luminosity sensor."""

    def __init__(self, mac, name, value) -> None:
        """Initialize an Sensor."""
        super().__init__(mac, name, DEVICE_CLASS_ILLUMINANCE, value)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement of this entity."""
        return LIGHT_LUX


# class MyGRSSISensor(MyGSensor):
#     """Representation of a MyGregor RSSI sensor."""

#     def __init__(self, mac, name, value) -> None:
#         """Initialize an Sensor."""
#         super().__init__(mac, name, DEVICE_CLASS_SIGNAL_STRENGTH, value)
#         # default availability is Off. User can activate this
#         self._attr_entity_registry_enabled_default = False

#     @property
#     def native_unit_of_measurement(self) -> str:
#         """Return the unit of measurement of this entity."""
#         return SIGNAL_STRENGTH_DECIBELS_MILLIWATT

#     @property
#     def entity_category(self):
#         return ENTITY_CATEGORY_DIAGNOSTIC
