#pragma once

#include <Arduino.h>
#include <EEPROM.h>
#include "Device.h"

namespace lovi {

class ConfigManager {
public:
    ConfigManager();
    void begin();
    void loadConfig();
    void saveConfig();
    
    const char* getSSID() const;
    const char* getPassword() const;
    void setSSID(const char* ssid);
    void setPassword(const char* password);
    
    bool isConfigured() const;
    void clearConfig();

private:
    char _ssid[32];
    char _password[64];
    void _loadFromEEPROM();
    void _saveToEEPROM();
};

}
