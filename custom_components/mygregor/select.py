"""Not using."""
from homeassistant.components.select import SelectEntity


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
        self.api.set_zone_state(self._device.zone_id, option)
