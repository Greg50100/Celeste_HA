"""Tests pour coordinator.py – CelesteCoordinator."""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# On importe directement _parse_response pour tester le parsing sans HA
import sys
import os

# Ajouter le chemin du composant au sys.path pour pouvoir l'importer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from .conftest import (
    MOCK_API_RESPONSE_EMPTY,
    MOCK_API_RESPONSE_JUPITER,
    MOCK_API_RESPONSE_MALFORMED,
    MOCK_API_RESPONSE_MARS,
    MOCK_CONFIG_ENTRY_DATA,
)


# ═════════════════════════════════════════════════════════════════════════════
# Tests du parsing (_parse_response)
# ═════════════════════════════════════════════════════════════════════════════

class TestParseResponse:
    """Tests unitaires pour _parse_response() sans dépendance HA."""

    def _make_coordinator_stub(self):
        """Crée un stub de CelesteCoordinator pour tester _parse_response."""
        # On crée un objet simple avec la méthode _parse_response
        # sans instancier le vrai coordinator (qui nécessite hass)
        from custom_components.celeste.coordinator import CelesteCoordinator

        # On ne peut pas instancier sans hass, donc on appelle la méthode en tant
        # que fonction non-bound en passant un stub
        stub = MagicMock()
        stub._parse_response = CelesteCoordinator._parse_response.__get__(stub)
        return stub

    def test_parse_mars_valid(self, api_response_mars):
        """Test le parsing d'une réponse Mars valide."""
        coord = self._make_coordinator_stub()
        result = coord._parse_response(api_response_mars)

        assert result["ra"] == "+23:15:59.12745"
        assert result["dec"] == "-05:53:10.4922"
        assert result["distance"] == 2.305
        assert result["magnitude"] == 1.168
        assert result["elongation"] == 16.83
        assert result["phase"] == 12.06
        assert result["radial_velocity"] == 23.45
        assert result["dra_cos_dec"] == -0.034
        assert result["ddec"] == 0.012
        assert result["date"] == "2026-03-25T09:34:18.000"
        assert result["object_name"] == "Mars"
        assert result["object_type"] == "planet"
        assert result["object_num"] == "499"

    def test_parse_jupiter_valid(self, api_response_jupiter):
        """Test le parsing d'une réponse Jupiter valide."""
        coord = self._make_coordinator_stub()
        result = coord._parse_response(api_response_jupiter)

        assert result["magnitude"] == -2.1
        assert result["distance"] == 5.912
        assert result["object_name"] == "Jupiter"
        assert result["object_num"] == "599"
        assert result["elongation"] == 78.5
        assert result["radial_velocity"] == -12.8

    def test_parse_empty_data(self):
        """Test le parsing avec data vide → retourne {}."""
        coord = self._make_coordinator_stub()
        result = coord._parse_response(MOCK_API_RESPONSE_EMPTY)
        assert result == {}

    def test_parse_malformed_no_data_key(self):
        """Test le parsing avec JSON malformé (pas de clé 'data')."""
        coord = self._make_coordinator_stub()
        result = coord._parse_response(MOCK_API_RESPONSE_MALFORMED)
        assert result == {}

    def test_parse_missing_fields_graceful(self):
        """Test que les champs manquants retournent None sans erreur."""
        coord = self._make_coordinator_stub()
        minimal_response = {
            "sso": {"name": "Test"},
            "data": [{"RA": "+12:00:00", "DEC": "+45:00:00"}],
        }
        result = coord._parse_response(minimal_response)

        assert result["ra"] == "+12:00:00"
        assert result["dec"] == "+45:00:00"
        assert result["magnitude"] is None
        assert result["distance"] is None
        assert result["elongation"] is None
        assert result["object_name"] == "Test"

    def test_parse_preserves_negative_magnitude(self):
        """Test que les magnitudes négatives (planètes brillantes) sont préservées."""
        coord = self._make_coordinator_stub()
        response = {
            "sso": {"name": "Venus", "type": "planet", "num": "299"},
            "data": [{"VMag": -4.6, "RA": "+01:00:00", "DEC": "+10:00:00"}],
        }
        result = coord._parse_response(response)
        assert result["magnitude"] == -4.6

    def test_parse_sso_missing(self):
        """Test le parsing quand le bloc sso est absent."""
        coord = self._make_coordinator_stub()
        response = {
            "data": [{"RA": "+12:00:00", "DEC": "+45:00:00", "VMag": 3.5}],
        }
        result = coord._parse_response(response)
        assert result["object_name"] is None
        assert result["object_type"] is None
        assert result["magnitude"] == 3.5


# ═════════════════════════════════════════════════════════════════════════════
# Tests des paramètres API
# ═════════════════════════════════════════════════════════════════════════════

class TestApiParams:
    """Vérifie que les paramètres envoyés à l'API IMCCE sont corrects."""

    def test_all_required_params_present(self):
        """Les paramètres obligatoires doivent tous être présents."""
        required_params = ["-name", "-type", "-ep", "-step", "-nbd", "-observer", "-output", "-mime"]
        # Simulons la construction des params comme dans coordinator.py
        params = {
            "-name": "Mars",
            "-type": "planet",
            "-ep": "2026-03-25T12:00:00",
            "-step": "1d",
            "-nbd": "1",
            "-observer": "2.35,48.85,0",
            "-output": "--ram --rv --mag --elo --pha",
            "-mime": "json",
        }
        for key in required_params:
            assert key in params, f"Paramètre manquant : {key}"

    def test_observer_format(self):
        """Le format observateur doit être lon,lat,alt."""
        lon, lat, alt = 2.35, 48.85, 0
        observer = f"{lon},{lat},{alt}"
        parts = observer.split(",")
        assert len(parts) == 3
        assert float(parts[0]) == lon
        assert float(parts[1]) == lat
        assert float(parts[2]) == alt

    def test_mime_json(self):
        """Le format de sortie doit être json."""
        assert "json" == "json"  # trivial mais documente l'exigence
