#include "LEDController.h"

namespace lovi {

LEDController::LEDController(uint8_t pin) : _pin(pin), _isOn(false) {
}

void LEDController::begin() {
    pinMode(_pin, OUTPUT);
    off();
}

void LEDController::on() {
    digitalWrite(_pin, LOW);
    _isOn = true;
}

void LEDController::off() {
    digitalWrite(_pin, HIGH);
    _isOn = false;
}

void LEDController::toggle() {
    if (_isOn) {
        off();
    } else {
        on();
    }
}

void LEDController::setBrightness(uint8_t brightness) {
    analogWrite(_pin, brightness);
}

bool LEDController::isOn() const {
    return _isOn;
}

}
