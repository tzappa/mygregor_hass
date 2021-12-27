"""MyGregor entity helper."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC

from .const import ATTR_MAC

_LOGGER = logging.getLogger(__name__)


class MyGregorDevice:
    """Interface for MyGregor devices, such as Drive and Station."""

    sensors: dict[str, Any] = {}
    extra_attrs: dict[str, Any] = {}

    def __init__(self, device) -> None:
        """Initialize device."""
        self.device = device
        self.extra_attrs[ATTR_MAC] = device.mac
        self._connections = {(CONNECTION_NETWORK_MAC, device.mac)}

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes. Needed in Entity class."""
        return self.extra_attrs
