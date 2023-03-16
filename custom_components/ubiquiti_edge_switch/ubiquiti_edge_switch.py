import requests
import json
import logging

import voluptuous as vol

from homeassistant.const import (
    CONF_USERNAME, CONF_PASSWORD, CONF_HOST, CONF_PORT,
)
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEFAULT_PORT = 443
DEFAULT_TIMEOUT = 10
DEFAULT_VERIFY_SSL = True

DOMAIN = 'ubiquiti_edge_switch'
CONF_INTERFACE = 'interface'
CONF_INTERFACES = 'interfaces'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional('timeout', default=DEFAULT_TIMEOUT): cv.positive_int,
        vol.Optional('verify_ssl', default=DEFAULT_VERIFY_SSL): cv.boolean,
        vol.Required(CONF_INTERFACES, default=[]): vol.All(
            cv.ensure_list, [cv.string]
        )
    })
}, extra=vol.ALLOW_EXTRA)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Ubiquiti Edge switch platform."""
    conf = config[DOMAIN]
    username = conf[CONF_USERNAME]
    password = conf[CONF_PASSWORD]
    host = conf[CONF_HOST]
    port = conf[CONF_PORT]
    timeout = conf['timeout']
    verify_ssl = conf['verify_ssl']
    interfaces = conf[CONF_INTERFACES]
    url = f"https://{host}:{port}/api/edge/"

    # Create a Ubiquiti Edge switch device
    device = UbiquitiEdgeSwitchDevice(url, username, password, timeout, verify_ssl)

    # Add a switch entity representing the Ubiquiti Edge switch
    add_entities([device])

    # Add a switch port entity for each port on the Ubiquiti Edge switch
    for interface in interfaces:
        add_entities([UbiquitiEdgeSwitchPort(device, interface)])

class UbiquitiEdgeSwitchDevice(Entity):
    """A class representing the Ubiquiti Edge switch."""

    def __init__(self, url, username, password, timeout, verify_ssl):
        """Initialize the device."""
        self._url = url
        self._username = username
        self._password = password
        self._timeout = timeout
        self._verify_ssl = verify_ssl
        self._state = None
        self._name = 'Ubiquiti Edge Switch'

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def should_poll(self):
        """Poll the switch periodically."""
        return True

    @property
    def state(self):
        """Return the state of the switch."""
        return self._state

    def update(self):
        """Update the state of the switch."""
        try:
            response = requests.get(
                f"{self._url}switch/get",
                auth=(self._username, self._password),
                timeout=self._timeout,
                verify=self._verify_ssl
            )

            if response.status_code == 200:
                self._state = 'on'
            else:
                self._state = 'off'
        except:
            _LOGGER.error("Unable to connect to the Ubiquiti Edge switch.")


class UbiquitiEdgeSwitchPort(Entity):
    """A class representing a port on the Ubiquiti Edge switch."""

    def __init__(self, device, interface):
        """Initialize the port."""
        self._device = device
        self._interface = interface
        self._name = f"{self._device.name} {self._interface}"
        self._state = None

    @property
    def name(self):
        """Return the name of the port."""
        return self._name

    @property
    def should_poll(self):
        """Poll the port periodically."""
        return True

    @property
    def state(self):
        """Return the state of the port."""
        return self._state

    def update(self):
        """Update the state of the port."""
        try:
            response = requests.get(
                f"{self._device._url}port/{self._interface}/get",
                auth=(self._device._username, self._device._password),
                timeout=self._device._timeout,
                verify=self._device._verify_ssl
            )

            if response.status_code == 200:
                data = json.loads(response.content)
                self._state = data['state']
            else:
                _LOGGER.error(f"Unable to get state of {self._interface} on the Ubiquiti Edge switch.")
        except:
            _LOGGER.error("Unable to connect to the Ubiquiti Edge switch.")
