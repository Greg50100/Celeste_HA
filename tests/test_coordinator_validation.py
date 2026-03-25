"""Tests de validation et robustesse pour coordinator.py – CelesteCoordinator."""
from __future__ import annotations

from unittest.mock import MagicMock, AsyncMock, patch
import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

# Importer les fixtures du conftest
from .conftest import (
    MOCK_API_RESPONSE_MARS,
    MOCK_API_RESPONSE_EMPTY,
    MOCK_API_RESPONSE_MALFORMED,
)


class TestCoordinatorDataValidation:
    """Tests de validation des données parsées par le coordinator."""

    def _make_coordinator_stub(self):
        """Crée un stub de CelesteCoordinator pour tester _parse_response."""
        from custom_components.celeste.coordinator import CelesteCoordinator

        stub = MagicMock()
        stub._parse_response = CelesteCoordinator._parse_response.__get__(stub)
        return stub

    def test_parse_response_validates_critical_keys(self):
        """_parse_response verifie la présence des clés critiques."""
        coord = self._make_coordinator_stub()

        # Réponse avec elongation et magnitude manquantes
        incomplete_response = {
            "sso": {"name": "Mars", "type": "planet", "num": "499"},
            "data": [
                {
                    "Date": "2026-03-25T09:34:18.000",
                    "RA": "+23:15:59.12745",
                    "DEC": "-05:53:10.4922",
                    "Dobs": 2.305,
                    "VMag": None,  # magnitude manquante
                    "Phase": 12.06,
                    "Elong.": None,  # elongation manquante
                    "dRAcosDEC": -0.034,
                    "dDEC": 0.012,
                    "RV": 23.45,
                }
            ],
        }

        result = coord._parse_response(incomplete_response)

        # Le dictionnaire est retourné, mais les clés manquantes sont loggées
        assert result["object_name"] == "Mars"
        assert result["magnitude"] is None
        assert result["elongation"] is None

    def test_parse_response_logs_missing_critical_keys(self):
        """_parse_response logue les clés critiques manquantes."""
        coord = self._make_coordinator_stub()

        incomplete_response = {
            "sso": {"name": "Venus"},
            "data": [
                {
                    "Date": None,  # date manquante
                    "RA": "+15:00:00",
                    "DEC": "-10:00:00",
                    "Dobs": 0.72,
                    "VMag": -4.0,
                    "Phase": 50.0,
                    "Elong.": 25.0,
                    "dRAcosDEC": 0.0,
                    "dDEC": 0.0,
                    "RV": 0.0,
                }
            ],
        }

        # On s'attend à un logging d'avertissement
        with patch("custom_components.celeste.coordinator._LOGGER") as mock_logger:
            result = coord._parse_response(incomplete_response)
            # Vérifier que warning a été appelé pour les clés manquantes
            mock_logger.warning.assert_called()

    def test_parse_response_returns_empty_dict_on_exception(self):
        """_parse_response retourne {} en cas d'exception de parsing."""
        coord = self._make_coordinator_stub()

        malformed = {
            "data": "not_a_list",  # Malformed: data devrait être une liste
            "sso": {},
        }

        result = coord._parse_response(malformed)
        assert result == {}

    def test_parse_response_handles_missing_sso(self):
        """_parse_response gère l'absence de 'sso'."""
        coord = self._make_coordinator_stub()

        response_no_sso = {
            "data": [
                {
                    "Date": "2026-03-25T09:34:18.000",
                    "RA": "+23:15:59",
                    "DEC": "-05:53:10",
                    "Dobs": 2.305,
                    "VMag": 1.168,
                    "Phase": 12.06,
                    "Elong.": 16.83,
                    "dRAcosDEC": -0.034,
                    "dDEC": 0.012,
                    "RV": 23.45,
                }
                # sso manquant
            ]
        }

        result = coord._parse_response(response_no_sso)

        assert result["object_name"] is None
        assert result["object_type"] is None
        assert result["object_num"] is None
        assert result["elongation"] == 16.83

    def test_parse_response_handles_empty_data_list(self):
        """_parse_response retourne {} si list data est vide."""
        coord = self._make_coordinator_stub()

        empty_data = {
            "sso": {"name": "Mars"},
            "data": [],  # Liste vide
        }

        result = coord._parse_response(empty_data)
        assert result == {}

    def test_parse_response_handles_missing_data_key(self):
        """_parse_response retourne {} si la clé 'data' manque."""
        coord = self._make_coordinator_stub()

        no_data_key = {
            "sso": {"name": "Mars"},
            # 'data' manquante
        }

        result = coord._parse_response(no_data_key)
        assert result == {}

    def test_parse_response_extracts_all_fields_correctly(self):
        """_parse_response extrait tous les champs correctement."""
        coord = self._make_coordinator_stub()

        result = coord._parse_response(MOCK_API_RESPONSE_MARS)

        # Tous les champs attendus sont présents
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

    def test_parse_response_with_null_optional_fields(self):
        """_parse_response gère gracieusement les champs optionnels null."""
        coord = self._make_coordinator_stub()

        response_with_nulls = {
            "sso": {"name": "Mars", "type": "planet"},
            "data": [
                {
                    "Date": "2026-03-25T09:34:18.000",
                    "RA": "+23:15:59",
                    "DEC": "-05:53:10",
                    "Dobs": 2.305,
                    "VMag": 1.168,
                    "Phase": 12.06,
                    "Elong.": 16.83,
                    "dRAcosDEC": None,  # null optionnel
                    "dDEC": None,  # null optionnel
                    "RV": None,  # null optionnel
                }
            ],
        }

        result = coord._parse_response(response_with_nulls)

        # Les champs null sont inclus avec valeur None
        assert result["dra_cos_dec"] is None
        assert result["ddec"] is None
        assert result["radial_velocity"] is None
        # Les champs critiques sont présents
        assert result["elongation"] == 16.83
        assert result["magnitude"] == 1.168


