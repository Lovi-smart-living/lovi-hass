#include "ConfigManager.h"

namespace lovi {

ConfigManager::ConfigManager() {
    _ssid[0] = '\0';
    _password[0] = '\0';
}

void ConfigManager::begin() {
    loadConfig();
}

void ConfigManager::loadConfig() {
    _loadFromEEPROM();
}

void ConfigManager::saveConfig() {
    _saveToEEPROM();
}

const char* ConfigManager::getSSID() const {
    return _ssid;
}

const char* ConfigManager::getPassword() const {
    return _password;
}

void ConfigManager::setSSID(const char* ssid) {
    strncpy(_ssid, ssid, sizeof(_ssid) - 1);
    _ssid[sizeof(_ssid) - 1] = '\0';
}

void ConfigManager::setPassword(const char* password) {
    strncpy(_password, password, sizeof(_password) - 1);
    _password[sizeof(_password) - 1] = '\0';
}

bool ConfigManager::isConfigured() const {
    return strlen(_ssid) > 0;
}

void ConfigManager::clearConfig() {
    _ssid[0] = '\0';
    _password[0] = '\0';
    _saveToEEPROM();
}

void ConfigManager::_loadFromEEPROM() {
    for (size_t i = 0; i < sizeof(_ssid); i++) {
        _ssid[i] = EEPROM.read(i);
    }
    for (size_t i = 0; i < sizeof(_password); i++) {
        _password[i] = EEPROM.read(sizeof(_ssid) + i);
    }
}

void ConfigManager::_saveToEEPROM() {
    for (size_t i = 0; i < sizeof(_ssid); i++) {
        EEPROM.write(i, _ssid[i]);
    }
    for (size_t i = 0; i < sizeof(_password); i++) {
        EEPROM.write(sizeof(_ssid) + i, _password[i]);
    }
    EEPROM.commit();
}

}
