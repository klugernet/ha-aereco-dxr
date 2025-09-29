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
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Aereco number entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    # Single timeout setting that applies to current mode
    # Absence mode uses days, other modes use hours/minutes
    entities.extend([
        AerecoModeTimeoutNumber(coordinator, entry, "mode_timeout", "Mode Timeout", "DYNAMIC"),
    ])
    
    # Mode airflow settings - system-wide airflow that applies to all modes
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


class AerecoModeTimeoutNumber(AerecoBaseNumber):
    """Number entity for universal mode timeout configuration."""

    def __init__(
        self,
        coordinator: AerecoDataUpdateCoordinator,
        entry: ConfigEntry,
        mode_key: str,
        name: str,
        post_command: str,
    ) -> None:
        """Initialize the timeout number entity."""
        super().__init__(coordinator, entry, f"{mode_key}_timeout", name, post_command)
        self._mode_key = mode_key
        self._attr_native_min_value = 1
        self._attr_native_step = 1
        self._attr_device_class = NumberDeviceClass.DURATION
        self._attr_mode = NumberMode.BOX
        self._attr_icon = "mdi:timer-outline"
        
        # This is a universal timeout that adapts to current mode
        # Default to hours, but will change based on current mode
        self._attr_native_unit_of_measurement = UnitOfTime.HOURS
        self._attr_native_max_value = 24  # Max 24 hours by default
        self._attr_entity_registry_enabled_default = True

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement based on current mode."""
        current_mode = self.coordinator.data.get("current_mode", {}).get("mode")
        
        # Absence mode uses days, others use hours
        if current_mode == "3":  # Absence mode
            return UnitOfTime.DAYS
        else:
            return UnitOfTime.HOURS

    @property
    def native_max_value(self) -> float:
        """Return max value based on current mode."""
        current_mode = self.coordinator.data.get("current_mode", {}).get("mode")
        
        # Absence mode: max 30 days, others: max 24 hours  
        if current_mode == "3":  # Absence mode
            return 30
        else:
            return 24

    @property
    def native_value(self) -> Optional[float]:
        """Return the current timeout value."""
        current_mode = self.coordinator.data.get("current_mode", {}).get("mode")
        
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
        if not current_mode:
            return
            
        # Store the value for display (this will be in the correct unit for the current mode)
        self._last_timeout_value = value
        self._last_mode = current_mode
        
        # Determine POST command based on current mode
        mode_timeout_commands = {
            "1": "02",  # Free Cooling -> POST_FREE_COOLING_MODE_TIMEOUT
            "2": "04",  # Boost -> POST_BOOST_MODE_TIMEOUT  
            "3": "06",  # Absence -> POST_ABSENCE_MODE_TIMEOUT
            "4": "08",  # Stop -> POST_STOP_MODE_TIMEOUT
        }
        
        post_command = mode_timeout_commands.get(current_mode)
        if not post_command:
            return
            
        # Send to settings.html as per user's observation
        success = await self.coordinator.api.set_mode_timeout_direct(post_command, int(value))
        
        if success:
            await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success and 
            self.coordinator.data is not None
        )

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # This will trigger a state update when coordinator data changes
        # which includes when the mode changes
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
        modes_config = self.coordinator.data.get("modes_config")
        if not modes_config:
            # Return a reasonable default for system airflow
            return 150  # Default system airflow in m³/h
            
        config_key = f"{self._mode_key}_airflow"
        return modes_config.get(config_key, 150)

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