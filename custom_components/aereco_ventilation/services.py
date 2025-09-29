"""Services for Aereco Ventilation System integration."""
import logging
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Aereco integration."""

    async def handle_set_mode_with_timeout(call: ServiceCall) -> None:
        """Handle set mode with custom timeout service."""
        device_id = call.data.get("device_id")
        mode = call.data.get("mode", "0")  # Default to automatic
        timeout = call.data.get("timeout", 60)  # Default 60 minutes
        timeout_unit = call.data.get("timeout_unit", "1")  # Default minutes

        if not device_id:
            raise HomeAssistantError("Device ID is required")

        # Get coordinator from device
        device_registry = dr.async_get(hass)
        device = device_registry.async_get(device_id)
        
        if not device:
            raise HomeAssistantError(f"Device {device_id} not found")

        # Find the coordinator for this device
        coordinator = None
        for entry_id, coord in hass.data[DOMAIN].items():
            if any(identifier[1] == entry_id for identifier in device.identifiers):
                coordinator = coord
                break

        if not coordinator:
            raise HomeAssistantError(f"No coordinator found for device {device_id}")

        try:
            # Set mode
            await coordinator.api.set_mode(mode)
            
            # Set timeout if different from current
            current_mode_data = await coordinator.api.get_current_mode()
            if current_mode_data:
                current_timeout = current_mode_data.get("timeout", 0)
                current_timeout_unit = current_mode_data.get("timeout_unit", 1)
                
                if current_timeout != timeout or current_timeout_unit != timeout_unit:
                    # Set custom timeout based on mode
                    timeout_commands = {
                        "1": "2",  # Free cooling timeout
                        "2": "4",  # Boost timeout  
                        "3": "6",  # Absence timeout
                        "4": "8",  # Stop timeout
                    }
                    
                    timeout_command = timeout_commands.get(mode)
                    if timeout_command:
                        await coordinator.api._post_command(timeout_command, str(timeout))
                        
            await coordinator.async_request_refresh()
            _LOGGER.info(f"Set mode {mode} with timeout {timeout} {timeout_unit} for device {device_id}")
            
        except Exception as err:
            raise HomeAssistantError(f"Failed to set mode: {err}") from err

    async def handle_reset_filter(call: ServiceCall) -> None:
        """Handle filter reset service."""
        device_id = call.data.get("device_id")
        
        if not device_id:
            raise HomeAssistantError("Device ID is required")

        # Get coordinator (same logic as above)
        device_registry = dr.async_get(hass)
        device = device_registry.async_get(device_id)
        
        if not device:
            raise HomeAssistantError(f"Device {device_id} not found")

        coordinator = None
        for entry_id, coord in hass.data[DOMAIN].items():
            if any(identifier[1] == entry_id for identifier in device.identifiers):
                coordinator = coord
                break

        if not coordinator:
            raise HomeAssistantError(f"No coordinator found for device {device_id}")

        try:
            # Reset filter (POST command 16)
            success = await coordinator.api._post_command("16", "1")
            if success:
                await coordinator.async_request_refresh()
                _LOGGER.info(f"Filter reset for device {device_id}")
            else:
                raise HomeAssistantError("Filter reset command failed")
                
        except Exception as err:
            raise HomeAssistantError(f"Failed to reset filter: {err}") from err

    async def handle_test_filter(call: ServiceCall) -> None:
        """Handle filter test service."""
        device_id = call.data.get("device_id")
        
        if not device_id:
            raise HomeAssistantError("Device ID is required")

        # Get coordinator (same logic as above)
        device_registry = dr.async_get(hass)
        device = device_registry.async_get(device_id)
        
        if not device:
            raise HomeAssistantError(f"Device {device_id} not found")

        coordinator = None
        for entry_id, coord in hass.data[DOMAIN].items():
            if any(identifier[1] == entry_id for identifier in device.identifiers):
                coordinator = coord
                break

        if not coordinator:
            raise HomeAssistantError(f"No coordinator found for device {device_id}")

        try:
            # Test filter (POST command 17)
            success = await coordinator.api._post_command("17", "1")
            if success:
                await coordinator.async_request_refresh()
                _LOGGER.info(f"Filter test initiated for device {device_id}")
            else:
                raise HomeAssistantError("Filter test command failed")
                
        except Exception as err:
            raise HomeAssistantError(f"Failed to test filter: {err}") from err

    # Register services
    hass.services.async_register(
        DOMAIN,
        "set_mode_with_timeout", 
        handle_set_mode_with_timeout,
        schema=vol.Schema({
            vol.Required("device_id"): str,
            vol.Optional("mode", default="0"): vol.In(["0", "1", "2", "3", "4"]),
            vol.Optional("timeout", default=60): vol.Range(min=1, max=999),
            vol.Optional("timeout_unit", default="1"): vol.In(["0", "1", "2", "3"]),
        })
    )

    hass.services.async_register(
        DOMAIN,
        "reset_filter",
        handle_reset_filter,
        schema=vol.Schema({
            vol.Required("device_id"): str,
        })
    )

    hass.services.async_register(
        DOMAIN,
        "test_filter", 
        handle_test_filter,
        schema=vol.Schema({
            vol.Required("device_id"): str,
        })
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services."""
    hass.services.async_remove(DOMAIN, "set_mode_with_timeout")
    hass.services.async_remove(DOMAIN, "reset_filter")
    hass.services.async_remove(DOMAIN, "test_filter")