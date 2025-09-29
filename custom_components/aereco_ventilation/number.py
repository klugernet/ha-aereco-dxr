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
    POST_AUTOMATIC_MODE_AIRFLOW,
    POST_FREE_COOLING_MODE_TIMEOUT,
    POST_FREE_COOLING_MODE_AIRFLW, 
    POST_BOOST_MODE_TIMEOUT,
    POST_BOOST_MODE_AIRFLOW,
    POST_ABSENCE_MODE_TIMEOUT,
    POST_ABSENCE_MODE_AIRFLOW,
    POST_STOP_MODE_TIMEOUT,
    POST_STOP_MODE_AIRFLOW,
    GET_OPERATION_MODES_CONFIG,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Aereco number entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    # Mode timeout settings
    entities.extend([
        AerecoModeTimeoutNumber(coordinator, entry, "free_cooling", "Free Cooling Timeout", POST_FREE_COOLING_MODE_TIMEOUT),
        AerecoModeTimeoutNumber(coordinator, entry, "boost", "Boost Mode Timeout", POST_BOOST_MODE_TIMEOUT),
        AerecoModeTimeoutNumber(coordinator, entry, "absence", "Absence Mode Timeout", POST_ABSENCE_MODE_TIMEOUT),
        AerecoModeTimeoutNumber(coordinator, entry, "stop", "Stop Mode Timeout", POST_STOP_MODE_TIMEOUT),
    ])
    
    # Mode airflow settings
    entities.extend([
        AerecoModeAirflowNumber(coordinator, entry, "automatic", "Automatic Mode Airflow", POST_AUTOMATIC_MODE_AIRFLOW),
        AerecoModeAirflowNumber(coordinator, entry, "free_cooling", "Free Cooling Airflow", POST_FREE_COOLING_MODE_AIRFLW),
        AerecoModeAirflowNumber(coordinator, entry, "boost", "Boost Mode Airflow", POST_BOOST_MODE_AIRFLOW),
        AerecoModeAirflowNumber(coordinator, entry, "absence", "Absence Mode Airflow", POST_ABSENCE_MODE_AIRFLOW),
        AerecoModeAirflowNumber(coordinator, entry, "stop", "Stop Mode Airflow", POST_STOP_MODE_AIRFLOW),
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
    """Number entity for mode timeout configuration."""

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
        self._attr_native_max_value = 999
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = UnitOfTime.MINUTES
        self._attr_device_class = NumberDeviceClass.DURATION
        self._attr_mode = NumberMode.BOX
        self._attr_icon = "mdi:timer-outline"
        self._attr_entity_registry_enabled_default = True

    @property
    def native_value(self) -> Optional[float]:
        """Return the current value."""
        modes_config = self.coordinator.data.get("modes_config")
        if not modes_config:
            return None
            
        config_key = f"{self._mode_key}_timeout"
        return modes_config.get(config_key)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        success = await self.coordinator.api.set_mode_timeout(self._mode_key, int(value))
        if success:
            await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Available if we have coordinator data and mode is supported
        return (
            self.coordinator.last_update_success and 
            self.coordinator.data is not None and
            self._mode_key in ["free_cooling", "boost", "absence", "stop"]
        )


class AerecoModeAirflowNumber(AerecoBaseNumber):
    """Number entity for mode airflow configuration."""

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
            return None
            
        config_key = f"{self._mode_key}_airflow"
        return modes_config.get(config_key)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        success = await self.coordinator.api.set_mode_airflow(self._mode_key, int(value))
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