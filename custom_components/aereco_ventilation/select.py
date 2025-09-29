"""Select entity for Aereco Ventilation System."""
from typing import Optional, List

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AerecoDataUpdateCoordinator
from .const import DOMAIN, MODE_NAMES, MODE_AUTOMATIC, MODE_FREE_COOLING, MODE_BOOST, MODE_ABSENCE, MODE_STOP


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Aereco select entity."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([AerecoModeSelect(coordinator, entry)])


class AerecoModeSelect(CoordinatorEntity, SelectEntity):
    """Select entity for choosing ventilation mode."""

    _attr_has_entity_name = True
    _attr_name = "Operation Mode"

    def __init__(self, coordinator: AerecoDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_operation_mode"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Aereco Ventilation System",
            "manufacturer": "Aereco",
            "model": "DXR",
        }

    @property
    def current_option(self) -> Optional[str]:
        """Return the current selected option."""
        mode_data = self.coordinator.data.get("current_mode")
        if mode_data:
            current_mode = str(mode_data.get("current_mode", MODE_STOP))
            return MODE_NAMES.get(current_mode, "Unknown")
        return None

    @property
    def options(self) -> List[str]:
        """Return the list of available options."""
        return [
            MODE_NAMES[MODE_AUTOMATIC],
            MODE_NAMES[MODE_FREE_COOLING], 
            MODE_NAMES[MODE_BOOST],
            MODE_NAMES[MODE_ABSENCE],
            MODE_NAMES[MODE_STOP]
        ]

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        # Find mode key by name
        mode_key = None
        for key, name in MODE_NAMES.items():
            if name == option:
                mode_key = key
                break
                
        if mode_key:
            await self.coordinator.api.set_mode(mode_key)
            await self.coordinator.async_request_refresh()