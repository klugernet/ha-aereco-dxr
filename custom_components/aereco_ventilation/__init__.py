"""The Aereco Ventilation System integration."""
import logging
import asyncio
from datetime import timedelta
from typing import Dict, Any, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL
from .api import AerecoAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.FAN, Platform.SENSOR, Platform.SELECT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Aereco Ventilation System from a config entry."""
    host = entry.data["host"]
    port = entry.data.get("port", 80)
    update_interval = entry.data.get("update_interval", DEFAULT_UPDATE_INTERVAL)

    api = AerecoAPI(host, port)
    
    coordinator = AerecoDataUpdateCoordinator(hass, api, update_interval)
    
    # Test connection
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class AerecoDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: AerecoAPI,
        update_interval: int,
    ) -> None:
        """Initialize."""
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via library."""
        try:
            # Fetch all relevant data
            current_mode_data = await self.api.get_current_mode()
            sensors_data = await self.api.get_sensors()
            warnings_data = await self.api.get_warnings()
            maintenance_data = await self.api.get_maintenance_section()
            
            return {
                "current_mode": current_mode_data,
                "sensors": sensors_data,
                "warnings": warnings_data,
                "maintenance": maintenance_data,
            }
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err