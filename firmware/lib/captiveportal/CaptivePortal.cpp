#include "CaptivePortal.h"

namespace lovi {

const char* AP_SSID = "Lovi-Config";
const char* HTML_FORM = R"(
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Lovi Device Configuration</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        input { margin: 10px 0; padding: 10px; width: 100%%; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; }
    </style>
</head>
<body>
    <h1>Lovi Device Setup</h1>
    <form method="POST" action="/save">
        <label>WiFi SSID:</label>
        <input type="text" name="ssid" required>
        <label>WiFi Password:</label>
        <input type="password" name="password" required>
        <button type="submit">Save & Connect</button>
    </form>
</body>
</html>
)";

CaptivePortal::CaptivePortal(uint8_t ledPin)
    : _configManager(nullptr)
    , _ledController(nullptr)
    , _ledPin(ledPin)
    , _configMode(false)
    , _started(false)
    , _dnsServer(nullptr)
    , _webServer(nullptr) {
}

CaptivePortal::~CaptivePortal() {
    if (_dnsServer) delete _dnsServer;
    if (_webServer) delete _webServer;
    if (_configManager) delete _configManager;
    if (_ledController) delete _ledController;
}

void CaptivePortal::begin() {
    if (_started) return;
    
    _configManager = new ConfigManager();
    _configManager->begin();
    _configManager->loadConfig();
    
    _ledController = new LEDController(_ledPin);
    _ledController->begin();
    
    _setupWebServer();
    _started = true;
}

void CaptivePortal::enterConfigMode() {
    if (_configMode) return;
    
    _configMode = true;
    _configManager = new ConfigManager();
    _ledController = new LEDController(_ledPin);
    _ledController->begin();
    
    _setupAP();
    _setupWebServer();
    
    _dnsServer = new DNSServer();
    _dnsServer->start(53, "*", WiFi.softAPIP());
}

void CaptivePortal::update() {
    if (_configMode && _dnsServer) {
        _dnsServer->processNextRequest();
    }
    if (_webServer) {
        _webServer->handleClient();
    }
}

bool CaptivePortal::isInConfigMode() const {
    return _configMode;
}

void CaptivePortal::_setupAP() {
    WiFi.mode(WIFI_AP);
    WiFi.softAP(AP_SSID);
    Serial.print("Access Point IP: ");
    Serial.println(WiFi.softAPIP());
}

void CaptivePortal::_setupWebServer() {
    _webServer = new ESP8266WebServer(80);
    
    _webServer->on("/", [this]() { _handleRoot(); });
    _webServer->on("/save", [this]() { _handleSave(); });
    _webServer->onNotFound([this]() { _handleNotFound(); });
    
    _webServer->begin();
}

void CaptivePortal::_handleRoot() {
    _webServer->send(200, "text/html", HTML_FORM);
}

void CaptivePortal::_handleSave() {
    if (_webServer->hasArg("ssid") && _webServer->hasArg("password")) {
        String ssid = _webServer->arg("ssid");
        String password = _webServer->arg("password");
        
        _configManager->setSSID(ssid.c_str());
        _configManager->setPassword(password.c_str());
        _configManager->saveConfig();
        
        _webServer->send(200, "text/html", "<h1>Settings Saved!</h1><p>Device will restart.</p>");
        delay(1000);
        ESP.restart();
    } else {
        _webServer->send(400, "text/html", "<h1>Invalid Request</h1>");
    }
}

void CaptivePortal::_handleNotFound() {
    _webServer->sendHeader("Location", "/");
    _webServer->send(302);
}

}
