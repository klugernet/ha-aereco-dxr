"""Sensor entities for Aereco Ventilation System."""
from typing import Optional, Dict, Any
from datetime import datetime

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfTemperature, CONCENTRATION_PARTS_PER_MILLION, PERCENTAGE

from . import AerecoDataUpdateCoordinator
from .const import DOMAIN, SENSOR_TYPE_CO2, SENSOR_TYPE_PYRO, SENSOR_TYPE_NAMES


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Aereco sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    # Add main system sensors
    entities.append(AerecoSystemSensor(coordinator, entry, "airflow", "Airflow", "m³/h"))
    entities.append(AerecoSystemSensor(coordinator, entry, "filter_level", "Filter Clogging Level", PERCENTAGE))
    entities.append(AerecoSystemSensor(coordinator, entry, "timeout", "Mode Timeout", "min"))
    
    # Add room sensors based on available sensor data
    if coordinator.data and "sensors" in coordinator.data:
        sensors_data = coordinator.data["sensors"]
        if sensors_data and "sensors" in sensors_data:
            room_names = await coordinator.api.get_room_names()
            
            for sensor_info in sensors_data["sensors"]:
                sensor_id = sensor_info["id"]
                sensor_type = sensor_info["type"]
                duct = sensor_info["duct"]
                
                room_name = room_names.get(duct, f"Room {duct + 1}")
                
                # Create appropriate sensor based on type
                if sensor_type == SENSOR_TYPE_CO2:
                    entities.append(AerecoRoomSensor(
                        coordinator, entry, sensor_id, "co2", 
                        f"{room_name} CO2", CONCENTRATION_PARTS_PER_MILLION,
                        SensorDeviceClass.CO2
                    ))
                elif sensor_type == SENSOR_TYPE_PYRO:
                    entities.append(AerecoRoomSensor(
                        coordinator, entry, sensor_id, "humidity",
                        f"{room_name} Humidity", None, None
                    ))
                
                # Always add temperature sensor for each room
                entities.append(AerecoRoomSensor(
                    coordinator, entry, sensor_id, "temperature",
                    f"{room_name} Temperature", None, SensorDeviceClass.TEMPERATURE
                ))
    
    async_add_entities(entities, update_before_add=True)


class AerecoBaseSensor(CoordinatorEntity, SensorEntity):
    """Base sensor for Aereco system."""

    def __init__(
        self, 
        coordinator: AerecoDataUpdateCoordinator, 
        entry: ConfigEntry,
        sensor_key: str,
        name: str,
        unit: Optional[str] = None
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_key = sensor_key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"{entry.entry_id}_{sensor_key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Aereco Ventilation System",
            "manufacturer": "Aereco",
            "model": "DXR",
        }


