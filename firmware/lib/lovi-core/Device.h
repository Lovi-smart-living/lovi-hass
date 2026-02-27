#pragma once

#include <Arduino.h>
#include <ESP8266WiFi.h>
#include "types.h"
#include "MDNSAdvertiser.h"
#include "APIServer.h"

namespace lovi {

class Device {
public:
    Device(const char* name, DeviceType type, const char* firmwareVersion);
    virtual ~Device() = default;

    virtual void begin();
    virtual void update();

    const char* getName() const;
    const char* getTypeString() const;
    DeviceType getType() const { return _type; }
    const char* getFirmwareVersion() const;
    const DeviceInfo::Capabilities& getCapabilities() const;
    const SensorData& getSensorData() const;

    void startMDNS(uint16_t port = 80);
    void updateMDNS();
    void stopMDNS();

    void startAPIServer(uint16_t port = 80);
    void updateAPIServer();
    void stopAPIServer();

protected:
    void _setCapabilities(const DeviceInfo::Capabilities& caps);
    void _setSensorData(const SensorData& data);

private:
    const char* _name;
    const char* _firmwareVersion;
    DeviceType _type;
    DeviceInfo::Capabilities _capabilities;
    SensorData _sensorData;
    MDNSAdvertiser* _mdns;
    APIServer* _apiServer;
    bool _mdnsStarted;
    bool _apiServerStarted;
};

}