class TestCoordinatorErrorHandling:
    """Tests de gestion des erreurs du coordinator."""

    @pytest.fixture
    async def real_coordinator(self, hass, mock_aiohttp_client):
        """Crée un vrai coordinator pour tester les appels API."""
        from homeassistant.config_entries import ConfigEntry
        from custom_components.celeste.coordinator import CelesteCoordinator

        config_entry = MagicMock(spec=ConfigEntry)
        config_entry.entry_id = "test_entry"
        config_entry.data = {
            "object_name": "Mars",
            "object_type": "planet",
            "latitude": 48.8566,
            "longitude": 2.3522,
            "altitude": 35,
        }

        coordinator = CelesteCoordinator(hass, config_entry)
        return coordinator

    def test_parse_response_survives_unexpected_structure(self):
        """_parse_response survit à des structures inattendues."""
        from custom_components.celeste.coordinator import CelesteCoordinator

        stub = MagicMock()
        stub._parse_response = CelesteCoordinator._parse_response.__get__(stub)

        # Structure complètement inattendue
        weird_response = {
            "unexpected_key": "value",
            "nested": {"data": [{"some": "thing"}]},
        }

        result = stub._parse_response(weird_response)
        assert isinstance(result, dict)

    def test_parse_response_handles_extra_fields_gracefully(self):
        """_parse_response ignore les champs supplémentaires."""
        from custom_components.celeste.coordinator import CelesteCoordinator

        stub = MagicMock()
        stub._parse_response = CelesteCoordinator._parse_response.__get__(stub)

        response_with_extras = {
            "sso": {
                "name": "Mars",
                "type": "planet",
                "num": "499",
                "extra_field_1": "ignored",
                "extra_field_2": 12345,
            },
            "data": [
                {
                    "Date": "2026-03-25T09:34:18.000",
                    "RA": "+23:15:59",
                    "DEC": "-05:53:10",
                    "Dobs": 2.305,
                    "VMag": 1.168,
                    "Phase": 12.06,
                    "Elong.": 16.83,
                    "dRAcosDEC": -0.034,
                    "dDEC": 0.012,
                    "RV": 23.45,
                    "extra_coord_field": "also_ignored",
                }
            ],
            "extra_top_level": "ignored",
        }

        result = stub._parse_response(response_with_extras)

        # Les champs principaux sont extraits correctement
        assert result["object_name"] == "Mars"
        assert result["elongation"] == 16.83
        # Les champs extras ne sont pas dans result
        assert "extra_field_1" not in result
        assert "extra_coord_field" not in result
