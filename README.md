# Lovi Home Assistant Integration

[![HACS Default](https://img.shields.io/badge/HACS-Default-blue.svg)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/release/Lovi-smart-living/lovi-hass.svg)](https://github.com/Lovi-smart-living/lovi-hass/releases)
[![GitHub Issues](https://img.shields.io/github/issues/Lovi-smart-living/lovi-hass.svg)](https://github.com/Lovi-smart-living/lovi-hass/issues)

Home Assistant custom integration for Lovi IoT devices.

## Supported Devices

- **Presence Gen One** - WiFi Radar Human Presence Sensor

## Features

- 🌐 **Local-First** - All device control works locally without cloud
- 🔒 **Privacy-First** - No data sent to external servers
- 🔍 **Auto-Discovery** - Devices discovered automatically via mDNS
- 📊 **Rich Entities** - Presence, Motion, Distance, Uptime
- ⚙️ **Simple Controls** - LED on/off, Sensitivity adjustment

## Installation

### Option 1: HACS (Recommended)

1. Open Home Assistant
2. Go to **HACS** → **Integrations**
3. Click **⋮** → **Custom repositories**
4. Add: `https://github.com/Lovi-smart-living/lovi-hass`
5. Search for "Lovi" and install

### Option 2: Manual

1. Download the `lovi` folder
2. Copy to `/config/custom_components/` in your Home Assistant config
3. Restart Home Assistant

## Configuration

### Automatic Discovery

Once the integration is installed and your Lovi device is powered on:

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Lovi"
4. Your device should be auto-discovered via mDNS

### Manual Configuration

If auto-discovery doesn't work:

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Lovi"
4. Enter your device IP address manually

## Entities

After setup, you'll have these entities:

| Entity | Type | Description |
|--------|------|-------------|
| `binary_sensor.lovi_presence` | Binary Sensor | Presence detected |
| `binary_sensor.lovi_motion` | Binary Sensor | Motion detected |
| `sensor.lovi_distance` | Sensor | Distance to target (meters) |
| `sensor.lovi_uptime` | Sensor | Device uptime (seconds) |
| `switch.lovi_led` | Switch | LED indicator control |
| `number.lovi_sensitivity` | Number | Detection sensitivity (0-100%) |

## Device Settings

### LED Indicator
- Turn LED on/off from Home Assistant
- Default: On

### Sensitivity
- Adjust radar detection sensitivity (0-100%)
- Default: 50%
- Higher = more sensitive detection

## Support

- 🐛 **Issues**: https://github.com/Lovi-smart-living/lovi-hass/issues
- 📖 **Documentation**: https://github.com/Lovi-smart-living/lovi-hass#readme

## Credits

- Created by [Lovi IoT](https://lovi-iot.com)
- Built for Home Assistant

---

*This integration is provided as-is. For support, please open an issue on GitHub.*
