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
UPDATE_INTERVAL = 3600  # 1 heure (service IMCCE)
UPDATE_INTERVAL_LOCAL = 60  # 1 minute (calcul local, sans réseau)

# ─── Source des calculs ──────────────────────────────────────────────────────
# local : Astronomy Engine sur la machine (Soleil, Lune, planètes) — par défaut
# imcce : service en ligne Miriade (astéroïdes, comètes, satellites naturels)
# time  : temps astronomique (jour julien, temps sidéral…), repris de ha-meeus-astronomy
CONF_SOURCE = "source"
SOURCE_LOCAL = "local"
SOURCE_IMCCE = "imcce"
SOURCE_TIME = "time"
SOURCES = {
    SOURCE_LOCAL: "Calcul local (sans Internet)",
    SOURCE_IMCCE: "Service IMCCE Miriade (en ligne)",
}
TIME_OBJECT_NAME = "Temps astronomique"

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


def _sensor(name, unit, icon, state_class="measurement", device_class=None, description=""):
    return {
        "name": name,
        "description": description or name,
        "unit": unit,
        "icon": icon,
        "device_class": device_class,
        "state_class": state_class,
    }


# Capteurs propres au calcul local (Soleil, Lune, planètes)
LOCAL_SENSORS = {
    "altitude": _sensor("Hauteur", "°", "mdi:elevation-rise", description="Hauteur au-dessus de l'horizon"),
    "azimuth": _sensor("Azimut", "°", "mdi:compass-outline"),
    "illumination": _sensor("Fraction éclairée", "%", "mdi:brightness-6"),
    "constellation": _sensor("Constellation", None, "mdi:star-four-points-outline", state_class=None),
    "rise": _sensor("Lever", None, "mdi:arrow-up-bold-circle-outline", state_class=None, device_class="timestamp"),
    "transit": _sensor("Passage au méridien", None, "mdi:arrow-collapse-up", state_class=None, device_class="timestamp"),
    "set": _sensor("Coucher", None, "mdi:arrow-down-bold-circle-outline", state_class=None, device_class="timestamp"),
}

# Capteurs supplémentaires pour la Lune
MOON_SENSORS = {
    "moon_phase": _sensor("Phase de la Lune", None, "mdi:moon-waxing-gibbous", state_class=None),
    "moon_age": _sensor("Âge de la Lune", "j", "mdi:calendar-month-outline"),
    "distance_km": _sensor("Distance", "km", "mdi:ruler", description="Distance au lieu d'observation"),
}

# Capteurs de temps astronomique (repris de ha-meeus-astronomy)
TIME_SENSORS = {
    "julian_day": _sensor("Jour julien", "j", "mdi:calendar-clock"),
    "modified_julian_day": _sensor("Jour julien modifié", "j", "mdi:calendar-clock"),
    "days_since_j2000": _sensor("Jours depuis J2000", "j", "mdi:timer-sand"),
    "day_of_week": _sensor("Jour de la semaine", None, "mdi:calendar-week", state_class=None),
    "day_of_year": _sensor("Jour de l'année", None, "mdi:calendar-today", state_class=None),
    "local_sidereal_time": _sensor("Temps sidéral local", None, "mdi:star-clock", state_class=None),
    "greenwich_sidereal_time": _sensor("Temps sidéral de Greenwich", None, "mdi:earth", state_class=None),
    "equation_of_time": _sensor("Équation du temps", "min", "mdi:sun-clock"),
}

# Tous les capteurs connus, pour retrouver la description d'un type
ALL_SENSORS = {**SENSORS_AVAILABLE, **LOCAL_SENSORS, **MOON_SENSORS, **TIME_SENSORS}
