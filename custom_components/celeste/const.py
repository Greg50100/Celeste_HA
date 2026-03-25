"""Constantes pour l'intégration Céleste."""

DOMAIN = "celeste"
PLATFORMS = ["binary_sensor", "sensor"]

# URL de l'API IMCCE Miriade
MIRIADE_API_URL = "https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php"

# ─── Paramètres de configuration ─────────────────────────────────────────────
CONF_OBJECT_NAME = "object_name"
CONF_OBJECT_TYPE = "object_type"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_ALTITUDE = "altitude"

# ─── Valeurs par défaut ──────────────────────────────────────────────────────
DEFAULT_ALTITUDE = 0
DEFAULT_STEP = "1d"
DEFAULT_NB_STEPS = 1

# ─── Types d'objets célestes supportés par Miriade ───────────────────────────
OBJECT_TYPES = {
    "planet": "Planète",
    "asteroid": "Astéroïde",
    "comet": "Comète",
    "satellite": "Satellite naturel",
}

# ─── Planètes prédéfinies (noms IMCCE) ──────────────────────────────────────
PREDEFINED_PLANETS = [
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Moon",
    "Sun",
]

# ─── Intervalle de mise à jour (secondes) ────────────────────────────────────
UPDATE_INTERVAL = 3600  # 1 heure

# ─── Seuil de visibilité ─────────────────────────────────────────────────────
# Un astre est considéré "potentiellement visible" quand son élongation solaire
# dépasse ce seuil. En-dessous, il est noyé dans la lumière crépusculaire.
ELONGATION_VISIBILITY_THRESHOLD = 15.0  # degrés

# ─── Seuil de magnitude (optionnel) ─────────────────────────────────────────
# Si configuré, l'astre doit avoir une magnitude < seuil pour être visible.
# En astronomie, plus la magnitude est petite (ou négative), plus l'astre est brillant.
# Exemple : limite à l'œil nu ~6.5, jumelles ~10, télescope amateur ~14.
CONF_MAGNITUDE_THRESHOLD = "magnitude_threshold"
DEFAULT_MAGNITUDE_THRESHOLD = None  # Aucun filtrage par magnitude par défaut

# ─── Configuration des sensors numériques ────────────────────────────────────
CONF_ENABLE_SENSORS = "enable_sensors"  # Activer les sensors numériques
DEFAULT_ENABLE_SENSORS = True  # Activés par défaut

# Sensors disponibles et leurs configurations
SENSORS_AVAILABLE = {
    "magnitude": {
        "name": "Magnitude",
        "description": "Magnitude apparente",
        "unit": "mag",
        "icon": "mdi:brightness-7",
        "device_class": None,
        "state_class": "measurement",
    },
    "elongation": {
        "name": "Élongation",
        "description": "Élongation solaire",
        "unit": "°",
        "icon": "mdi:angle-acute",
        "device_class": None,
        "state_class": "measurement",
    },
    "distance": {
        "name": "Distance",
        "description": "Distance géocentrique",
        "unit": "ua",
        "icon": "mdi:ruler",
        "device_class": None,
        "state_class": "measurement",
    },
    "phase": {
        "name": "Phase",
        "description": "Angle de phase",
        "unit": "°",
        "icon": "mdi:circle-half-full",
        "device_class": None,
        "state_class": "measurement",
    },
    "radial_velocity": {
        "name": "Vitesse radiale",
        "description": "Vitesse radiale géocentrique",
        "unit": "km/s",
        "icon": "mdi:speedometer",
        "device_class": None,
        "state_class": "measurement",
    },
}
