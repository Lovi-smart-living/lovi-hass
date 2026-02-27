#include <Arduino.h>
#include <EEPROM.h>
#include <ESP8266WiFi.h>
#include <CaptivePortal.h>
#include <Device.h>

using namespace lovi;

#define FIRMWARE_VERSION "1.0.0"
#define LED_PIN 16
#define WIFI_TIMEOUT 30

class PresenceGenOneDevice : public Device {
public:
    PresenceGenOneDevice() 
        : Device("Lovi-Presence", DeviceType::PRESENCE_GEN_ONE, FIRMWARE_VERSION) {
        
        DeviceInfo::Capabilities caps;
        caps.hasPresence = true;
        caps.hasMotion = true;
        caps.hasTemperature = true;
        caps.hasHumidity = true;
        caps.hasSensitivity = true;
        caps.maxDistance = 5.0f;
        _setCapabilities(caps);
    }

    void begin() override {
        Device::begin();
    }

    void update() override {
        Device::update();
        
        SensorData data;
        data.presence = false;
        data.motion = false;
        data.distance = 0.0f;
        data.sensitivity = 50;
        data.temperature = 22.5f;
        data.humidity = 45.0f;
        data.uptime = millis() / 1000;
        _setSensorData(data);
    }
};

PresenceGenOneDevice device;
CaptivePortal portal(LED_PIN);

void connectToWiFi(const char* ssid, const char* password) {
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    
    Serial.print("Connecting to WiFi");
    int timeout = 0;
    while (WiFi.status() != WL_CONNECTED && timeout < WIFI_TIMEOUT) {
        delay(1000);
        Serial.print(".");
        timeout++;
    }
    Serial.println();
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.print("Connected! IP: ");
        Serial.println(WiFi.localIP());
        
        device.begin();
        device.startMDNS(80);
        device.startAPIServer(80);
    } else {
        Serial.println("WiFi connection failed!");
    }
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("Starting Presence Gen One...");

    EEPROM.begin(512);
    
    ConfigManager* configManager = portal.getConfigManager();
    configManager->loadConfig();
    
    const char* ssid = configManager->getSSID();
    
    if (strlen(ssid) == 0) {
        Serial.println("No WiFi credentials found - starting captive portal");
        portal.enterConfigMode();
    } else {
        Serial.println("WiFi credentials found - connecting...");
        portal.begin();
        connectToWiFi(ssid, configManager->getPassword());
    }
}

void loop() {
    portal.update();
    device.update();
}
