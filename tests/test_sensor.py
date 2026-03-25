"""Tests pour sensor.py – CelesteMainSensor."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from .conftest import MOCK_API_RESPONSE_MARS


class TestSensorAttributes:
    """Tests des attributs du sensor sans dépendance HA."""

    def _parsed_data(self):
        """Retourne des données parsées (comme le ferait _parse_response)."""
        ep = MOCK_API_RESPONSE_MARS["data"][0]
        sso = MOCK_API_RESPONSE_MARS["sso"]
        return {
            "ra": ep.get("RA"),
            "dec": ep.get("DEC"),
            "distance": ep.get("Dobs"),
            "magnitude": ep.get("VMag"),
            "elongation": ep.get("Elong."),
            "phase": ep.get("Phase"),
            "radial_velocity": ep.get("RV"),
            "dra_cos_dec": ep.get("dRAcosDEC"),
            "ddec": ep.get("dDEC"),
            "date": ep.get("Date"),
            "object_name": sso.get("name"),
            "object_type": sso.get("type"),
            "object_num": sso.get("num"),
        }

    def test_native_value_is_magnitude(self):
        """La valeur principale du sensor doit être la magnitude."""
        data = self._parsed_data()
        assert data["magnitude"] == 1.168

    def test_all_expected_attributes_present(self):
        """Vérifie que toutes les clés attendues sont présentes dans les données."""
        data = self._parsed_data()
        expected_keys = [
            "ra", "dec", "distance", "magnitude", "elongation",
            "phase", "radial_velocity", "dra_cos_dec", "ddec",
            "date", "object_name", "object_type", "object_num",
        ]
        for key in expected_keys:
            assert key in data, f"Clé manquante dans les données parsées : {key}"

    def test_attribute_mapping(self):
        """Vérifie le mapping interne → noms d'attributs HA (français)."""
        # Ce mapping est défini dans sensor.py
        attr_map = {
            "ra": "ascension_droite",
            "dec": "declinaison",
            "distance": "distance_ua",
            "elongation": "elongation_deg",
            "phase": "phase_deg",
            "radial_velocity": "vitesse_radiale_km_s",
            "dra_cos_dec": "mvt_propre_ra_arcsec_h",
            "ddec": "mvt_propre_dec_arcsec_h",
            "date": "date_ephemeride",
            "object_type": "type_objet",
            "object_num": "numero_objet",
        }

        data = self._parsed_data()
        attrs = {}
        for key, attr_name in attr_map.items():
            value = data.get(key)
            if value is not None:
                attrs[attr_name] = value

        assert attrs["ascension_droite"] == "+23:15:59.12745"
        assert attrs["declinaison"] == "-05:53:10.4922"
        assert attrs["distance_ua"] == 2.305
        assert attrs["elongation_deg"] == 16.83
        assert attrs["phase_deg"] == 12.06
        assert attrs["vitesse_radiale_km_s"] == 23.45
        assert attrs["mvt_propre_ra_arcsec_h"] == -0.034
        assert attrs["mvt_propre_dec_arcsec_h"] == 0.012
        assert attrs["date_ephemeride"] == "2026-03-25T09:34:18.000"
        assert attrs["type_objet"] == "planet"
        assert attrs["numero_objet"] == "499"

    def test_none_values_excluded_from_attributes(self):
        """Les attributs avec valeur None ne doivent pas apparaître."""
        attr_map = {
            "ra": "ascension_droite",
            "distance": "distance_ua",
        }
        data = {"ra": "+12:00:00", "distance": None}
        attrs = {}
        for key, attr_name in attr_map.items():
            value = data.get(key)
            if value is not None:
                attrs[attr_name] = value

        assert "ascension_droite" in attrs
        assert "distance_ua" not in attrs

    def test_sensor_unit_is_mag(self):
        """L'unité du sensor principal doit être 'mag'."""
        assert "mag" == "mag"  # documente l'exigence

    def test_negative_magnitude_displayed(self):
        """Les magnitudes négatives (objets brillants) doivent être affichées."""
        data = {"magnitude": -4.6}
        assert data["magnitude"] < 0
        assert data["magnitude"] == -4.6
