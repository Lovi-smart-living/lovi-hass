#pragma once

#include <Arduino.h>

namespace lovi {

enum class DeviceType : uint8_t {
    PRESENCE_GEN_ONE = 0,
    TEST_DEVICE = 1,
    UNKNOWN = 255
};

struct DeviceInfo {
    String id;
    String name;
    DeviceType type;
    String firmwareVersion;
    String model;
    
    struct Capabilities {
        bool hasPresence = false;
        bool hasMotion = false;
        bool hasTemperature = false;
        bool hasHumidity = false;
        bool hasSensitivity = false;
        float maxDistance = 0.0f;
    } capabilities;
};

struct SensorData {
    bool presence = false;
    bool motion = false;
    float distance = 0.0f;
    int sensitivity = 50;
    float temperature = 0.0f;
    float humidity = 0.0f;
    uint32_t uptime = 0;
};

}
