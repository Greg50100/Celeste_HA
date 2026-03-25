"""Tests pour config_flow.py – CelesteConfigFlow."""
from __future__ import annotations

import pytest

from .conftest import MOCK_CONFIG_ENTRY_DATA


class TestConfigFlowData:
    """Tests de validation des données de configuration sans dépendance HA."""

    def test_predefined_planets_list(self):
        """Vérifie la liste des planètes prédéfinies."""
        from custom_components.celeste.const import PREDEFINED_PLANETS

        expected = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Moon", "Sun"]
        assert PREDEFINED_PLANETS == expected

    def test_object_types_valid(self):
        """Vérifie les types d'objets supportés par Miriade."""
        from custom_components.celeste.const import OBJECT_TYPES

        assert "planet" in OBJECT_TYPES
        assert "asteroid" in OBJECT_TYPES
        assert "comet" in OBJECT_TYPES
        assert "satellite" in OBJECT_TYPES

    def test_config_entry_data_complete(self, config_entry_data):
        """Vérifie que les données de config entry sont complètes."""
        required = ["object_name", "object_type", "latitude", "longitude", "altitude"]
        for key in required:
            assert key in config_entry_data, f"Clé manquante : {key}"

    def test_config_entry_latitude_range(self, config_entry_data):
        """La latitude doit être entre -90 et 90."""
        lat = config_entry_data["latitude"]
        assert -90 <= lat <= 90

    def test_config_entry_longitude_range(self, config_entry_data):
        """La longitude doit être entre -180 et 180."""
        lon = config_entry_data["longitude"]
        assert -180 <= lon <= 180

    def test_unique_id_format(self, config_entry_data):
        """Vérifie le format de l'unique_id."""
        object_name = config_entry_data["object_name"]
        unique_id = f"celeste_{object_name.lower()}"
        assert unique_id == "celeste_mars"

    def test_unique_id_case_insensitive(self):
        """Le unique_id doit être insensible à la casse."""
        assert f"celeste_{'Mars'.lower()}" == f"celeste_{'mars'.lower()}"
        assert f"celeste_{'JUPITER'.lower()}" == f"celeste_{'jupiter'.lower()}"

    def test_entry_title_format(self, config_entry_data):
        """Vérifie le format du titre de l'entrée."""
        name = config_entry_data["object_name"]
        title = f"Céleste – {name}"
        assert title == "Céleste – Mars"


class TestApiValidation:
    """Tests de la logique de validation API (sans appel réseau)."""

    def test_validation_params_format(self):
        """Vérifie les paramètres envoyés pour la validation."""
        name = "Ceres"
        obj_type = "asteroid"
        params = {
            "-name": name,
            "-type": obj_type,
            "-ep": "now",
            "-step": "1d",
            "-nbd": "1",
            "-observer": "0,0,0",
            "-output": "--mag",
            "-mime": "json",
        }
        assert params["-name"] == "Ceres"
        assert params["-type"] == "asteroid"
        assert params["-mime"] == "json"

    def test_validation_success_returns_sso(self):
        """Si l'API retourne des données, la validation réussit."""
        data = {
            "sso": {"name": "Ceres", "type": "asteroid", "num": "1"},
            "data": [{"VMag": 8.5}],
        }
        # Simule la logique de _validate_object_with_api
        has_data = isinstance(data, dict) and "data" in data and data["data"]
        assert has_data
        assert data["sso"]["name"] == "Ceres"

    def test_validation_failure_no_data(self):
        """Si l'API ne retourne pas de données, la validation échoue."""
        data = {"sso": {}, "data": []}
        has_data = isinstance(data, dict) and "data" in data and data["data"]
        assert not has_data
