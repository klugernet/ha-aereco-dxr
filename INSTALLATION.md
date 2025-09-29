# Installation of the Aereco HomeAssistant Integration

This guide will walk you through the installation and setup of the Aereco Ventilation System integration for Home Assistant.

## Prerequisites

- Home Assistant 2023.1 or newer
- Aereco DXR ventilation system with network connection
- The IP address of your Aereco system

## Step 1: Install Integration

### Option A: HACS (recommended)
1. **Open HACS**: Go to HACS > Integrations
2. **Add repository**:
   - Click on the three dots (⋮) in the top right
   - Select "Custom repositories"
   - URL: `https://github.com/klugernet/ha-aereco-dxr`
   - Category: "Integration"
   - Click "ADD"
3. **Install integration**:
   - Search for "Aereco Ventilation System"
   - Click "Download"
   - Select the latest version
4. **Restart Home Assistant**

### Option B: Manual Installation
1. **Download files**:
   - Download the latest release version
   - Or clone the repository: `git clone https://github.com/klugernet/ha-aereco-dxr.git`

2. **Copy files**:
   ```
   <config>/custom_components/aereco_ventilation/
   ├── __init__.py
   ├── api.py
   ├── config_flow.py
   ├── const.py
   ├── fan.py
   ├── manifest.json
   ├── select.py
   ├── sensor.py
   ├── strings.json
   └── translations/
       └── de.json
   ```

3. **Restart Home Assistant**

## Step 2: Find IP Address of Your Aereco System

### Method 1: System Display
1. Navigate to the network settings on your Aereco system
2. Note the displayed IP address

### Method 2: Router Interface
1. Log into your router
2. Look in the DHCP client list for "Aereco" or "DXR"
3. Note the IP address

### Method 3: Network Scanner
1. Use an app like "Fing" or "Network Scanner"
2. Scan your local network
3. Look for a device on port 80 with HTTP server

### Method 4: Command Line (Windows)
```cmd
# Ping sweep for typical router ranges
for /L %i in (1,1,254) do ping -n 1 -w 1000 192.168.1.%i | find "TTL"
for /L %i in (1,1,254) do ping -n 1 -w 1000 192.168.0.%i | find "TTL"
```

## Step 3: Configure Integration

1. **Add integration**:
   - Go to "Settings" > "Devices & Services"
   - Click on "Add Integration"
   - Search for "Aereco Ventilation System"

2. **Enter configuration**:
   - **IP Address**: The IP address of your Aereco system (e.g. 192.168.1.100)
   - **Port**: 80 (default HTTP port)
   - **Update Interval**: 30 seconds (recommended)

3. **Test connection**:
   - Click "Next"
   - The integration automatically tests the connection
   - On success, the system will be added

## Step 4: Check Entities

After successful installation, you will find the following entities:

### Fan Entity
- `fan.aereco_ventilation_system`
  - Main control of the ventilation system
  - Supports: On/Off, Speed (%), Preset modes

### Select Entity  
- `select.aereco_operation_mode`
  - Direct mode selection
  - Options: Automatic, Free Cooling, Boost, Absence, Stop

### Sensor Entities
- `sensor.aereco_airflow` - Current airflow (m³/h)
- `sensor.aereco_filter_level` - Filter clogging level (%)
- `sensor.aereco_timeout` - Current mode timeout

### Room Sensors (automatically detected)
- `sensor.ROOMNAME_co2` - CO2 level (ppm)
- `sensor.ROOMNAME_humidity` - Humidity
- `sensor.ROOMNAME_temperature` - Temperature (°C/°F)

### Number Entities (Mode Configuration)
- `number.aereco_free_cooling_timeout` - Free Cooling timeout (minutes)
- `number.aereco_boost_timeout` - Boost mode timeout (minutes)
- `number.aereco_absence_timeout` - Absence mode timeout (minutes)
- `number.aereco_stop_timeout` - Stop mode timeout (minutes)
- `number.aereco_automatic_airflow` - Automatic mode airflow (m³/h)
- `number.aereco_free_cooling_airflow` - Free Cooling airflow (m³/h)
- `number.aereco_boost_airflow` - Boost mode airflow (m³/h)
- `number.aereco_absence_airflow` - Absence mode airflow (m³/h)
- `number.aereco_stop_airflow` - Stop mode airflow (m³/h)

## Step 5: Setup Dashboard

### Basic Card
```yaml
type: entities
title: Ventilation
entities:
  - fan.aereco_ventilation_system
  - select.aereco_operation_mode
  - sensor.aereco_airflow
  - sensor.aereco_filter_level
```

### Advanced Control
```yaml
type: horizontal-stack
cards:
  - type: fan-control
    entity: fan.aereco_ventilation_system
  - type: entity
    entity: select.aereco_operation_mode
    name: Mode
```

### Sensor Overview
```yaml
type: grid
columns: 2
square: false
cards:
  - type: sensor
    entity: sensor.living_room_co2
    graph: line
  - type: sensor  
    entity: sensor.bedroom_temperature
    graph: line
  - type: gauge
    entity: sensor.aereco_filter_level
    min: 0
    max: 100
    severity:
      green: 0
      yellow: 60
      red: 80
```

### Mode Configuration Panel
```yaml
type: entities
title: Mode Settings
entities:
  - type: section
    label: Timeout Settings
  - entity: number.aereco_free_cooling_timeout
  - entity: number.aereco_boost_timeout
  - entity: number.aereco_absence_timeout
  - type: section
    label: Airflow Settings
  - entity: number.aereco_automatic_airflow
  - entity: number.aereco_free_cooling_airflow
  - entity: number.aereco_boost_airflow
  - entity: number.aereco_absence_airflow
```

## Fehlerbehebung

### Integration nicht verfügbar
- **Prüfe HACS**: Stelle sicher, dass HACS korrekt installiert ist
- **Cache leeren**: Lösche den Browser-Cache und starte HA neu
- **Logs prüfen**: Schaue in die Home Assistant Logs

### Verbindung fehlschlägt
```bash
# Teste die Verbindung manuell
curl http://IP-ADRESSE/02
# Sollte Hex-Daten zurückgeben, z.B. "0001001E64"
```

Häufige Probleme:
- **Falsche IP**: Prüfe die IP-Adresse erneut
- **Firewall**: Stelle sicher, dass Port 80 offen ist
- **Netzwerk**: HA und Aereco müssen im gleichen Netzwerk sein

### Sensoren fehlen
- **Wait**: Sensor detection can take up to 5 minutes
- **Restart**: Restart the integration via "Devices & Services"
- **Sensor configuration**: Check sensor configuration on the Aereco system

### Enable Debug Logging
```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.aereco_ventilation: debug
    custom_components.aereco_ventilation.api: debug
```

## Next Steps

1. **Automations**: Create automations based on CO2 values or time schedules
2. **Notifications**: Set up notifications for filter warnings  
3. **Energy monitoring**: Monitor the system's energy consumption
4. **Dashboard**: Customize your dashboard to your preferences

## Get Support

- 📚 **Documentation**: Read the complete README.md
- 🐛 **Issues**: Report problems on GitHub
- 💬 **Community**: Ask questions in the Home Assistant forum
- 🚀 **Updates**: Keep the integration up to date via HACS

Good luck with your new Aereco integration! 🌬️