class AerecoSystemSensor(AerecoBaseSensor):
    """System-level sensor for Aereco ventilation."""

    def __init__(
        self,
        coordinator: AerecoDataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_key: str,
        name: str,
        unit: Optional[str] = None,
        device_class: Optional[SensorDeviceClass] = None,
    ) -> None:
        """Initialize the system sensor."""
        super().__init__(coordinator, entry, sensor_key, name, unit)
        self._attr_device_class = device_class
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_unit_of_measurement(self) -> Optional[str]:
        """Return the unit of measurement for dynamic timeout display."""
        if self._sensor_key == "timeout":
            mode_data = self.coordinator.data.get("current_mode", {})
            timeout_unit = mode_data.get("timeout_unit", 1)  # Default to minutes
            current_mode_num = mode_data.get("current_mode")
            
            # Special handling for Absence mode - always show days
            if current_mode_num == 3:  # Absence mode
                return "d"  # Always display as days for Absence mode
            
            unit_map = {0: "s", 1: "min", 2: "h", 3: "d"}
            return unit_map.get(timeout_unit, "min")
        
        return self._attr_native_unit_of_measurement

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        if self._sensor_key == "airflow":
            mode_data = self.coordinator.data.get("current_mode", {})
            return mode_data.get("airflow")
            
        elif self._sensor_key == "filter_level":
            maintenance_data = self.coordinator.data.get("maintenance", {})
            return maintenance_data.get("filter_clogging_level")
            
        elif self._sensor_key == "timeout":
            mode_data = self.coordinator.data.get("current_mode", {})
            current_mode = mode_data.get("mode_name", "").lower()
            current_mode_num = mode_data.get("current_mode")
            
            # Automatic mode has no timeout
            if current_mode == "automatic":
                return None
            
            timeout_value = mode_data.get("timeout")
            timeout_unit = mode_data.get("timeout_unit", 1)  # Default to minutes
            
            # Convert based on timeout_unit for better display
            if timeout_unit == 3:  # Days - system returns days directly (for larger values ≥5 days)
                return timeout_value
            elif current_mode_num == 3 and timeout_unit == 2:  # Absence mode with hours (≤4 days)
                # System returns hours directly (e.g., 95 hours), convert to days
                days_value = round(timeout_value / 24, 1) if timeout_value else None
                return days_value
            elif timeout_unit == 2:  # Hours - convert minutes to hours (other modes)
                return round(timeout_value / 60, 1) if timeout_value else None
            else:  # Minutes or seconds - keep as is
                return timeout_value
            
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        attributes = {}
        
        if self._sensor_key == "timeout":
            mode_data = self.coordinator.data.get("current_mode", {})
            timeout_unit = mode_data.get("timeout_unit", 0)
            unit_map = {0: "sec", 1: "min", 2: "hour", 3: "day"}
            attributes["timeout_unit"] = unit_map.get(timeout_unit, "min")
            
        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if self._sensor_key == "timeout":
            # Timeout sensor is only available when not in automatic mode
            mode_data = self.coordinator.data.get("current_mode", {})
            current_mode = mode_data.get("mode_name", "").lower()
            return (
                self.coordinator.last_update_success and 
                self.coordinator.data is not None and
                current_mode != "automatic"
            )
        
        return (
            self.coordinator.last_update_success and 
            self.coordinator.data is not None
        )


class AerecoRoomSensor(AerecoBaseSensor):
    """Room-level sensor for Aereco ventilation."""

    def __init__(
        self,
        coordinator: AerecoDataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_id: int,
        sensor_type: str,
        name: str,
        unit: Optional[str] = None,
        device_class: Optional[SensorDeviceClass] = None,
    ) -> None:
        """Initialize the room sensor."""
        unique_key = f"sensor_{sensor_id}_{sensor_type}"
        super().__init__(coordinator, entry, unique_key, name, unit)
        self._sensor_id = sensor_id
        self._sensor_type = sensor_type
        self._attr_device_class = device_class
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Optional[float]:
        """Return the native value of the sensor."""
        sensors_data = self.coordinator.data.get("sensors", {})
        if not sensors_data or "sensors" not in sensors_data:
            return None
            
        for sensor_info in sensors_data["sensors"]:
            if sensor_info["id"] == self._sensor_id:
                if self._sensor_type == "co2":
                    return sensor_info.get("value")  # Already converted to ppm in API
                elif self._sensor_type == "humidity":
                    return sensor_info.get("value")  # 0 or 1 for humidity threshold
                elif self._sensor_type == "temperature":
                    temp = sensor_info.get("temperature", 0)
                    # Convert to correct unit based on system setting
                    # This will need to be enhanced to check temperature unit setting
                    return temp
                    
        return None

    @property
    def native_unit_of_measurement(self) -> Optional[str]:
        """Return the unit of measurement."""
        if self._sensor_type == "temperature":
            # Get temperature unit from system
            return UnitOfTemperature.CELSIUS  # Default, should be dynamic
        return super().native_unit_of_measurement

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        sensors_data = self.coordinator.data.get("sensors", {})
        if not sensors_data or "sensors" not in sensors_data:
            return {}
            
        for sensor_info in sensors_data["sensors"]:
            if sensor_info["id"] == self._sensor_id:
                return {
                    "sensor_type": sensor_info.get("type_name"),
                    "duct": sensor_info.get("duct"),
                    "raw_value": sensor_info.get("raw_value"),
                }
                
        return {}