#include "Device.h"

namespace lovi {

Device::Device(const char* name, DeviceType type, const char* firmwareVersion)
    : _name(name)
    , _firmwareVersion(firmwareVersion)
    , _type(type)
    , _mdns(nullptr)
    , _apiServer(nullptr)
    , _mdnsStarted(false)
    , _apiServerStarted(false) {
    
    _capabilities.hasPresence = false;
    _capabilities.hasMotion = false;
    _capabilities.hasTemperature = false;
    _capabilities.hasHumidity = false;
    _capabilities.hasSensitivity = false;
    _capabilities.maxDistance = 0.0f;
}

void Device::begin() {
    Serial.print("Device initialized: ");
    Serial.println(_name);
}

void Device::update() {
    if (_mdnsStarted && _mdns) {
        _mdns->update();
    }
    if (_apiServerStarted && _apiServer) {
        _apiServer->update();
    }
}

const char* Device::getName() const {
    return _name;
}

const char* Device::getTypeString() const {
    switch (_type) {
        case DeviceType::PRESENCE_GEN_ONE:
            return "presence_gen_one";
        case DeviceType::TEST_DEVICE:
            return "test_device";
        default:
            return "unknown";
    }
}

const char* Device::getFirmwareVersion() const {
    return _firmwareVersion;
}

const DeviceInfo::Capabilities& Device::getCapabilities() const {
    return _capabilities;
}

const SensorData& Device::getSensorData() const {
    return _sensorData;
}

void Device::_setCapabilities(const DeviceInfo::Capabilities& caps) {
    _capabilities = caps;
}

void Device::_setSensorData(const SensorData& data) {
    _sensorData = data;
}

void Device::startMDNS(uint16_t port) {
    if (!_mdnsStarted) {
        _mdns = new MDNSAdvertiser();
        _mdns->begin(_name, _firmwareVersion, port);
        _mdnsStarted = true;
    }
}

void Device::updateMDNS() {
    if (_mdns) {
        _mdns->update();
    }
}

void Device::stopMDNS() {
    if (_mdns) {
        _mdns->stop();
        delete _mdns;
        _mdns = nullptr;
    }
    _mdnsStarted = false;
}

void Device::startAPIServer(uint16_t port) {
    if (!_apiServerStarted) {
        _apiServer = new APIServer(this, port);
        _apiServer->begin();
        _apiServerStarted = true;
    }
}

void Device::updateAPIServer() {
    if (_apiServer) {
        _apiServer->update();
    }
}

void Device::stopAPIServer() {
    if (_apiServer) {
        _apiServer->stop();
        delete _apiServer;
        _apiServer = nullptr;
    }
    _apiServerStarted = false;
}

}
