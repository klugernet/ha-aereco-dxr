"""Fan entity for Aereco Ventilation System."""
from typing import Any, Optional, Dict, List

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AerecoDataUpdateCoordinator
from .const import DOMAIN, MODE_NAMES, MODE_AUTOMATIC, MODE_BOOST, MODE_STOP, MODE_ABSENCE, MODE_FREE_COOLING, VERSION


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Aereco fan entity."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([AerecoFan(coordinator, entry)])


class AerecoFan(CoordinatorEntity, FanEntity):
    """Representation of an Aereco Ventilation System as a fan entity."""

    _attr_has_entity_name = True
    _attr_name = "Ventilation System"
    _attr_supported_features = FanEntityFeature.SET_SPEED | FanEntityFeature.PRESET_MODE

    def __init__(self, coordinator: AerecoDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the fan."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_ventilation_fan"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Aereco Ventilation System",
            "manufacturer": "Aereco",
            "model": "DXR",
            "sw_version": VERSION,
        }

    @property
    def is_on(self) -> bool:
        """Return true if fan is on."""
        mode_data = self.coordinator.data.get("current_mode")
        if mode_data:
            current_mode = str(mode_data.get("current_mode", MODE_STOP))
            return current_mode != MODE_STOP
        return False

    @property
    def percentage(self) -> Optional[int]:
        """Return the current speed percentage."""
        mode_data = self.coordinator.data.get("current_mode")
        if not mode_data:
            return None
            
        current_mode = str(mode_data.get("current_mode", MODE_STOP))
        airflow = mode_data.get("airflow", 0)
        
        # Convert airflow to percentage based on mode
        if current_mode == MODE_STOP:
            return 0
        elif current_mode == MODE_ABSENCE:
            return 20  # Low speed for absence mode
        elif current_mode == MODE_AUTOMATIC:
            # Automatic mode - use airflow value (could be 0-100)
            return min(100, max(0, airflow))
        elif current_mode == MODE_FREE_COOLING:
            return 60  # Medium speed for free cooling
        elif current_mode == MODE_BOOST:
            return 100  # Maximum speed for boost
        else:
            return 50  # Default medium speed

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return 100  # Support percentage-based speeds

    @property
    def preset_mode(self) -> Optional[str]:
        """Return the current preset mode."""
        mode_data = self.coordinator.data.get("current_mode")
        if mode_data:
            current_mode = str(mode_data.get("current_mode", MODE_STOP))
            return MODE_NAMES.get(current_mode, "Unknown")
        return None

    @property
    def preset_modes(self) -> List[str]:
        """Return a list of available preset modes."""
        return [
            MODE_NAMES[MODE_AUTOMATIC],
            MODE_NAMES[MODE_FREE_COOLING], 
            MODE_NAMES[MODE_BOOST],
            MODE_NAMES[MODE_ABSENCE],
            MODE_NAMES[MODE_STOP]
        ]

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        mode_data = self.coordinator.data.get("current_mode", {})
        attributes = {}
        
        if mode_data:
            attributes.update({
                "user_mode": MODE_NAMES.get(str(mode_data.get("user_mode", "")), "Unknown"),
                "timeout": mode_data.get("timeout", 0),
                "timeout_unit": mode_data.get("timeout_unit", 0),
                "airflow": mode_data.get("airflow", 0),
            })
            
        # Add maintenance info if available
        maintenance_data = self.coordinator.data.get("maintenance", {})
        if maintenance_data:
            attributes.update({
                "filter_clogging_level": maintenance_data.get("filter_clogging_level", 0),
                "bypass_status": maintenance_data.get("bypass_status", 0),
                "preheater_level": maintenance_data.get("preheater_level", 0),
            })
            
        # Add warnings if any
        warnings_data = self.coordinator.data.get("warnings", {})
        if warnings_data:
            attributes["has_warnings"] = warnings_data.get("has_warnings", False)
            
        return attributes

    async def async_turn_on(
        self,
        percentage: Optional[int] = None,
        preset_mode: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        if preset_mode:
            await self.async_set_preset_mode(preset_mode)
        elif percentage is not None:
            await self.async_set_percentage(percentage)
        else:
            # Default to automatic mode
            await self.coordinator.api.set_mode(MODE_AUTOMATIC)
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan."""
        await self.coordinator.api.set_mode(MODE_STOP)
        await self.coordinator.async_request_refresh()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        if percentage == 0:
            await self.async_turn_off()
            return
            
        # Map percentage to appropriate mode
        if percentage <= 25:
            mode = MODE_ABSENCE
        elif percentage <= 50:
            mode = MODE_AUTOMATIC  
        elif percentage <= 75:
            mode = MODE_FREE_COOLING
        else:
            mode = MODE_BOOST
            
        await self.coordinator.api.set_mode(mode)
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        # Find mode key by name
        mode_key = None
        for key, name in MODE_NAMES.items():
            if name == preset_mode:
                mode_key = key
                break
                
        if mode_key:
            await self.coordinator.api.set_mode(mode_key)
            await self.coordinator.async_request_refresh()