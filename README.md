# Aereco Ventilation System - Home Assistant Integration

Diese Home Assistant Integration ermöglicht es, ein Aereco Lüftungssystem (DXR) über Home Assistant zu steuern und zu überwachen.

## Funktionen

### 🌬️ Lüftungssteuerung
- **Fan Entity**: Vollständige Steuerung des Lüftungssystems als Fan-Entity
- **Betriebsmodi**: Automatik, Freikühlung, Boost, Abwesenheit, Stop
- **Geschwindigkeitskontrolle**: Prozentuale Geschwindigkeitssteuerung
- **Preset-Modi**: Schnelle Modusumschaltung über Preset-Funktionen

### 📊 Sensoren
- **System-Sensoren**:
  - Luftstrom (m³/h)
  - Filter-Verstopfungsgrad (%)
  - Modus-Timeout (min/h/d)
  
- **Raum-Sensoren** (automatisch erkannt):
  - CO2-Sensoren (ppm)
  - Luftfeuchtigkeit-Sensoren
  - Temperatursensoren pro Raum (°C/°F)

### ⚙️ Erweiterte Steuerung
- **Select Entity**: Direkte Modusauswahl
- **Wartungsinfos**: Filter-Status, Bypass-Ventil, Vorheizer-Level
- **Warnungen**: Automatische Anzeige von Systemwarnungen

## Installation

### HACS (empfohlen)
1. Öffne HACS in Home Assistant
2. Gehe zu "Integrations"
3. Klicke auf die drei Punkte oben rechts und wähle "Custom repositories"
4. Füge diese Repository-URL hinzu: `https://github.com/your-username/aereco-homeassistant`
5. Wähle die Kategorie "Integration"
6. Suche nach "Aereco Ventilation System" und installiere es
7. Starte Home Assistant neu

### Manuelle Installation
1. Kopiere den `custom_components/aereco_ventilation` Ordner in das `custom_components` Verzeichnis deiner Home Assistant Installation
2. Starte Home Assistant neu
3. Gehe zu "Einstellungen" > "Geräte & Dienste"
4. Klicke auf "Integration hinzufügen"
5. Suche nach "Aereco Ventilation System"

## Konfiguration

### Erstmalige Einrichtung
1. Gehe zu "Einstellungen" > "Geräte & Dienste"
2. Klicke auf "Integration hinzufügen"
3. Suche nach "Aereco Ventilation System"
4. Gib die erforderlichen Informationen ein:
   - **IP-Adresse**: Die IP-Adresse deines Aereco Systems
   - **Port**: Port für HTTP-Kommunikation (Standard: 80)
   - **Aktualisierungsintervall**: Wie oft Daten abgerufen werden sollen (Standard: 30 Sekunden)

### Ermittlung der IP-Adresse
Du kannst die IP-Adresse deines Aereco Systems folgendermaßen finden:
- Prüfe die Netzwerk-Einstellungen am System-Display
- Verwende einen Netzwerk-Scanner wie "Fing" oder "Network Scanner"
- Prüfe die DHCP-Client-Liste deines Routers

## Verwendung

### Als Lüfter steuern
```yaml
# Beispiel-Automatisierung: Boost-Modus beim Kochen
automation:
  - alias: "Küche Boost beim Kochen"
    trigger:
      - platform: state
        entity_id: binary_sensor.kueche_bewegung
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

### Modusauswahl verwenden
```yaml
# Beispiel: Abwesenheitsmodus bei Urlaub aktivieren
automation:
  - alias: "Urlaub Lüftung"
    trigger:
      - platform: state
        entity_id: input_boolean.urlaub
        to: 'on'
    action:
      - service: select.select_option
        target:
          entity_id: select.aereco_operation_mode  
        data:
          option: "Absence"
```

### Sensoren überwachen
```yaml
# Beispiel: Warnung bei hohem CO2-Gehalt
automation:
  - alias: "CO2 Warnung"
    trigger:
      - platform: numeric_state
        entity_id: sensor.wohnzimmer_co2
        above: 1000
    action:
      - service: notify.mobile_app_mein_handy
        data:
          message: "CO2-Gehalt im Wohnzimmer zu hoch: {{ states('sensor.wohnzimmer_co2') }} ppm"
```

## Unterstützte Geräte

Diese Integration wurde entwickelt und getestet mit:
- **Aereco DXR** Lüftungssystemen
- Firmware-Versionen: Alle gängigen Versionen
- Sensor-Typen: CO2, Luftfeuchtigkeit (PYRO), Temperatur

## API-Referenz

Die Integration basiert auf der HTTP-API des Aereco Systems:

### GET-Befehle
- `00`: Warnungen abrufen
- `02`: Aktueller Betriebsmodus
- `05`: Wartungsdaten  
- `06`: Sensor-Daten
- `11`: System-Version
- `13`: Temperatur-Einheit

### POST-Befehle
- `15`: Betriebsmodus setzen (0=Auto, 1=Free Cooling, 2=Boost, 3=Absence, 4=Stop)

## Fehlerbehebung

### Verbindungsprobleme
- **Prüfe die IP-Adresse**: Stelle sicher, dass die IP-Adresse korrekt ist
- **Netzwerk-Konnektivität**: Teste die Verbindung mit `ping <IP-Adresse>`
- **Firewall**: Prüfe, ob Port 80 zwischen Home Assistant und dem Aereco System offen ist

### Keine Sensoren sichtbar
- **Sensor-Erkennung**: Es kann einige Minuten dauern, bis alle Sensoren erkannt werden
- **Raum-Namen**: Konfiguriere Raum-Namen am Aereco System für bessere Anzeige
- **Sensor-Typen**: Nicht alle Sensor-Slots müssen belegt sein

### Logs prüfen
Aktiviere Debug-Logging für detailliertere Informationen:

```yaml
logger:
  default: info
  logs:
    custom_components.aereco_ventilation: debug
```

## Changelog

### Version 1.0.0
- ✨ Erste Veröffentlichung
- 🌬️ Fan Entity mit vollständiger Steuerung
- 📊 Sensor-Unterstützung für CO2, Luftfeuchtigkeit, Temperatur
- ⚙️ Select Entity für Modusauswahl
- 🌍 Deutsche Übersetzung
- 📝 Umfassende Dokumentation

## Mitwirken

Beiträge sind willkommen! Bitte:
1. Forke dieses Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/AmazingFeature`)
3. Committe deine Änderungen (`git commit -m 'Add some AmazingFeature'`)
4. Push zum Branch (`git push origin feature/AmazingFeature`)
5. Öffne einen Pull Request

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe die [LICENSE](LICENSE) Datei für Details.

## Support

Bei Problemen oder Fragen:
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-username/aereco-homeassistant/issues)
- 💬 **Community**: [Home Assistant Community](https://community.home-assistant.io/)
- 📧 **E-Mail**: your-email@example.com

## Credits

Entwickelt mit ❤️ für die Home Assistant Community.

Basierend auf der Analyse der originalen Aereco Web-Anwendung.