"""Tests pour les sensors numériques de Céleste."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.celeste.const import (
    CONF_ENABLE_SENSORS,
    CONF_OBJECT_NAME,
    DEFAULT_ENABLE_SENSORS,
    DOMAIN,
    SENSORS_AVAILABLE,
)
from custom_components.celeste.sensor import CelesteNumericSensor


class TestCelesteNumericSensor:
    """Tests des sensors numériques."""

    @pytest.fixture
    def mock_coordinator(self):
        """Crée un mock du CelesteCoordinator."""
        coord = MagicMock()
        coord.last_update_success = True
        return coord

    @pytest.fixture
    def mock_entry(self):
        """Crée une mock config entry."""
        entry = MagicMock()
        entry.entry_id = "test_entry_id"
        entry.data = {CONF_OBJECT_NAME: "Mars"}
        entry.options = {CONF_ENABLE_SENSORS: True}
        return entry

    def test_numeric_sensor_initialization(self, mock_coordinator, mock_entry):
        """Test que le sensor numérique s'initialise correctement."""
        sensor = CelesteNumericSensor(
            mock_coordinator, mock_entry, "Mars", "magnitude"
        )

        assert sensor._sensor_type == "magnitude"
        assert sensor._object_name == "Mars"
        assert sensor._attr_name == "Magnitude"
        assert sensor._attr_native_unit_of_measurement == "mag"

    def test_numeric_sensor_unique_id(self, mock_coordinator, mock_entry):
        """Test que chaque sensor a un unique ID unique."""
        sensors = [
            CelesteNumericSensor(
                mock_coordinator, mock_entry, "Mars", sensor_type
            )
            for sensor_type in ["magnitude", "elongation", "distance"]
        ]

        unique_ids = [sensor.unique_id for sensor in sensors]
        # Tous les IDs doivent être uniques
        assert len(unique_ids) == len(set(unique_ids))

    def test_numeric_sensor_available_with_data(
        self, mock_coordinator, mock_entry
    ):
        """Test que le sensor est disponible si les données contiennent la clé."""
        mock_coordinator.last_update_success = True
        mock_coordinator.data = {
            "magnitude": 1.5,
            "elongation": 16.83,
            "distance": 2.305,
        }
        sensor = CelesteNumericSensor(
            mock_coordinator, mock_entry, "Mars", "magnitude"
        )

        assert sensor.available is True

    def test_numeric_sensor_unavailable_without_data(
        self, mock_coordinator, mock_entry
    ):
        """Test que le sensor est indisponible si la clé manque."""
        mock_coordinator.last_update_success = True
        mock_coordinator.data = {
            "elongation": 16.83,
            # magnitude manquante
        }
        sensor = CelesteNumericSensor(
            mock_coordinator, mock_entry, "Mars", "magnitude"
        )

        assert sensor.available is False

    def test_numeric_sensor_value_retrieval(self, mock_coordinator, mock_entry):
        """Test que le sensor retourne la bonne valeur."""
        mock_coordinator.data = {
            "magnitude": 1.168,
            "elongation": 16.83,
            "distance": 2.305,
        }
        sensor = CelesteNumericSensor(
            mock_coordinator, mock_entry, "Mars", "magnitude"
        )

        assert sensor.native_value == 1.168

    def test_numeric_sensor_value_none_when_no_data(
        self, mock_coordinator, mock_entry
    ):
        """Test que le sensor retourne None si pas de données."""
        mock_coordinator.data = None
        sensor = CelesteNumericSensor(
            mock_coordinator, mock_entry, "Mars", "magnitude"
        )

        assert sensor.native_value is None

    def test_numeric_sensor_value_none_when_key_missing(
        self, mock_coordinator, mock_entry
    ):
        """Test que le sensor retourne None si la clé manque."""
        mock_coordinator.data = {"elongation": 16.83}
        sensor = CelesteNumericSensor(
            mock_coordinator, mock_entry, "Mars", "magnitude"
        )

        assert sensor.native_value is None

    def test_all_sensors_available(self):
        """Test que toutes les sensors disponibles ont les config correctes."""
        for sensor_type, config in SENSORS_AVAILABLE.items():
            assert "name" in config
            assert "unit" in config
            assert "icon" in config
            assert "state_class" in config

    def test_device_info_consistency(self, mock_coordinator, mock_entry):
        """Test que device_info est cohérent."""
        sensor = CelesteNumericSensor(
            mock_coordinator, mock_entry, "Mars", "magnitude"
        )
        device_info = sensor.device_info

        assert isinstance(device_info, dict)
        assert (DOMAIN, "test_entry_id") in device_info["identifiers"]
        assert "Céleste" in device_info["name"]
        assert "Mars" in device_info["name"]

    def test_sensor_icon_configuration(self, mock_coordinator, mock_entry):
        """Test que chaque sensor a la bonne icône."""
        expected_icons = {
            "magnitude": "mdi:brightness-7",
            "elongation": "mdi:angle-acute",
            "distance": "mdi:ruler",
            "phase": "mdi:circle-half-full",
            "radial_velocity": "mdi:speedometer",
        }

        for sensor_type, expected_icon in expected_icons.items():
            sensor = CelesteNumericSensor(
                mock_coordinator, mock_entry, "Mars", sensor_type
            )
            assert sensor.icon == expected_icon

    def test_sensor_unit_configuration(self, mock_coordinator, mock_entry):
        """Test que chaque sensor a la bonne unité."""
        expected_units = {
            "magnitude": "mag",
            "elongation": "°",
            "distance": "ua",
            "phase": "°",
            "radial_velocity": "km/s",
        }

        for sensor_type, expected_unit in expected_units.items():
            sensor = CelesteNumericSensor(
                mock_coordinator, mock_entry, "Mars", sensor_type
            )
            assert sensor.native_unit_of_measurement == expected_unit

    def test_sensor_creation_for_each_type(self, mock_coordinator, mock_entry):
        """Test que les sensors se créent correctement pour chaque type."""
        sensors = [
            CelesteNumericSensor(
                mock_coordinator, mock_entry, "Mars", sensor_type
            )
            for sensor_type in SENSORS_AVAILABLE.keys()
        ]

        # Vérifier qu'on a un sensor par type
        assert len(sensors) == len(SENSORS_AVAILABLE)

        # Vérifier que chaque sensor a le bon type
        for sensor in sensors:
            assert sensor._sensor_type in SENSORS_AVAILABLE
