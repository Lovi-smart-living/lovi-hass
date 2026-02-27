#pragma once

#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>

namespace lovi {

class MDNSAdvertiser {
public:
    MDNSAdvertiser();
    ~MDNSAdvertiser() = default;

    void begin(const char* deviceName, const char* firmwareVersion, uint16_t port = 80);

    void update();
    void stop();

private:
    void _setDeviceProperties(const char* firmwareVersion);
    String _getMACAddress();
    bool _started;
};

}
