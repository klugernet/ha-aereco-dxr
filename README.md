# Aereco Ventilation System - Home Assistant Integration

This Home Assistant integration allows you to control and monitor an Aereco ventilation system (DXR) through Home Assistant.

## Features

### 🌬️ Ventilation Control
- **Fan Entity**: Complete control of the ventilation system as a fan entity
- **Operation Modes**: Automatic, Free Cooling, Boost, Absence, Stop
- **Speed Control**: Percentage-based speed control
- **Preset Modes**: Quick mode switching via preset functions

### 📊 Sensors
- **System Sensors**:
  - Airflow (m³/h)
  - Filter clogging level (%)
  - Mode timeout (min/h/d)
  
- **Room Sensors** (automatically detected):
  - CO2 sensors (ppm)
  - Humidity sensors
  - Temperature sensors per room (°C/°F)

### ⚙️ Advanced Control
- **Select Entity**: Direct mode selection
- **Maintenance Info**: Filter status, bypass valve, preheater level
- **Warnings**: Automatic display of system warnings

## Installation

### HACS (recommended)
1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click on the three dots in the top right and select "Custom repositories"
4. Add this repository URL: `https://github.com/klugernet/ha-aereco-dxr`
5. Select the category "Integration"
6. Search for "Aereco Ventilation System" and install it
7. Restart Home Assistant

### Manual Installation
1. Copy the `custom_components/aereco_ventilation` folder into the `custom_components` directory of your Home Assistant installation
2. Restart Home Assistant
3. Go to "Settings" > "Devices & Services"
4. Click on "Add Integration"
5. Search for "Aereco Ventilation System"

## Configuration

### Initial Setup
1. Go to "Settings" > "Devices & Services"
2. Click on "Add Integration"
3. Search for "Aereco Ventilation System"
4. Enter the required information:
   - **IP Address**: The IP address of your Aereco system
   - **Port**: Port for HTTP communication (default: 80)
   - **Update Interval**: How often data should be fetched (default: 30 seconds)

### Finding the IP Address
You can find the IP address of your Aereco system as follows:
- Check the network settings on the system display
- Use a network scanner like "Fing" or "Network Scanner"
- Check your router's DHCP client list

## Usage

### Control as Fan
```yaml
# Example automation: Boost mode when cooking
automation:
  - alias: "Kitchen Boost When Cooking"
    trigger:
      - platform: state
        entity_id: binary_sensor.kitchen_motion
        to: 'on'
    condition:
      - condition: time
        after: '17:00:00'
        before: '21:00:00'
    action:
      - service: fan.set_preset_mode
        target:
          entity_id: fan.aereco_ventilation_system
        data:
          preset_mode: "Boost"
```

### Using Mode Selection
```yaml
# Example: Activate absence mode during vacation
automation:
  - alias: "Vacation Ventilation"
    trigger:
      - platform: state
        entity_id: input_boolean.vacation
        to: 'on'
    action:
      - service: select.select_option
        target:
          entity_id: select.aereco_operation_mode  
        data:
          option: "Absence"
```

### Monitor Sensors
```yaml
# Example: Warning for high CO2 levels
automation:
  - alias: "CO2 Warning"
    trigger:
      - platform: numeric_state
        entity_id: sensor.living_room_co2
        above: 1000
    action:
      - service: notify.mobile_app_my_phone
        data:
          message: "CO2 level in living room too high: {{ states('sensor.living_room_co2') }} ppm"
```

## Supported Devices

This integration was developed and tested with:
- **Aereco DXR** ventilation systems
- Firmware versions: All common versions
- Sensor types: CO2, Humidity (PYRO), Temperature

## API Reference

The integration is based on the HTTP API of the Aereco system:

### GET Commands
- `00`: Get warnings
- `02`: Current operation mode
- `05`: Maintenance data  
- `06`: Sensor data
- `11`: System version
- `13`: Temperature unit

### POST Commands
- `15`: Set operation mode (0=Auto, 1=Free Cooling, 2=Boost, 3=Absence, 4=Stop)

## Troubleshooting

### Connection Issues
- **Check IP Address**: Make sure the IP address is correct
- **Network Connectivity**: Test the connection with `ping <IP-address>`
- **Firewall**: Check if port 80 is open between Home Assistant and the Aereco system

### No Sensors Visible
- **Sensor Detection**: It may take a few minutes for all sensors to be detected
- **Room Names**: Configure room names on the Aereco system for better display
- **Sensor Types**: Not all sensor slots need to be occupied

### Check Logs
Enable debug logging for more detailed information:

```yaml
logger:
  default: info
  logs:
    custom_components.aereco_ventilation: debug
```

## Changelog

### Version 1.0.0
- ✨ Initial release
- 🌬️ Fan entity with complete control
- 📊 Sensor support for CO2, humidity, temperature
- ⚙️ Select entity for mode selection
- 🌍 German translation
- 📝 Comprehensive documentation

## Contributing

Contributions are welcome! Please:
1. Fork this repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues or questions:
- 🐛 **Issues**: [GitHub Issues](https://github.com/klugernet/ha-aereco-dxr/issues)
- 💬 **Community**: [Home Assistant Community](https://community.home-assistant.io/)
- 📧 **Email**: your-email@example.com

## Credits

Developed with ❤️ for the Home Assistant Community.

Based on analysis of the original Aereco web application.