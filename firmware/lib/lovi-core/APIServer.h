#pragma once

#include <Arduino.h>
#include <ESP8266WebServer.h>
#include <ArduinoJson.h>
#include "types.h"

namespace lovi {

class Device;

class APIServer {
public:
    APIServer(Device* device, uint16_t port = 80);
    ~APIServer();

    void begin();
    void update();
    void stop();

    bool isRunning() const { return _server != nullptr; }

private:
    Device* _device;
    uint16_t _port;
    ESP8266WebServer* _server;

    void _handleDeviceInfo();
    void _handleData();
    void _handleNotFound();
    
    String _getMACAddress();
};

}
