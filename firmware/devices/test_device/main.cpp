#include <Arduino.h>
#include <EEPROM.h>
#include <CaptivePortal.h>
#include <Device.h>
#include <ConfigManager.h>
#include <LEDController.h>

using namespace lovi;

#define DEVICE_NAME "Lovi-Test"
#define FIRMWARE_VERSION "1.0.0"
#define LED_PIN 16

class TestDevice : public Device {
public:
    TestDevice() : Device(DEVICE_NAME, FIRMWARE_VERSION) {}

    void begin(ConfigManager* configManager, LEDController* ledController) override {
        Serial.println("Test Device: Initialized");
    }

    void update() override {
        delay(1);
    }
};

TestDevice device;
CaptivePortal portal(&device, LED_PIN);

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("Starting...");

    EEPROM.begin(512);
    
    ConfigManager configManager;
    configManager.begin();
    configManager.loadConfig();
    
    const char* ssid = configManager.getSSID();
    
    if (strlen(ssid) == 0) {
        Serial.println("No WiFi credentials found - starting captive portal");
        portal.enterConfigMode();
    } else {
        Serial.println("WiFi credentials found - connecting and exposing LED API");
        portal.begin();
    }
}

void loop() {
    portal.update();
}
