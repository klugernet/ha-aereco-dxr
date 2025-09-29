"""API client for Aereco Ventilation System."""
import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional, List
import urllib.parse

from .const import *

_LOGGER = logging.getLogger(__name__)


class AerecoAPI:
    """API client for communicating with Aereco ventilation system."""

    def __init__(self, host: str, port: int = 80):
        """Initialize the API client."""
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.session = None

    async def _get_session(self):
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
        return self.session

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

    def _convert_hex_stream_to_array(self, hex_string: str) -> List[int]:
        """Convert hex stream to integer array (similar to JS convertHexStreamToArray)."""
        if not hex_string or len(hex_string) % 2 != 0:
            return []
        
        result = []
        for i in range(0, len(hex_string), 2):
            hex_byte = hex_string[i:i+2]
            try:
                result.append(int(hex_byte, 16))
            except ValueError:
                result.append(0)
        return result

    def _hex_to_dec(self, hex_string: str) -> int:
        """Convert hex string to decimal."""
        try:
            return int(hex_string, 16)
        except ValueError:
            return 0

    async def _get_command(self, command: str) -> Optional[str]:
        """Execute GET command."""
        session = await self._get_session()
        url = f"{self.base_url}/{command}"
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    try:
                        text = await response.text()
                        return text.strip()
                    except UnicodeDecodeError as e:
                        # Some commands return binary data that can't be decoded as UTF-8
                        _LOGGER.debug(f"GET {command} returned binary data, cannot decode as text: {e}")
                        return None
                else:
                    _LOGGER.error(f"GET {command} failed with status {response.status}")
                    return None
        except Exception as e:
            _LOGGER.error(f"Error executing GET {command}: {e}")
            return None

    def _dec_to_hex(self, decimal_value: str) -> str:
        """Convert decimal string to 2-digit hex format (like decToHex in JS)."""
        try:
            dec_val = int(decimal_value)
            hex_val = format(dec_val, '02x')  # Convert to 2-digit hex with leading zero if needed
            return hex_val
        except ValueError:
            return "00"

    async def _post_command(self, command: str, value: str) -> bool:
        """Execute POST command."""
        session = await self._get_session()
        url = f"{self.base_url}/home.html"  # Original system uses home.html endpoint
        
        # Convert to hex format like the original JavaScript prepareDataForPost function
        # The format should be p_i=0f&p_v=00 (hex values, not decimal)
        try:
            hex_command = f"{int(command):02x}"  # Convert decimal to 2-digit hex
            hex_value = f"{int(value):02x}"      # Convert decimal to 2-digit hex
        except ValueError as e:
            _LOGGER.error(f"Invalid command or value for POST: command={command}, value={value}: {e}")
            return False
        
        # Use dictionary for proper application/x-www-form-urlencoded encoding
        data = {
            "p_i": hex_command,
            "p_v": hex_value
        }
        
        _LOGGER.debug(f"Sending POST {command} (hex: {hex_command}) with value {value} (hex: {hex_value}) to {url}")
        _LOGGER.debug(f"POST data: {data}")
        
        try:
            # aiohttp will automatically set Content-Type to application/x-www-form-urlencoded when data is dict
            async with session.post(url, data=data) as response:
                response_text = await response.text()
                success = response.status == 200
                
                _LOGGER.debug(f"POST {command} response status: {response.status}")
                _LOGGER.debug(f"POST {command} response text: {response_text[:100] if response_text else 'No content'}...")  # First 100 chars
                
                if success:
                    _LOGGER.debug(f"POST {command} successful")
                else:
                    _LOGGER.error(f"POST {command} failed with status {response.status}")
                return success
        except Exception as e:
            _LOGGER.error(f"Error executing POST {command} with value {value}: {e}")
            return False
            return False

    async def get_current_mode(self) -> Optional[Dict[str, Any]]:
        """Get current operation mode."""
        result = await self._get_command(GET_CURR_OPMODE)
        if not result:
            return None

        # Convert hex data to array (similar to modeRawDataConverter in h.js)
        data = self._convert_hex_stream_to_array(result)
        if len(data) < 5:
            return None

        return {
            "current_mode": data[0],
            "user_mode": data[1], 
            "timeout": data[2],
            "timeout_unit": data[3],
            "airflow": data[4],
            "raw_data": result
        }

    async def set_mode(self, mode: str) -> bool:
        """Set operation mode."""
        _LOGGER.debug(f"Setting mode to: {mode}")
        result = await self._post_command(POST_CURRENT_MODE, mode)
        _LOGGER.debug(f"Set mode result: {result}")
        return result

    async def get_sensors(self) -> Optional[Dict[str, Any]]:
        """Get sensor data."""
        result = await self._get_command(GET_SENSORS)
        if not result:
            return None

        # Convert sensors data (similar to sensorDataConverter in m.js)
        data = self._convert_hex_stream_to_array(result)
        sensors = []
        
        if len(data) >= 40:  # Need at least 40 bytes for full sensor data
            for i in range(MAX_DUCT):
                sensor_type = data[i + MAX_DUCT]
                if sensor_type in [1, 2, 3]:  # Valid sensor types
                    raw_value = data[i]
                    temp = data[i + 3 * MAX_DUCT] if len(data) > i + 3 * MAX_DUCT else 0
                    to_duct = data[i + 2 * MAX_DUCT] if len(data) > i + 2 * MAX_DUCT else i
                    
                    # Convert raw sensor value (similar to sensorValueRawToClientConverter)
                    if sensor_type == SENSOR_TYPE_CO2:
                        value = raw_value * 8 if raw_value else 0  # CO2 in ppm
                    elif sensor_type == SENSOR_TYPE_PYRO:
                        value = 1 if raw_value >= 162 else 0  # Humidity threshold
                    else:
                        value = raw_value

                    sensors.append({
                        "id": i,
                        "type": sensor_type,
                        "type_name": SENSOR_TYPE_NAMES.get(sensor_type, "Unknown"),
                        "value": value,
                        "raw_value": raw_value,
                        "temperature": temp,
                        "duct": to_duct
                    })

        return {
            "sensors": sensors,
            "raw_data": result
        }

    async def get_room_names(self) -> Dict[int, str]:
        """Get room names."""
        room_names = {}
        
        # Get room names (starting from GET_ROOM_NAME1 = "43")
        for i in range(MAX_DUCT):
            command_id = str(int(GET_ROOM_NAME1) + i)
            try:
                result = await self._get_command(command_id)
                if result and isinstance(result, str):
                    room_names[i] = result.strip()
                    _LOGGER.debug(f"Room {i}: '{result.strip()}'")
                else:
                    _LOGGER.debug(f"No room name found for command {command_id} (room {i})")
            except UnicodeDecodeError as e:
                _LOGGER.debug(f"Room name command {command_id} returned binary data, skipping: {e}")
            except Exception as e:
                _LOGGER.debug(f"Failed to get room name for command {command_id}: {e}")
        
        return room_names

    async def get_warnings(self) -> Optional[Dict[str, Any]]:
        """Get warning status."""
        result = await self._get_command(GET_WARNINGS)
        if not result:
            return None

        return {
            "raw_data": result,
            "has_warnings": len(result) > 0
        }

    async def get_maintenance_section(self) -> Optional[Dict[str, Any]]:
        """Get maintenance information."""
        result = await self._get_command(GET_MAINTENANCE_SECTION)
        if not result:
            return None

        # Convert maintenance data (similar to maintenanceSectionParamsRawDataConverter)
        data = self._convert_hex_stream_to_array(result)
        if len(data) < 5:
            return None

        maintenance_data = {
            "filter_clogging_level": data[0],
            "filter_reset": data[1],
            "filter_test": data[2], 
            "bypass_status": data[3],
            "preheater_level": data[4],
            "raw_data": result
        }
        
        if len(data) > 5:
            maintenance_data["f7_filter_clogging_level"] = data[5]
            
        return maintenance_data

    async def get_version(self) -> Optional[str]:
        """Get system version."""
        result = await self._get_command(GET_DXRVERS)
        if not result:
            return None
            
        data = self._convert_hex_stream_to_array(result)
        if len(data) > 0:
            version_map = {
                0: "DXR Basic",
                1: "DXR Premium", 
                2: "DXR Comfort",
                3: "DXR Plus"
            }
            return version_map.get(data[0], "Unknown")
        
        return "Unknown"

    async def get_temperature_unit(self) -> Optional[str]:
        """Get temperature unit setting."""
        result = await self._get_command(GET_TEMPERATURE_UNIT)
        if not result:
            return None
            
        data = self._convert_hex_stream_to_array(result)
        if len(data) > 0:
            return "°F" if data[0] == 1 else "°C"
        
        return "°C"

    async def test_connection(self) -> bool:
        """Test connection to the system."""
        try:
            result = await self._get_command(GET_CURR_OPMODE)
            return result is not None
        except Exception:
            return False

    async def get_operation_modes_config(self) -> Optional[Dict[str, Any]]:
        """Get operation modes configuration (timeouts and airflows)."""
        result = await self._get_command(GET_OPERATION_MODES_CONFIG)
        if not result:
            return None

        # Convert hex data to configuration values
        data = self._convert_hex_stream_to_array(result)
        if len(data) < 10:  # Need at least 10 bytes for basic config
            return None

        return {
            "automatic_airflow": data[0] if len(data) > 0 and data[0] > 0 else 60,  # Default 60
            "free_cooling_timeout": data[1] if len(data) > 1 else 60,
            "free_cooling_airflow": data[2] if len(data) > 2 and data[2] > 0 else 80,  # Default 80
            "boost_timeout": data[3] if len(data) > 3 else 30,
            "boost_airflow": data[4] if len(data) > 4 and data[4] > 0 else 120,  # Default 120
            "absence_timeout": data[5] if len(data) > 5 else 480,
            "absence_airflow": data[6] if len(data) > 6 and data[6] > 0 else 40,  # Default 40
            "stop_timeout": data[7] if len(data) > 7 else 0,
            "stop_airflow": data[8] if len(data) > 8 and data[8] > 0 else 0,  # Default 0
            "raw_data": result
        }

    async def set_mode_timeout(self, mode: str, timeout: int) -> bool:
        """Set timeout for a specific mode."""
        mode_timeout_commands = {
            "free_cooling": POST_FREE_COOLING_MODE_TIMEOUT,
            "boost": POST_BOOST_MODE_TIMEOUT,
            "absence": POST_ABSENCE_MODE_TIMEOUT,
            "stop": POST_STOP_MODE_TIMEOUT,
        }
        
        command = mode_timeout_commands.get(mode)
        if not command:
            return False
            
        return await self._post_command(command, str(timeout))

    async def set_mode_airflow(self, mode: str, airflow: int) -> bool:
        """Set airflow for a specific mode."""
        mode_airflow_commands = {
            "automatic": POST_AUTOMATIC_MODE_AIRFLOW,
            "free_cooling": POST_FREE_COOLING_MODE_AIRFLW,
            "boost": POST_BOOST_MODE_AIRFLOW,
            "absence": POST_ABSENCE_MODE_AIRFLOW,
            "stop": POST_STOP_MODE_AIRFLOW,
        }
        
        command = mode_airflow_commands.get(mode)
        if not command:
            return False
            
        return await self._post_command(command, str(airflow))