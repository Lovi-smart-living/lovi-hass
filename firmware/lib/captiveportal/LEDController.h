#pragma once

#include <Arduino.h>

namespace lovi {

class LEDController {
public:
    LEDController(uint8_t pin);
    void begin();
    void on();
    void off();
    void toggle();
    void setBrightness(uint8_t brightness);
    bool isOn() const;

private:
    uint8_t _pin;
    bool _isOn;
};

}
