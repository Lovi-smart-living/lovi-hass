#pragma once

#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <DNSServer.h>
#include <ESP8266WebServer.h>
#include "ConfigManager.h"
#include "LEDController.h"

namespace lovi {

class CaptivePortal {
public:
    CaptivePortal(uint8_t ledPin);
    ~CaptivePortal();

    void begin();
    void enterConfigMode();
    void update();

    bool isInConfigMode() const;
    ConfigManager* getConfigManager() { return _configManager; }

private:
    ConfigManager* _configManager;
    LEDController* _ledController;
    uint8_t _ledPin;
    
    bool _configMode;
    bool _started;
    DNSServer* _dnsServer;
    ESP8266WebServer* _webServer;
    
    void _setupAP();
    void _setupWebServer();
    void _handleRoot();
    void _handleSave();
    void _handleNotFound();
};

}
