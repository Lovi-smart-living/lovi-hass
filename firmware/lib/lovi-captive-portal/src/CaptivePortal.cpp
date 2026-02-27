/**
 * @file CaptivePortal.cpp
 * @brief Captive Portal implementation
 * 
 * All operations are logged to Serial for debugging.
 */

#include "CaptivePortal.h"
#include <ArduinoJson.h>
#include <functional>

namespace lovi {

// =====================================================
// CONSTRUCTOR
// =====================================================

CaptivePortal::CaptivePortal(
    Device* device,
    int ledPin,
    const char* apSSID,
    const char* apPassword,
    int apChannel
) : device(device)
  , ledController(ledPin)
  , webServer(80)
  , configMode(false)
  , deviceInitialized(false)
  , presenceDetected(false)
  , apChannel(apChannel)
  , apIP(192, 168, 4, 1)
{
    // Set AP SSID (use device name if not provided)
    if (apSSID && strlen(apSSID) > 0) {
        strncpy(this->apSSID, apSSID, sizeof(this->apSSID) - 1);
    } else if (device) {
        strncpy(this->apSSID, device->getDeviceName(), sizeof(this->apSSID) - 1);
    } else {
        strncpy(this->apSSID, "Lovi Device", sizeof(this->apSSID) - 1);
    }
    this->apSSID[sizeof(this->apSSID) - 1] = '\0';
    
    // Set AP password
    strncpy(this->apPassword, apPassword, sizeof(this->apPassword) - 1);
    this->apPassword[sizeof(this->apPassword) - 1] = '\0';
    
    Serial.println(F("========================================"));
    Serial.println(F("  Lovi Captive Portal"));
    Serial.println(F("========================================"));
}

// =====================================================
// BEGIN
// =====================================================

void CaptivePortal::begin() {
    // Initialize Serial
    Serial.begin(115200);
    Serial.println();
    Serial.println(F("========================================"));
    if (device) {
        Serial.print(F("  "));
        Serial.println(device->getDeviceName());
    } else {
        Serial.println(F("  Lovi Device"));
    }
    Serial.println(F("========================================"));
    Serial.println(F("[INIT] Starting initialization..."));
    Serial.println();

    // Initialize EEPROM
    Serial.println(F("[INIT] EEPROM: Initializing..."));
    EEPROM.begin(512);

    // Initialize LED
    Serial.println(F("[INIT] LED: Initializing controller..."));
    ledController.begin();
    ledController.setPattern(LEDPattern::BOOT);

    // Initialize config manager
    Serial.println(F("[INIT] Config: Loading from EEPROM..."));
    configManager.begin();
    if (!configManager.loadConfig()) {
        Serial.println(F("[INIT] Config: No saved config found, using defaults"));
    } else {
        Serial.println(F("[INIT] Config: Loaded successfully"));
    }

    // Set device info from config
    if (device) {
        device->setDeviceID(configManager.getDeviceID());
        
        // Set hostname from device name
        String hostname = String(device->getDeviceName());
        hostname.replace(" ", "-");
        hostname.toLowerCase();
        wifiManager.setHostname(hostname.c_str());
        
        Serial.print(F("[INIT] Device ID: "));
        Serial.println(configManager.getDeviceID());
    }

    // Initialize WiFi manager
    Serial.println(F("[INIT] WiFi: Initializing..."));
    wifiManager.begin(&configManager, &ledController);
    
    // Set up callbacks
    wifiManager.onConnected([this]() { this->onWiFiConnected(); });
    wifiManager.onDisconnected([this]() { this->onWiFiDisconnected(); });
    wifiManager.onEnterAPMode([this]() { this->onEnterAPMode(); });
    
    // Try to connect to WiFi (async - callbacks will handle success/failure)
    Serial.println(F("[INIT] WiFi: Attempting connection..."));
    ledController.setPattern(LEDPattern::WIFI_CONNECT);
    bool connectInitiated = wifiManager.connect();
    
    // If no SSID configured, enter AP mode immediately
    if (!connectInitiated) {
        Serial.println(F("[INIT] WiFi: No credentials saved, entering AP mode"));
        enterConfigMode();
    }

    // Setup web server routes
    Serial.println(F("[INIT] HTTP: Setting up web server..."));
    setupWebServerRoutes();
    webServer.begin();
    Serial.println(F("[INIT] HTTP: Server started on port 80"));

    // Initialize device
    if (device && !deviceInitialized) {
        Serial.println(F("[INIT] Device: Initializing..."));
        device->begin(&configManager, &ledController);
        device->registerAPIRoutes(&webServer);
        deviceInitialized = true;
        
        // Device starts in normal mode (not config mode)
        device->onExitConfigMode();
    }

    Serial.println();
    Serial.println(F("[INIT] Initialization complete!"));
    Serial.println(F("========================================"));
}

// =====================================================
// UPDATE
// =====================================================

void CaptivePortal::update() {
    // Update LED with presence state
    ledController.update(presenceDetected);

    // Handle AP mode specific tasks
    if (configMode || (WiFi.getMode() & WIFI_AP)) {
        dnsHandler.processRequests();
    }

    // Handle web server
    webServer.handleClient();

    // Update WiFi manager for async connection handling
    wifiManager.update();

    // Handle device or network updates
    if (configMode) {
        // In config mode, just update web server
    } else {
        // Update device
        if (device) {
            bool presence = false;
            device->update(&presence);
            presenceDetected = presence;
        }

        // Update mDNS if connected
        if (WiFi.status() == WL_CONNECTED) {
            MDNS.update();
        }
    }

    // Feed watchdog
    ESP.wdtFeed();
}

// =====================================================
// WIFI CALLBACKS
// =====================================================

void CaptivePortal::onWiFiConnected() {
    Serial.println();
    Serial.println(F("[WIFI] Connected successfully!"));
    Serial.print(F("[WIFI] SSID: "));
    Serial.println(WiFi.SSID());
    Serial.print(F("[WIFI] IP Address: "));
    Serial.println(WiFi.localIP().toString());
    Serial.print(F("[WIFI] Gateway: "));
    Serial.println(WiFi.gatewayIP().toString());
    Serial.print(F("[WIFI] DNS: "));
    Serial.println(WiFi.dnsIP().toString());
    Serial.print(F("[WIFI] Signal Strength (RSSI): "));
    Serial.print(WiFi.RSSI());
    Serial.println(F(" dBm"));

    // LED feedback
    ledController.setPattern(LEDPattern::CONNECTED);
    delay(500);  // Brief flash to show connection
    
    // Exit config mode if we were in it
    if (configMode) {
        configMode = false;
        
        // Stop DNS server
        Serial.println(F("[DNS] Stopping DNS server"));
        dnsHandler.stop();
        
        // Stop AP mode
        Serial.println(F("[AP] Stopping access point"));
        WiFi.softAPdisconnect(true);
        WiFi.mode(WIFI_STA);
        
        Serial.println(F("[MODE] Switched to STA mode"));
    }
    
    // Start mDNS
    if (device) {
        String hostname = String(device->getDeviceName());
        hostname.replace(" ", "-");
        hostname.toLowerCase();
        
        // Get MAC address for TXT record
        String mac = WiFi.macAddress();
        
        if (MDNS.begin(hostname.c_str())) {
            // Add _lovi._tcp service for Home Assistant
            MDNS.addService("lovi", "tcp", 80);
            
            // Add TXT records for HA discovery
            MDNS.addServiceTxt("lovi", "tcp", "mac", mac.c_str());
            MDNS.addServiceTxt("lovi", "tcp", "device_type", device->getDeviceType());
            MDNS.addServiceTxt("lovi", "tcp", "model", device->getModelName());
            MDNS.addServiceTxt("lovi", "tcp", "firmware_version", "1.0.0");
            MDNS.addServiceTxt("lovi", "tcp", "capabilities", "presence,motion");
            
            Serial.print(F("[mDNS] Started: http://"));
            Serial.print(hostname.c_str());
            Serial.println(F(".local"));
            Serial.print(F("[mDNS] MAC: "));
            Serial.println(mac);
        }
        
        device->onWiFiConnected();
        device->onExitConfigMode();
    }
}

void CaptivePortal::onWiFiDisconnected() {
    Serial.println();
    Serial.println(F("[WIFI] Disconnected!"));
    
    if (device) {
        device->onWiFiDisconnected();
    }
}

void CaptivePortal::onEnterAPMode() {
    Serial.println();
    Serial.println(F("[AP] Entering configuration mode"));
    ledController.setPattern(LEDPattern::AP_MODE);
    configMode = true;
    startAccessPoint();
    
    if (device) {
        device->onEnterConfigMode();
    }
}

// =====================================================
// CONFIG MODE
// =====================================================

void CaptivePortal::enterConfigMode() {
    configMode = true;
    startAccessPoint();
    
    if (device) {
        device->onEnterConfigMode();
    }
}

void CaptivePortal::startAccessPoint() {
    Serial.println();
    Serial.println(F("========================================"));
    Serial.println(F("  ACCESS POINT MODE"));
    Serial.println(F("========================================"));
    
    // WIFI_AP_STA allows both AP mode AND station mode
    WiFi.mode(WIFI_AP_STA);
    
    Serial.print(F("[AP] Starting softAP with SSID: "));
    Serial.println(apSSID);
    
    // Use WPA2 with password
    WiFi.softAP(apSSID, apPassword, apChannel);
    WiFi.softAPConfig(apIP, apIP, IPAddress(255, 255, 255, 0));
    
    // Start DNS for captive portal
    Serial.print(F("[DNS] Starting DNS server on "));
    Serial.print(apIP);
    Serial.println(F(":53"));
    dnsHandler.begin(apIP, 53);
    
    Serial.println();
    Serial.println(F("[AP] Access point active!"));
    Serial.print(F("[AP] SSID: "));
    Serial.println(apSSID);
    Serial.print(F("[AP] Password: "));
    Serial.println(apPassword);
    Serial.print(F("[AP] IP Address: http://"));
    Serial.println(apIP.toString());
    Serial.println(F("========================================"));
}

// =====================================================
// WEB SERVER ROUTES
// =====================================================

void CaptivePortal::setupWebServerRoutes() {
    using namespace std::placeholders;
    
    Serial.println(F("[HTTP] Setting up API routes..."));
    
    // ========== CAPTIVE PORTAL DETECTION ROUTES ==========
    webServer.on("/generate_204", HTTP_GET, std::bind(&CaptivePortal::handleGenerate204, this));
    webServer.on("/generate204", HTTP_GET, std::bind(&CaptivePortal::handleGenerate204, this));
    webServer.on("/hotspot-detect.html", HTTP_GET, std::bind(&CaptivePortal::handleHotspotDetect, this));
    webServer.on("/ncsi.txt", HTTP_GET, std::bind(&CaptivePortal::handleNCSI, this));
    webServer.on("/connecttest.txt", HTTP_GET, std::bind(&CaptivePortal::handleConnectTest, this));
    webServer.on("/redirect", HTTP_GET, std::bind(&CaptivePortal::handleRedirect, this));
    webServer.on("/favicon.ico", HTTP_GET, std::bind(&CaptivePortal::handleFavicon, this));
    
    // ========== MAIN ROUTES ==========
    webServer.on("/", HTTP_GET, std::bind(&CaptivePortal::handleRoot, this));
    
    // ========== API ROUTES (clean paths) ==========
    webServer.on("/connected", HTTP_GET, std::bind(&CaptivePortal::handleConnected, this));
    webServer.on("/presence", HTTP_GET, std::bind(&CaptivePortal::handlePresence, this));
    webServer.on("/status", HTTP_GET, std::bind(&CaptivePortal::handleStatus, this));
    webServer.on("/data", HTTP_GET, std::bind(&CaptivePortal::handleData, this));
    webServer.on("/device", HTTP_GET, std::bind(&CaptivePortal::handleDevice, this));
    webServer.on("/scan", HTTP_GET, std::bind(&CaptivePortal::handleScan, this));
    webServer.on("/network", HTTP_GET, std::bind(&CaptivePortal::handleNetwork, this));
    webServer.on("/settings", HTTP_GET, std::bind(&CaptivePortal::handleSettings, this));
    webServer.on("/settings", HTTP_POST, std::bind(&CaptivePortal::handleSettings, this));
    webServer.on("/restart", HTTP_POST, std::bind(&CaptivePortal::handleRestart, this));
    webServer.on("/reset", HTTP_POST, std::bind(&CaptivePortal::handleReset, this));
    webServer.on("/led", HTTP_POST, std::bind(&CaptivePortal::handleLED, this));
    
    // ========== API ROUTES (with /api/ prefix for compatibility) ==========
    webServer.on("/api/connected", HTTP_GET, std::bind(&CaptivePortal::handleConnected, this));
    webServer.on("/api/presence", HTTP_GET, std::bind(&CaptivePortal::handlePresence, this));
    webServer.on("/api/status", HTTP_GET, std::bind(&CaptivePortal::handleStatus, this));
    webServer.on("/api/data", HTTP_GET, std::bind(&CaptivePortal::handleData, this));
    webServer.on("/api/device", HTTP_GET, std::bind(&CaptivePortal::handleDevice, this));
    webServer.on("/api/scan", HTTP_GET, std::bind(&CaptivePortal::handleScan, this));
    webServer.on("/api/network", HTTP_GET, std::bind(&CaptivePortal::handleNetwork, this));
    webServer.on("/api/settings", HTTP_GET, std::bind(&CaptivePortal::handleSettings, this));
    webServer.on("/api/settings", HTTP_POST, std::bind(&CaptivePortal::handleSettings, this));
    webServer.on("/api/restart", HTTP_POST, std::bind(&CaptivePortal::handleRestart, this));
    webServer.on("/api/reset", HTTP_POST, std::bind(&CaptivePortal::handleReset, this));
    webServer.on("/api/led", HTTP_POST, std::bind(&CaptivePortal::handleLED, this));
    
    // ========== CATCH-ALL ==========
    webServer.onNotFound(std::bind(&CaptivePortal::handleNotFound, this));
    
    Serial.println(F("[HTTP] API routes configured"));
    Serial.println(F("[HTTP]   GET  /connected  - WiFi status"));
    Serial.println(F("[HTTP]   GET  /presence   - Presence data"));
    Serial.println(F("[HTTP]   GET  /status     - Device health"));
    Serial.println(F("[HTTP]   GET  /data       - Raw sensor data"));
    Serial.println(F("[HTTP]   GET/POST /settings - Configuration"));
    Serial.println(F("[HTTP]   POST /restart    - Restart device"));
    Serial.println(F("[HTTP]   POST /reset      - Factory reset"));
    Serial.println(F("[HTTP] Also supports /api/ prefix for compatibility"));
}

// =====================================================
// API HANDLERS
// =====================================================

void CaptivePortal::handleConnected() {
    Serial.println(F("[API] /connected request"));
    
    bool connected = (WiFi.status() == WL_CONNECTED);
    
    JsonDocument doc;
    doc["connected"] = connected;
    doc["ip"] = connected ? WiFi.localIP().toString() : "0.0.0.0";
    doc["ssid"] = connected ? WiFi.SSID() : "";
    doc["rssi"] = connected ? WiFi.RSSI() : 0;
    
    String output;
    serializeJson(doc, output);
    webServer.send(200, "application/json", output);
    
    Serial.print(F("[API] Response: connected="));
    Serial.print(connected ? "true" : "false");
    if (connected) {
        Serial.print(F(", ip="));
        Serial.print(WiFi.localIP().toString());
    }
    Serial.println();
}

void CaptivePortal::handlePresence() {
    Serial.println(F("[API] /presence request"));
    
    JsonDocument doc;
    
    if (device) {
        device->getPresence(doc);
    } else {
        doc["presence"] = false;
        doc["motion"] = false;
        doc["distance"] = 0.0f;
    }
    
    String output;
    serializeJson(doc, output);
    webServer.send(200, "application/json", output);
    
    Serial.print(F("[API] Response: presence="));
    Serial.print(doc["presence"].as<bool>() ? "true" : "false");
    Serial.print(F(", motion="));
    Serial.print(doc["motion"].as<bool>() ? "true" : "false");
    Serial.print(F(", distance="));
    Serial.print(doc["distance"].as<float>());
    Serial.println(F("m"));
}

void CaptivePortal::handleStatus() {
    Serial.println(F("[API] /status request"));
    
    // Check for health parameter
    bool healthCheck = webServer.hasArg("health");
    
    JsonDocument doc;
    
    if (device) {
        device->getStatus(doc, healthCheck);
    } else {
        doc["uptime"] = millis() / 1000;
        doc["heap"] = ESP.getFreeHeap();
        doc["status"] = "healthy";
    }
    
    String output;
    serializeJson(doc, output);
    webServer.send(200, "application/json", output);
    
    Serial.print(F("[API] Response: uptime="));
    Serial.print(doc["uptime"].as<long>());
    Serial.print(F("s, heap="));
    Serial.print(doc["heap"].as<int>());
    Serial.println(F(" bytes"));
}

void CaptivePortal::handleData() {
    Serial.println(F("[API] /data request"));
    
    JsonDocument doc;
    
    if (device) {
        device->getSensorData(doc);
    } else {
        doc["raw"] = "No device";
    }
    
    String output;
    serializeJson(doc, output);
    webServer.send(200, "application/json", output);
    Serial.println(F("[API] Response sent"));
}

void CaptivePortal::handleDevice() {
    Serial.println(F("[API] /device request"));
    
    JsonDocument doc;
    doc["name"] = device ? device->getDeviceName() : "Unknown";
    doc["version"] = device ? device->getFirmwareVersion() : "1.0.0";
    doc["id"] = device ? device->getDeviceID() : "unknown";
    doc["model"] = device ? device->getModelName() : "Unknown";
    doc["device_type"] = device ? device->getDeviceType() : "unknown";
    doc["manufacturer"] = "Lovi";
    doc["mac_address"] = WiFi.macAddress();
    
    String output;
    serializeJson(doc, output);
    webServer.send(200, "application/json", output);
    
    Serial.print(F("[API] Device: "));
    Serial.print(device ? device->getDeviceName() : "Unknown");
    Serial.print(F(", ID: "));
    Serial.println(device ? device->getDeviceID() : "unknown");
}

void CaptivePortal::handleScan() {
    Serial.println(F("[API] /scan request"));
    Serial.println(F("[WiFi] Scanning for networks..."));

    int n = WiFi.scanNetworks();

    JsonDocument doc;
    JsonArray networks = doc["networks"].to<JsonArray>();

    if (n > 0) {
        for (int i = 0; i < n; i++) {
            JsonObject network = networks.add<JsonObject>();
            network["ssid"] = WiFi.SSID(i);
            network["rssi"] = WiFi.RSSI(i);
            network["encryption"] = WiFi.encryptionType(i);
        }
        Serial.print(F("[WiFi] Found "));
        Serial.print(n);
        Serial.println(F(" networks"));
    } else {
        Serial.println(F("[WiFi] No networks found"));
    }

    String output;
    serializeJson(doc, output);
    webServer.send(200, "application/json", output);

    WiFi.scanDelete();
}

void CaptivePortal::handleNetwork() {
    Serial.println(F("[API] /network request"));
    
    JsonDocument doc;
    doc["ap_ip"] = WiFi.softAPIP().toString();
    doc["sta_ip"] = WiFi.localIP().toString();
    
    uint8_t mode = WiFi.getMode();
    const char* modeStr;
    if (mode == WIFI_AP_STA) modeStr = "AP_STA";
    else if (mode == WIFI_STA) modeStr = "STA";
    else if (mode == WIFI_AP) modeStr = "AP";
    else modeStr = "OFF";
    doc["mode"] = modeStr;
    doc["ap_ssid"] = apSSID;
    doc["connected"] = (WiFi.status() == WL_CONNECTED);
    doc["ssid"] = WiFi.SSID();
    doc["rssi"] = WiFi.RSSI();
    doc["channel"] = WiFi.channel();
    
    String output;
    serializeJson(doc, output);
    webServer.send(200, "application/json", output);
    
    Serial.print(F("[API] Network: "));
    Serial.print(modeStr);
    Serial.print(F(", AP IP: "));
    Serial.print(WiFi.softAPIP().toString());
    Serial.print(F(", STA IP: "));
    Serial.println(WiFi.localIP().toString());
}

void CaptivePortal::handleSettings() {
    JsonDocument doc;
    
    if (webServer.method() == HTTP_GET) {
        Serial.println(F("[API] /settings GET request"));
        
        if (device) {
            device->getSettings(doc);
        } else {
            doc["error"] = "No device";
        }
    } else {
        // POST - Update settings
        Serial.println(F("[API] /settings POST request"));
        
        String body = webServer.arg("plain");
        
        DeserializationError error = deserializeJson(doc, body);
        
        if (error) {
            Serial.print(F("[API] JSON parse error: "));
            Serial.println(error.c_str());
            JsonDocument errDoc;
            errDoc["error"] = "Invalid JSON";
            errDoc["message"] = error.c_str();
            String errOutput;
            serializeJson(errDoc, errOutput);
            webServer.send(400, "application/json", errOutput);
            return;
        }
        
        if (device && device->updateSettings(doc)) {
            Serial.println(F("[API] Settings updated successfully"));
            doc["success"] = true;
            doc["message"] = "Settings updated";
        } else {
            doc["success"] = false;
            doc["message"] = "No settings updated";
        }
    }
    
    String output;
    serializeJson(doc, output);
    webServer.send(200, "application/json", output);
}

void CaptivePortal::handleLED() {
    Serial.println(F("[API] /led request"));
    
    JsonDocument doc;
    
    // Only handle POST requests
    if (webServer.method() != HTTP_POST) {
        doc["error"] = "Use POST method";
        doc["message"] = "Send JSON with 'state': true/false";
        String output;
        serializeJson(doc, output);
        webServer.send(405, "application/json", output);
        return;
    }
    
    String body = webServer.arg("plain");
    DeserializationError error = deserializeJson(doc, body);
    
    if (error) {
        Serial.print(F("[API] JSON parse error: "));
        Serial.println(error.c_str());
        JsonDocument errDoc;
        errDoc["error"] = "Invalid JSON";
        errDoc["message"] = error.c_str();
        String errOutput;
        serializeJson(errDoc, errOutput);
        webServer.send(400, "application/json", errOutput);
        return;
    }
    
    // Handle LED control
    if (doc.containsKey("state")) {
        bool ledState = doc["state"].as<bool>();
        
        LEDController* ledCtrl = getLEDController();
        if (ledCtrl) {
            ledCtrl->setState(ledState);
            // Also set the pattern
            if (ledState) {
                ledCtrl->setPattern(lovi::LEDPattern::ON);
            } else {
                ledCtrl->setPattern(lovi::LEDPattern::OFF);
            }
            
            JsonDocument response;
            response["success"] = true;
            response["led"] = ledState;
            response["message"] = ledState ? "LED turned on" : "LED turned off";
            
            String output;
            serializeJson(response, output);
            webServer.send(200, "application/json", output);
            
            Serial.print(F("[API] LED set to: "));
            Serial.println(ledState ? "ON" : "OFF");
        } else {
            doc["error"] = "No LED controller";
            String output;
            serializeJson(doc, output);
            webServer.send(500, "application/json", output);
        }
    } else {
        doc["error"] = "Missing 'state' parameter";
        doc["message"] = "Send JSON with 'state': true/false";
        String output;
        serializeJson(doc, output);
        webServer.send(400, "application/json", output);
    }
}

void CaptivePortal::handleRestart() {
    Serial.println(F("[API] /restart request"));
    
    JsonDocument doc;
    doc["message"] = "Restarting device...";
    doc["success"] = true;
    
    String output;
    serializeJson(doc, output);
    webServer.send(200, "application/json", output);
    
    Serial.println(F("[API] Restarting device in 1 second..."));
    delay(1000);
    ESP.restart();
}

void CaptivePortal::handleReset() {
    Serial.println(F("[API] /reset request"));
    
    JsonDocument doc;
    doc["message"] = "Resetting to factory defaults...";
    doc["success"] = true;
    
    String output;
    serializeJson(doc, output);
    webServer.send(200, "application/json", output);
    
    Serial.println(F("[API] Factory reset in 1 second..."));
    delay(1000);
    
    // Reset config
    configManager.resetConfig();
    
    // Restart
    ESP.restart();
}

// =====================================================
// CAPTIVE PORTAL DETECTION HANDLERS
// =====================================================

String CaptivePortal::getCaptivePortalUrl() {
    IPAddress ip = (WiFi.getMode() & WIFI_AP) ? WiFi.softAPIP() : WiFi.localIP();
    String url = "http://";
    url += ip.toString();
    url += "/";
    return url;
}

void CaptivePortal::handleGenerate204() {
    Serial.println(F("[API] /generate_204 (Android captive portal)"));
    String redirectUrl = getCaptivePortalUrl();
    webServer.sendHeader("Location", redirectUrl, true);
    webServer.send(302, "text/plain", "");
}

void CaptivePortal::handleHotspotDetect() {
    Serial.println(F("[API] /hotspot-detect.html (iOS captive portal)"));
    String redirectUrl = getCaptivePortalUrl();
    webServer.sendHeader("Location", redirectUrl, true);
    webServer.send(302, "text/plain", "");
}

void CaptivePortal::handleNCSI() {
    Serial.println(F("[API] /ncsi.txt (Windows captive portal)"));
    String redirectUrl = getCaptivePortalUrl();
    webServer.sendHeader("Location", redirectUrl, true);
    webServer.send(302, "text/plain", "");
}

void CaptivePortal::handleConnectTest() {
    Serial.println(F("[API] /connecttest.txt (Windows alt)"));
    String redirectUrl = getCaptivePortalUrl();
    webServer.sendHeader("Location", redirectUrl, true);
    webServer.send(302, "text/plain", "");
}

void CaptivePortal::handleRedirect() {
    Serial.println(F("[API] /redirect (Microsoft)"));
    String redirectUrl = getCaptivePortalUrl();
    webServer.sendHeader("Location", redirectUrl, true);
    webServer.send(302, "text/plain", "");
}

void CaptivePortal::handleFavicon() {
    Serial.println(F("[API] /favicon.ico"));
    webServer.send(204, "image/x-icon", "");
}

void CaptivePortal::handleRoot() {
    Serial.println(F("[API] / request - serving captive portal"));
    String html = FPSTR(WEB_UI_HTML);
    webServer.send(200, "text/html", html);
}

void CaptivePortal::handleNotFound() {
    String uri = webServer.uri();
    Serial.print(F("[API] 404: "));
    Serial.println(uri);
    
    // API routes return 404
    if (uri.startsWith("/api/") || uri.startsWith("/connected") ||
        uri.startsWith("/presence") || uri.startsWith("/status") ||
        uri.startsWith("/data") || uri.startsWith("/settings") ||
        uri.startsWith("/restart") || uri.startsWith("/reset")) {
        webServer.send(404, "application/json", "{\"error\":\"Not found\"}");
        return;
    }
    
    // Otherwise serve the captive portal page
    Serial.println(F("[API] Serving captive portal page"));
    String html = FPSTR(WEB_UI_HTML);
    webServer.send(200, "text/html", html);
}

// =====================================================
// UTILITY METHODS
// =====================================================

bool CaptivePortal::isConnected() const {
    return wifiManager.isConnected();
}

String CaptivePortal::getLocalIP() const {
    return wifiManager.getLocalIP();
}

String CaptivePortal::getAPIP() const {
    return apIP.toString();
}

} // namespace lovi
