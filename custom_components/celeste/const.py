"""Constantes pour l'intégration Céleste."""

DOMAIN = "celeste"
PLATFORMS = ["sensor"]

# URL de l'API IMCCE Miriade
MIRIADE_API_URL = "https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php"

# Paramètres de configuration
CONF_OBJECT_NAME = "object_name"
CONF_OBJECT_TYPE = "object_type"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_ALTITUDE = "altitude"
CONF_STEP = "step"
CONF_NB_STEPS = "nb_steps"

# Valeurs par défaut
DEFAULT_STEP = "1d"
DEFAULT_NB_STEPS = 1
DEFAULT_ALTITUDE = 0

# Types d'objets célestes supportés
OBJECT_TYPES = {
    "planet": "Planète",
    "asteroid": "Astéroïde",
    "comet": "Comète",
    "satellite": "Satellite naturel",
}

# Planètes prédéfinies
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

# Attributs des capteurs
ATTR_RA = "ascension_droite"
ATTR_DEC = "declinaison"
ATTR_DISTANCE = "distance"
ATTR_MAGNITUDE = "magnitude"
ATTR_ELONGATION = "elongation"
ATTR_PHASE = "phase"
ATTR_RISE = "lever"
ATTR_SET = "coucher"
ATTR_TRANSIT = "transit"
ATTR_CONSTELLATION = "constellation"
ATTR_OBJECT_TYPE = "type_objet"

# Intervalle de mise à jour (secondes)
UPDATE_INTERVAL = 3600  # 1 heure
