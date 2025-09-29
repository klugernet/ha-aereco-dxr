"""Number entities for Aereco Ventilation System."""
from typing import Optional, Dict, Any

from homeassistant.components.number import (
    NumberEntity,
    NumberDeviceClass,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfTime, UnitOfVolumeFlowRate

from . import AerecoDataUpdateCoordinator
from .const import (
    DOMAIN, 
    MODE_NAMES,
    POST_SYSTEM_AIRFLOW,  # System-wide airflow setting
    GET_OPERATION_MODES_CONFIG,
    DEFAULT_TIMEOUT_VALUES,
    DEFAULT_AIRFLOW_VALUES,
    MODE_AUTOMATIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Aereco number entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    # Separate timeout entities for better UX
    # Hours timeout for Free Cooling, Boost, Stop modes
    entities.extend([
        AerecoModeTimeoutHoursNumber(coordinator, entry, "timeout_hours", "Mode Timeout (Hours)", "DYNAMIC"),
    ])
    
    # Days timeout for Absence mode  
    entities.extend([
        AerecoModeTimeoutDaysNumber(coordinator, entry, "timeout_days", "Mode Timeout (Days)", "DYNAMIC"),
    ])
    
    # System-wide airflow that applies to all modes
    entities.extend([
        AerecoSystemAirflowNumber(coordinator, entry, "system", "System Airflow", POST_SYSTEM_AIRFLOW),
    ])
    
    async_add_entities(entities, update_before_add=True)


class AerecoBaseNumber(CoordinatorEntity, NumberEntity):
    """Base number entity for Aereco system."""

    def __init__(
        self, 
        coordinator: AerecoDataUpdateCoordinator, 
        entry: ConfigEntry,
        key: str,
        name: str,
        post_command: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._key = key
        self._post_command = post_command
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Aereco Ventilation System",
            "manufacturer": "Aereco",
            "model": "DXR",
        }


class AerecoModeTimeoutHoursNumber(AerecoBaseNumber):
    """Number entity for timeout configuration in hours (Free Cooling, Boost, Stop)."""

    def __init__(
        self,
        coordinator: AerecoDataUpdateCoordinator,
        entry: ConfigEntry,
        mode_key: str,
        name: str,
        post_command: str,
    ) -> None:
        """Initialize the timeout hours number entity."""
        super().__init__(coordinator, entry, f"{mode_key}", name, post_command)
        self._mode_key = mode_key
        self._attr_native_min_value = 1
        self._attr_native_max_value = 24  # Max 24 hours
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = UnitOfTime.HOURS
        self._attr_device_class = NumberDeviceClass.DURATION
        self._attr_mode = NumberMode.BOX
        self._attr_icon = "mdi:timer-outline"
        self._attr_entity_registry_enabled_default = True

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success and 
            self.coordinator.data is not None
        )

    @property
    def native_value(self) -> Optional[float]:
        """Return the current timeout value in hours."""
        current_mode = self.coordinator.data.get("current_mode", {}).get("mode")
        
        # Only show value for applicable modes
        if current_mode not in ["1", "2", "4"]:  # Free Cooling, Boost, Stop
            return None
            
        # Get default timeout value for current mode
        default_timeout = DEFAULT_TIMEOUT_VALUES.get(current_mode, 2)
        
        # Check if mode has changed since last update
        if hasattr(self, '_last_mode') and self._last_mode != current_mode:
            # Mode changed - clear stored value to show new mode's default
            if hasattr(self, '_last_timeout_value'):
                delattr(self, '_last_timeout_value')
        
        # Store current mode for next comparison
        self._last_mode = current_mode
        
        # Return stored value or default for current mode
        if hasattr(self, '_last_timeout_value') and self._last_timeout_value is not None:
            return self._last_timeout_value
        else:
            return default_timeout

    async def async_set_native_value(self, value: float) -> None:
        """Set the timeout value and apply it to current mode."""
        current_mode = self.coordinator.data.get("current_mode", {}).get("mode")
        if not current_mode or current_mode not in ["1", "2", "4"]:
            return
            
        # Store the value for display
        self._last_timeout_value = value
        self._last_mode = current_mode
        
        # Determine POST command based on current mode
        mode_timeout_commands = {
            "1": "02",  # Free Cooling -> POST_FREE_COOLING_MODE_TIMEOUT
            "2": "04",  # Boost -> POST_BOOST_MODE_TIMEOUT  
            "4": "08",  # Stop -> POST_STOP_MODE_TIMEOUT
        }
        
        post_command = mode_timeout_commands.get(current_mode)
        if not post_command:
            return
            
        # Send to settings.html
        success = await self.coordinator.api.set_mode_timeout_direct(post_command, int(value))
        
        if success:
            await self.coordinator.async_request_refresh()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        super()._handle_coordinator_update()


class AerecoModeTimeoutDaysNumber(AerecoBaseNumber):
    """Number entity for timeout configuration in days (Absence mode)."""

    def __init__(
        self,
        coordinator: AerecoDataUpdateCoordinator,
        entry: ConfigEntry,
        mode_key: str,
        name: str,
        post_command: str,
    ) -> None:
        """Initialize the timeout days number entity."""
        super().__init__(coordinator, entry, f"{mode_key}", name, post_command)
        self._mode_key = mode_key
        self._attr_native_min_value = 1
        self._attr_native_max_value = 30  # Max 30 days
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = UnitOfTime.DAYS
        self._attr_device_class = NumberDeviceClass.DURATION
        self._attr_mode = NumberMode.BOX
        self._attr_icon = "mdi:calendar-clock"
        self._attr_entity_registry_enabled_default = True

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success and 
            self.coordinator.data is not None
        )

    @property
    def native_value(self) -> Optional[float]:
        """Return the current timeout value in days."""
        current_mode = self.coordinator.data.get("current_mode", {}).get("mode")
        
        # Only show value for Absence mode
        if current_mode != "3":  # Absence mode
            return None
            
        # Get default timeout value for Absence mode (1 day)
        default_timeout = DEFAULT_TIMEOUT_VALUES.get("3", 1)
        
        # Return stored value or default
        if hasattr(self, '_last_timeout_value') and self._last_timeout_value is not None:
            return self._last_timeout_value
        else:
            return default_timeout

    async def async_set_native_value(self, value: float) -> None:
        """Set the timeout value and apply it to Absence mode."""
        current_mode = self.coordinator.data.get("current_mode", {}).get("mode")
        if current_mode != "3":  # Only for Absence mode
            return
            
        # Store the value for display
        self._last_timeout_value = value
        
        # Send to settings.html (Absence timeout command)
        success = await self.coordinator.api.set_mode_timeout_direct("06", int(value))
        
        if success:
            await self.coordinator.async_request_refresh()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        super()._handle_coordinator_update()


