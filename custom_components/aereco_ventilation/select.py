"""Select entity for Aereco Ventilation System."""
import asyncio
import logging
from typing import Optional, List

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AerecoDataUpdateCoordinator
from .const import (
    DOMAIN, MODE_NAMES, MODE_AUTOMATIC, MODE_FREE_COOLING, MODE_BOOST, MODE_ABSENCE, MODE_STOP,
    DEFAULT_AIRFLOW_VALUES, DEFAULT_TIMEOUT_VALUES
)

_LOGGER = logging.getLogger(__name__)


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
        _LOGGER.debug(f"Select option called with: {option}")
        
        # Find mode key by name
        mode_key = None
        for key, name in MODE_NAMES.items():
            if name == option:
                mode_key = key
                break
        
        _LOGGER.debug(f"Found mode key: {mode_key} for option: {option}")
        
        if mode_key:
            # Set the mode first
            result = await self.coordinator.api.set_mode(mode_key)
            _LOGGER.debug(f"Set mode API call result: {result}")
            
            # Apply default timeout for the new mode
            timeout_value = DEFAULT_TIMEOUT_VALUES.get(mode_key)
            if timeout_value and timeout_value > 0:  # Skip timeout for Automatic mode (0 = no timeout)
                # Send timeout to settings.html
                timeout_commands = {
                    "1": "02",  # Free Cooling -> POST_FREE_COOLING_MODE_TIMEOUT
                    "2": "04",  # Boost -> POST_BOOST_MODE_TIMEOUT  
                    "3": "06",  # Absence -> POST_ABSENCE_MODE_TIMEOUT
                    "4": "08",  # Stop -> POST_STOP_MODE_TIMEOUT
                }
                
                post_command = timeout_commands.get(mode_key)
                if post_command:
                    timeout_result = await self.coordinator.api.set_mode_timeout_direct(post_command, timeout_value)
                    _LOGGER.debug(f"Set default timeout {timeout_value} for mode {option}: {timeout_result}")
            
            # Apply default airflow for the new mode
            default_airflow = DEFAULT_AIRFLOW_VALUES.get(mode_key)
            if default_airflow is not None:
                airflow_result = await self.coordinator.api.set_system_airflow(default_airflow)
                _LOGGER.debug(f"Set default airflow {default_airflow} for mode {option}: {airflow_result}")
            
            # Wait a moment for the system to process the changes
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error(f"Could not find mode key for option: {option}")