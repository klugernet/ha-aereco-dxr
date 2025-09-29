# Installation der Aereco HomeAssistant Integration

Diese Anleitung führt dich durch die Installation und Einrichtung der Aereco Lüftungssystem Integration für Home Assistant.

## Voraussetzungen

- Home Assistant 2023.1 oder neuer
- Aereco DXR Lüftungssystem mit Netzwerk-Anschluss
- Die IP-Adresse deines Aereco Systems

## Schritt 1: Integration installieren

### Option A: HACS (empfohlen)
1. **HACS öffnen**: Gehe zu HACS > Integrations
2. **Repository hinzufügen**:
   - Klicke auf die drei Punkte (⋮) oben rechts
   - Wähle "Custom repositories"
   - URL: `https://github.com/your-username/aereco-homeassistant`
   - Kategorie: "Integration"
   - Klicke "ADD"
3. **Integration installieren**:
   - Suche nach "Aereco Ventilation System"
   - Klicke "Download"
   - Wähle die neueste Version
4. **Home Assistant neustarten**

### Option B: Manuelle Installation
1. **Dateien herunterladen**:
   - Lade die neueste Release-Version herunter
   - Oder clone das Repository: `git clone https://github.com/your-username/aereco-homeassistant.git`

2. **Dateien kopieren**:
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

3. **Home Assistant neustarten**

## Schritt 2: IP-Adresse deines Aereco Systems finden

### Methode 1: System-Display
1. Navigiere am Aereco System zu den Netzwerk-Einstellungen
2. Notiere dir die angezeigte IP-Adresse

### Methode 2: Router-Interface
1. Logge dich in deinen Router ein
2. Suche in der DHCP-Client-Liste nach "Aereco" oder "DXR"
3. Notiere dir die IP-Adresse

### Methode 3: Netzwerk-Scanner
1. Verwende eine App wie "Fing" oder "Network Scanner"
2. Scanne dein lokales Netzwerk
3. Suche nach einem Gerät auf Port 80 mit HTTP-Server

### Methode 4: Kommandozeile (Windows)
```cmd
# Ping-Sweep für typische Router-Bereiche
for /L %i in (1,1,254) do ping -n 1 -w 1000 192.168.1.%i | find "TTL"
for /L %i in (1,1,254) do ping -n 1 -w 1000 192.168.0.%i | find "TTL"
```

## Schritt 3: Integration konfigurieren

1. **Integration hinzufügen**:
   - Gehe zu "Einstellungen" > "Geräte & Dienste"
   - Klicke auf "Integration hinzufügen"
   - Suche nach "Aereco Ventilation System"

2. **Konfiguration eingeben**:
   - **IP-Adresse**: Die IP-Adresse deines Aereco Systems (z.B. 192.168.1.100)
   - **Port**: 80 (Standard HTTP-Port)
   - **Aktualisierungsintervall**: 30 Sekunden (empfohlen)

3. **Verbindung testen**:
   - Klicke "Weiter"
   - Die Integration testet automatisch die Verbindung
   - Bei Erfolg wird das System hinzugefügt

## Schritt 4: Entities überprüfen

Nach erfolgreicher Installation findest du folgende Entities:

### Fan Entity
- `fan.aereco_ventilation_system`
  - Hauptsteuerung des Lüftungssystems
  - Unterstützt: Ein/Aus, Geschwindigkeit (%), Preset-Modi

### Select Entity  
- `select.aereco_operation_mode`
  - Direkte Modusauswahl
  - Optionen: Automatik, Freikühlung, Boost, Abwesenheit, Stop

### Sensor Entities
- `sensor.aereco_airflow` - Aktueller Luftstrom (m³/h)
- `sensor.aereco_filter_level` - Filter-Verstopfungsgrad (%)
- `sensor.aereco_timeout` - Aktuelles Modus-Timeout

### Raum-Sensoren (automatisch erkannt)
- `sensor.RAUMNAME_co2` - CO2-Gehalt (ppm)
- `sensor.RAUMNAME_humidity` - Luftfeuchtigkeit
- `sensor.RAUMNAME_temperature` - Temperatur (°C/°F)

## Schritt 5: Dashboard einrichten

### Basis-Karte
```yaml
type: entities
title: Lüftung
entities:
  - fan.aereco_ventilation_system
  - select.aereco_operation_mode
  - sensor.aereco_airflow
  - sensor.aereco_filter_level
```

### Erweiterte Steuerung
```yaml
type: horizontal-stack
cards:
  - type: fan-control
    entity: fan.aereco_ventilation_system
  - type: entity
    entity: select.aereco_operation_mode
    name: Modus
```

### Sensor-Übersicht
```yaml
type: grid
columns: 2
square: false
cards:
  - type: sensor
    entity: sensor.wohnzimmer_co2
    graph: line
  - type: sensor  
    entity: sensor.schlafzimmer_temperature
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
- **Warten**: Sensor-Erkennung kann bis zu 5 Minuten dauern
- **Neustart**: Starte die Integration neu über "Geräte & Dienste"
- **Sensor-Konfiguration**: Prüfe die Sensor-Konfiguration am Aereco System

### Debug-Logging aktivieren
```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.aereco_ventilation: debug
    custom_components.aereco_ventilation.api: debug
```

## Nächste Schritte

1. **Automatisierungen**: Erstelle Automatisierungen basierend auf CO2-Werten oder Tageszeiten
2. **Benachrichtigungen**: Richte Benachrichtigungen für Filterwarnungen ein  
3. **Energiemonitoring**: Überwache den Energieverbrauch des Systems
4. **Dashboard**: Gestalte dein Dashboard nach deinen Wünschen

## Support erhalten

- 📚 **Dokumentation**: Lies die vollständige README.md
- 🐛 **Issues**: Melde Probleme auf GitHub
- 💬 **Community**: Stelle Fragen im Home Assistant Forum
- 🚀 **Updates**: Halte die Integration über HACS aktuell

Viel Erfolg mit deiner neuen Aereco Integration! 🌬️