class AerecoSystemAirflowNumber(AerecoBaseNumber):
    """Number entity for system-wide airflow configuration."""

    def __init__(
        self,
        coordinator: AerecoDataUpdateCoordinator,
        entry: ConfigEntry,
        mode_key: str,
        name: str,
        post_command: str,
    ) -> None:
        """Initialize the airflow number entity."""
        super().__init__(coordinator, entry, f"{mode_key}_airflow", name, post_command)
        self._mode_key = mode_key
        self._attr_native_min_value = 0
        self._attr_native_max_value = 500  # Typical max airflow in m³/h
        self._attr_native_step = 5
        self._attr_native_unit_of_measurement = UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR
        self._attr_mode = NumberMode.BOX
        self._attr_icon = "mdi:fan"
        self._attr_entity_registry_enabled_default = True

    @property
    def native_value(self) -> Optional[float]:
        """Return the current value."""
        current_mode = self.coordinator.data.get("current_mode", {}).get("mode")
        modes_config = self.coordinator.data.get("modes_config")
        
        if not modes_config:
            # Return the default airflow for current mode, fallback to Automatic mode default
            return DEFAULT_AIRFLOW_VALUES.get(current_mode, DEFAULT_AIRFLOW_VALUES.get(MODE_AUTOMATIC, 60))
            
        config_key = f"{self._mode_key}_airflow"
        stored_value = modes_config.get(config_key)
        
        if stored_value is not None:
            return stored_value
        else:
            # No stored value, return default for current mode
            return DEFAULT_AIRFLOW_VALUES.get(current_mode, DEFAULT_AIRFLOW_VALUES.get(MODE_AUTOMATIC, 60))

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        success = await self.coordinator.api.set_system_airflow(int(value))
        if success:
            await self.coordinator.async_request_refresh()

    @property
    def native_max_value(self) -> float:
        """Return the maximum value based on mode."""
        # Different modes might have different max values
        if self._mode_key == "boost":
            return 500
        elif self._mode_key == "absence":
            return 100  # Lower max for absence mode
        elif self._mode_key == "stop":
            return 50   # Very low for stop mode
        else:
            return 300  # Default max for automatic and free cooling

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Available if we have coordinator data
        return (
            self.coordinator.last_update_success and 
            self.coordinator.data is not None
        )