# Lovi Integration Strategy

## Overview

This document outlines the strategic roadmap for Lovi IoT devices, covering Home Assistant integration, standalone usage, and future expansion plans.

---

## 1. Product Vision

Lovi smart sensors for human presence detection and environmental monitoring that:
- Work seamlessly with Home Assistant
- Can be used standalone with basic features
- Have a proprietary app with full features (future)
- Support multiple device types under one brand

---

## 2. Device Types

### Current
| Device Type | Description | Status |
|-------------|-------------|--------|
| `presence_gen_one` | Human Presence Sensor (radar-based) | ✅ Implemented |
| `temperature_humidity_sensor` | Temperature & Humidity Sensor | ✅ Implemented |

### Future Devices (Planned)
- Motion sensor variants
- Smart switch/plug with presence detection
- Multi-sensor combinations
- Custom form factors

---

## 3. Architecture

### Technology Stack
- **Hardware**: ESP8266 (current), ESP32 (future devices)
- **Connectivity**: WiFi (primary)
- **Protocol**: REST API over HTTP
- **Discovery**: mDNS/Zeroconf

### API Design

#### Standalone Mode (Limited - No Auth)
```
GET  /api/status     → Device status (presence, motion, distance, etc.)
GET  /api/device    → Device information
POST /api/led        → LED control (on/off only)
POST /api/settings  → Basic settings (limited)
```

#### Lovi App Mode (Full - Authenticated)
```
GET  /api/status     → Full device status
GET  /api/device    → Complete device info
POST /api/led       → Full LED control (brightness, effects)
POST /api/settings  → All settings (sensitivity, thresholds, etc.)
GET  /api/diagnostics → Device health info
POST /api/firmware   → OTA firmware update
GET  /api/stats     → Usage statistics
```

#### Authentication Flow
1. User registers device to Lovi account via app
2. Device stores API key/token
3. Authenticated requests include token
4. Unauthenticated requests limited to basic endpoints

---

## 4. Home Assistant Integration

### Brand Identity
- **Brand Name**: Lovi
- **Domain**: `lovi`
- **Logo**: Already present in `brands/lovi/`

### Configuration Flow

```
User adds "Lovi" integration
    │
    ▼
┌─────────────────────────────┐
│  1. mDNS Discovery          │
│  - Search for _lovi._tcp    │
│  - Found devices shown      │
└─────────────────────────────┘
    │
    ├── Found ──────────────────► Show discovered devices
    │                                └── Add device → Done
    │
    └── Not Found
              │
              ▼
┌─────────────────────────────┐
│  2. Retry / Manual Entry    │
│  - Search Again             │
│  - Enter IP manually        │
└─────────────────────────────┘
```

### Supported Platforms
- `sensor` - Distance, temperature, humidity, sensitivity, uptime
- `binary_sensor` - Presence, motion
- `switch` - LED control
- `number` - Sensitivity adjustment

### Discovery
- **Method**: Zeroconf/mDNS
- **Service Type**: `_lovi._tcp.local.`
- **Properties**: mac, model, device_type, firmware_version, capabilities

---

## 5. Standalone Usage

### User Flow

```
1. Power on device
       │
       ▼
2. Device starts in AP mode
       │
       ▼
3. User connects to "Lovi-XXXX" WiFi
       │
       ▼
4. Captive portal opens
       │
       ▼
5. User enters home WiFi credentials
       │
       ▼
6. Device connects to WiFi
       │
       ▼
7. Device accessible at:
   • http://lovi-XXXX.local/
   • http://<IP_ADDRESS>
```

### Basic API (No Authentication)
- Limited to essential features only
- No sensitivity adjustment
- LED on/off only
- No firmware updates
- No diagnostics

### Lovi App Integration (Future)
- Full feature access
- Account-based authentication
- Device registration/linking
- Cloud backup of settings

---

## 6. Implementation Roadmap

### Phase 1: Brand Setup ✅ Ready to Implement
- [ ] Create `brands/lovi.json` for Home Assistant brand page
- [ ] Verify brand logos are correct format

### Phase 2: Config Flow Enhancement ✅ Ready to Implement
- [ ] Improve zeroconf discovery flow
- [ ] Add device retry mechanism
- [ ] Better device naming (use model name)
- [ ] Add onboarding text/instructions
- [ ] Update translations

### Phase 3: Standalone Auth (Firmware)
- [ ] Implement API key storage on device
- [ ] Add authentication middleware
- [ ] Create limited API mode for unauthenticated requests

### Phase 4: Lovi App Platform (Future)
- [ ] User authentication system
- [ ] Device linking/registration flow
- [ ] Full API implementation
- [ ] Mobile app development
- [ ] OTA firmware update system

### Phase 5: Additional Devices (Future)
- [ ] New device type templates
- [ ] Registry pattern for easy addition
- [ ] HA platform implementations

---

## 7. File Structure

```
lovi-hass/
├── __init__.py              # Integration entry point
├── config_flow.py           # Configuration flow
├── manifest.json            # HA manifest
├── brands/
│   └── lovi/
│       ├── logo.png
│       ├── icon.png
│       ├── icon@2x.png
│       └── dark_logo.png
├── brands/
│   └── lovi.json            # Brand definition
├── translations/
│   └── en.json              # English strings
├── devices/
│   ├── base.py              # Base device class
│   ├── factory.py           # Device factory pattern
│   ├── registry.py          # Device registry
│   └── wifi/
│       ├── __init__.py
│       └── presence_gen_one.py
├── api/
│   ├── __init__.py
│   ├── client.py
│   └── exceptions.py
├── platforms/
│   ├── sensor.py
│   ├── binary_sensor.py
│   ├── switch.py
│   └── number.py
└── const.py
```

---

## 8. Key Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| HA Structure | Single integration (lovi) | All devices under one brand |
| Discovery | mDNS/Zeroconf primary | Standard HA discovery |
| Standalone | Limited API (no auth) | Simple, secure by default |
| App Auth | Account-based | Scalable, future-proof |
| Device Types | Registry pattern | Easy to add new devices |

---

## 9. Notes

- ESP8266 chosen for cost-effectiveness
- REST API chosen for simplicity and broad compatibility
- mDNS for zero-config discovery
- Standalone mode prioritizes simplicity over features
- Lovi app provides full control for power users

---

## 10. References

- HA Brand Guidelines: https://developers.home-assistant.io/docs/creating_integration_brand/
- HA Config Flow: https://developers.home-assistant.io/docs/config_entries_config_flow_handler/
- ESPHome: https://esphome.io/

---

*Last Updated: 2026-02-27*
*Document Version: 1.0*
