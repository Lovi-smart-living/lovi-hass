"""Constants for Lovi integration."""
from homeassistant.const import Platform

DOMAIN = "lovi"

# Platforms
PLATFORMS = [Platform.SENSOR]

# Configuration
CONF_HOST = "host"
CONF_PORT = "port"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

# API Constants
DEFAULT_PORT = 80
DEFAULT_TIMEOUT = 10

# Device info
MANUFACTURER = "Lovi"

# Presence sensor specific
PRESENCE_GEN_ONE = "presence_gen_one"

# Device types
DEVICE_TYPE_PRESENCE_SENSOR = "presence_sensor"

