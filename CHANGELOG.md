# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2025-09-29

### Fixed
- Removed incorrect humidity sensor references from documentation
- Updated README.md and CHANGELOG.md to accurately reflect supported sensors (CO2, Temperature only)

## [1.1.0] - 2025-09-29

### Added
- **Number Entities**: Configuration controls for mode timeouts and airflows
  - Free Cooling timeout configuration (1-999 minutes)
  - Boost mode timeout configuration (1-999 minutes)
  - Absence mode timeout configuration (1-999 minutes)
  - Stop mode timeout configuration (1-999 minutes)
  - Automatic mode airflow configuration (0-300 m³/h)
  - Free Cooling airflow configuration (0-300 m³/h)
  - Boost mode airflow configuration (0-500 m³/h)
  - Absence mode airflow configuration (0-100 m³/h)
  - Stop mode airflow configuration (0-50 m³/h)
- **Extended API**: New methods for reading and setting mode configurations
  - `get_operation_modes_config()` - Fetch current mode settings
  - `set_mode_timeout()` - Configure mode timeout
  - `set_mode_airflow()` - Configure mode airflow
- **Enhanced Dashboard Support**: Dashboard examples for mode configuration
- **Version Information**: Added version tracking in device info

### Changed
- Updated documentation with mode configuration examples
- Enhanced HACS integration with number domain support
- Improved translations for German and English

### Technical
- Added POST commands for all mode configuration parameters
- Extended DataUpdateCoordinator to fetch mode configurations
- Added number platform to PLATFORMS list
- Updated manifest.json with proper version tracking

## [1.0.0] - 2025-09-29

### Added
- **Initial Release** 🎉
- **Fan Entity**: Complete ventilation system control
  - On/Off functionality
  - Speed control (0-100%)
  - Preset modes (Automatic, Free Cooling, Boost, Absence, Stop)
- **Sensor Entities**: Comprehensive monitoring
  - System sensors (airflow, filter level, timeout)
  - Room sensors (CO2, temperature)
  - Automatic sensor detection and room naming
- **Select Entity**: Direct operation mode selection
- **API Integration**: HTTP-based communication with Aereco DXR systems
  - GET commands for status and sensor data
  - POST commands for mode control
  - Hex data conversion and processing
- **HACS Support**: Full Home Assistant Community Store integration
- **Multi-language Support**: German and English translations
- **Configuration Flow**: Easy setup through Home Assistant UI
- **Documentation**: Comprehensive README and installation guide

### Supported Systems
- Aereco DXR ventilation systems
- All common firmware versions
- CO2, humidity (PYRO), and temperature sensors

### Technical Features
- Local polling (no cloud dependency)
- Robust error handling and connection management
- Automatic device discovery and configuration
- Real-time status updates and sensor monitoring

[1.1.0]: https://github.com/klugernet/ha-aereco-dxr/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/klugernet/ha-aereco-dxr/releases/tag/v1.0.0