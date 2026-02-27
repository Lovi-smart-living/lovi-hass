#include "MDNSAdvertiser.h"

namespace lovi {

MDNSAdvertiser::MDNSAdvertiser() : _started(false) {
}

void MDNSAdvertiser::begin(const char* deviceName, const char* firmwareVersion, uint16_t port) {
    if (_started) {
        return;
    }

    if (MDNS.begin(deviceName)) {
        Serial.print("mDNS started: ");
        Serial.print(deviceName);
        Serial.println(".local");

        MDNS.addService("lovi", "tcp", port);
        _setDeviceProperties(firmwareVersion);

        Serial.println("mDNS service advertised");
        _started = true;
    } else {
        Serial.println("Failed to start mDNS");
    }
}

void MDNSAdvertiser::update() {
    if (_started) {
        MDNS.update();
    }
}

void MDNSAdvertiser::stop() {
    _started = false;
}

void MDNSAdvertiser::_setDeviceProperties(const char* firmwareVersion) {
    String mac = _getMACAddress();
    String model = "Lovi Device";
    String deviceType = "presence_gen_one";

    MDNS.addServiceTxt("lovi", "tcp", "mac", mac);
    MDNS.addServiceTxt("lovi", "tcp", "model", model);
    MDNS.addServiceTxt("lovi", "tcp", "device_type", deviceType);
    MDNS.addServiceTxt("lovi", "tcp", "firmware_version", firmwareVersion);
}

String MDNSAdvertiser::_getMACAddress() {
    uint8_t mac[6];
    WiFi.macAddress(mac);
    char buffer[18];
    snprintf(buffer, sizeof(buffer), "%02X:%02X:%02X:%02X:%02X:%02X",
             mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    return String(buffer);
}

}
