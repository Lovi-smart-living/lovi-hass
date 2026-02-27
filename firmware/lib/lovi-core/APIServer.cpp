#include "APIServer.h"
#include "Device.h"

namespace lovi {

APIServer::APIServer(Device* device, uint16_t port)
    : _device(device)
    , _port(port)
    , _server(nullptr) {
}

APIServer::~APIServer() {
    stop();
}

void APIServer::begin() {
    if (_server) {
        return;
    }
    
    _server = new ESP8266WebServer(_port);
    
    _server->on("/api/device", [this]() { _handleDeviceInfo(); });
    _server->on("/api/data", [this]() { _handleData(); });
    _server->onNotFound([this]() { _handleNotFound(); });
    
    _server->begin();
    Serial.print("API Server started on port ");
    Serial.println(_port);
}

void APIServer::update() {
    if (_server) {
        _server->handleClient();
    }
}

void APIServer::stop() {
    if (_server) {
        _server->stop();
        delete _server;
        _server = nullptr;
    }
}

void APIServer::_handleDeviceInfo() {
    StaticJsonDocument<256> doc;
    
    doc["id"] = _getMACAddress();
    doc["name"] = _device->getName();
    doc["type"] = _device->getTypeString();
    doc["firmware_version"] = _device->getFirmwareVersion();
    
    JsonObject capabilities = doc.createNestedObject("capabilities");
    const DeviceInfo::Capabilities& caps = _device->getCapabilities();
    capabilities["has_presence"] = caps.hasPresence;
    capabilities["has_motion"] = caps.hasMotion;
    capabilities["has_temperature"] = caps.hasTemperature;
    capabilities["has_humidity"] = caps.hasHumidity;
    capabilities["has_sensitivity"] = caps.hasSensitivity;
    capabilities["max_distance"] = caps.maxDistance;
    
    String response;
    serializeJson(doc, response);
    
    _server->send(200, "application/json", response);
}

void APIServer::_handleData() {
    StaticJsonDocument<256> doc;
    
    const SensorData& data = _device->getSensorData();
    doc["presence"] = data.presence;
    doc["motion"] = data.motion;
    doc["distance"] = data.distance;
    doc["sensitivity"] = data.sensitivity;
    doc["temperature"] = data.temperature;
    doc["humidity"] = data.humidity;
    doc["uptime"] = data.uptime;
    
    String response;
    serializeJson(doc, response);
    
    _server->send(200, "application/json", response);
}

void APIServer::_handleNotFound() {
    _server->send(404, "application/json", "{\"error\":\"Not found\"}");
}

String APIServer::_getMACAddress() {
    uint8_t mac[6];
    WiFi.macAddress(mac);
    char buffer[18];
    snprintf(buffer, sizeof(buffer), "%02X%02X%02X%02X%02X%02X",
             mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    return String(buffer);
}

}
