import requests
import math
import logging
from datetime import timedelta
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Fires PT"
CONF_RADIUS = "radius"
DEFAULT_RADIUS = 100

SCAN_INTERVAL = timedelta(minutes=10)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_LATITUDE): cv.latitude,
        vol.Optional(CONF_LONGITUDE): cv.longitude,
        vol.Optional(CONF_RADIUS, default=DEFAULT_RADIUS): cv.positive_int,
    }
)

def haversine(coord1, coord2):
    R = 6371  # Earth radius in km
    lat1, lon1 = map(math.radians, coord1)
    lat2, lon2 = map(math.radians, coord2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def setup_platform(hass, config, add_entities, discovery_info=None):
    name = config.get(CONF_NAME)
    lat = config.get(CONF_LATITUDE, hass.config.latitude)
    lng = config.get(CONF_LONGITUDE, hass.config.longitude)
    radius = config.get(CONF_RADIUS)

    add_entities([FiresSensor(name, (lat, lng), radius)], True)

class FiresSensor(Entity):
    def __init__(self, name, coordinate, radius):
        self._name = name
        self._coordinate = coordinate
        self._radius = radius
        self._state = "off"
        self._fires = []

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return {"fires": self._fires}

    def update(self):
        url = "https://api.fogos.pt/new/fires"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            fires = []
            for fire in data.get("data", []):
                if not (fire.get("lat") and fire.get("lng") and fire.get("statusCode") == 5):
                    continue
                fire_coordinate = (float(fire["lat"]), float(fire["lng"]))
                distance = haversine(self._coordinate, fire_coordinate)
                if distance <= self._radius:
                    fires.append(
                        {
                            "location": fire.get("location"),
                            "distance_km": round(distance, 2),
                            "lat": fire.get("lat"),
                            "lng": fire.get("lng"),
                        }
                    )

            self._fires = fires
            self._state = "on" if fires else "off"

        except Exception as e:
            _LOGGER.error("Error fetching fire data: %s", e)
            self._state = "off"
            self._fires = []