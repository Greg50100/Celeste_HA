"""Fixtures partagées pour les tests Céleste."""
from __future__ import annotations

import pytest

# ─── Données de test : réponse API IMCCE réelle (Mars, 2026-03-25) ──────────

MOCK_API_RESPONSE_MARS = {
    "sso": {
        "num": "499",
        "name": "Mars",
        "type": "planet",
    },
    "coosys": {
        "epoch": "J2000.0",
        "equinox": "ICRF",
        "system": "equatorial",
    },
    "ephemeris": {
        "time_scale": "UTC",
    },
    "data": [
        {
            "Date": "2026-03-25T09:34:18.000",
            "IAU_code": "--1",
            "RA": "+23:15:59.12745",
            "DEC": "-05:53:10.4922",
            "Dobs": 2.305,
            "VMag": 1.168,
            "Phase": 12.06,
            "Elong.": 16.83,
            "dRAcosDEC": -0.034,
            "dDEC": 0.012,
            "RV": 23.45,
        }
    ],
    "datacol": ["Date", "IAU_code", "RA", "DEC", "Dobs", "VMag", "Phase", "Elong.", "dRAcosDEC", "dDEC", "RV"],
    "unit": ["", "", "h:m:s", "d:m:s", "au", "mag", "deg", "deg", "arcsec/h", "arcsec/h", "km/s"],
}

MOCK_API_RESPONSE_JUPITER = {
    "sso": {
        "num": "599",
        "name": "Jupiter",
        "type": "planet",
    },
    "coosys": {
        "epoch": "J2000.0",
        "equinox": "ICRF",
        "system": "equatorial",
    },
    "ephemeris": {
        "time_scale": "UTC",
    },
    "data": [
        {
            "Date": "2026-03-25T12:00:00.000",
            "IAU_code": "--1",
            "RA": "+04:22:11.98765",
            "DEC": "+20:45:32.1234",
            "Dobs": 5.912,
            "VMag": -2.1,
            "Phase": 5.32,
            "Elong.": 78.5,
            "dRAcosDEC": 0.089,
            "dDEC": -0.021,
            "RV": -12.8,
        }
    ],
    "datacol": ["Date", "IAU_code", "RA", "DEC", "Dobs", "VMag", "Phase", "Elong.", "dRAcosDEC", "dDEC", "RV"],
    "unit": ["", "", "h:m:s", "d:m:s", "au", "mag", "deg", "deg", "arcsec/h", "arcsec/h", "km/s"],
}

MOCK_API_RESPONSE_EMPTY = {
    "sso": {},
    "data": [],
}

MOCK_API_RESPONSE_MALFORMED = {
    "error": "Object not found",
}

MOCK_CONFIG_ENTRY_DATA = {
    "object_name": "Mars",
    "object_type": "planet",
    "latitude": 48.85,
    "longitude": 2.35,
    "altitude": 0,
}


@pytest.fixture
def config_entry_data():
    """Retourne des données de config entry de test."""
    return MOCK_CONFIG_ENTRY_DATA.copy()


@pytest.fixture
def api_response_mars():
    """Retourne une réponse API simulée pour Mars."""
    return MOCK_API_RESPONSE_MARS.copy()


@pytest.fixture
def api_response_jupiter():
    """Retourne une réponse API simulée pour Jupiter."""
    return MOCK_API_RESPONSE_JUPITER.copy()
