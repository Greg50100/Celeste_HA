"""Choix de la source de calcul et des entités créées."""
from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.celeste.binary_sensor import CelesteAboveHorizonSensor
from custom_components.celeste.const import MOON_SENSORS, SOURCE_IMCCE, SOURCE_LOCAL, SOURCE_TIME, TIME_SENSORS
from custom_components.celeste.coordinator import CelesteCoordinator
from custom_components.celeste.helpers import build_device_info, get_source
from custom_components.celeste.sensor import CelesteNumericSensor, sensor_types_for


def entry(data, options=None, entry_id="e1"):
    return SimpleNamespace(data=data, options=options or {}, entry_id=entry_id)


class TestGetSource:
    def test_local_planet(self):
        assert get_source(entry({"object_name": "Mars", "object_type": "planet", "source": "local"})) == SOURCE_LOCAL

    def test_entries_from_v01_stay_on_imcce(self):
        assert get_source(entry({"object_name": "Mars", "object_type": "planet"})) == SOURCE_IMCCE

    def test_option_overrides_data(self):
        e = entry({"object_name": "Venus", "object_type": "planet", "source": "local"}, {"source": "imcce"})
        assert get_source(e) == SOURCE_IMCCE

    def test_unknown_body_falls_back_to_imcce(self):
        assert get_source(entry({"object_name": "Ceres", "object_type": "asteroid", "source": "local"})) == SOURCE_IMCCE

    def test_time(self):
        assert get_source(entry({"object_name": "Temps astronomique", "source": "time"})) == SOURCE_TIME

    def test_device_info_by_source(self):
        local = build_device_info(entry({"object_name": "Mars", "object_type": "planet", "source": "local"}), "Mars")
        assert local["manufacturer"] == "Astronomy Engine"
        assert build_device_info(entry({"source": "time"}), "Temps astronomique")["model"].startswith("Temps")
        assert local["name"] == "Céleste – Mars"
        assert build_device_info(entry({"object_name": "Sun", "source": "local"}), "Sun")["name"] == "Céleste – Soleil"


class TestSensorTypes:
    def test_imcce_keeps_original_sensors(self):
        assert "radial_velocity" in sensor_types_for(SOURCE_IMCCE, "Mars")

    def test_moon(self):
        types = sensor_types_for(SOURCE_LOCAL, "Moon")
        assert set(MOON_SENSORS) <= set(types)
        assert "distance" not in types and "radial_velocity" not in types

    def test_sun_has_no_phase(self):
        types = sensor_types_for(SOURCE_LOCAL, "Sun")
        assert "phase" not in types and "illumination" not in types and "rise" in types

    def test_time(self):
        assert sensor_types_for(SOURCE_TIME, "Temps astronomique") == list(TIME_SENSORS)


class TestEntities:
    @pytest.fixture
    def coordinator(self):
        coord = MagicMock()
        coord.last_update_success = True
        return coord

    def test_timestamp_sensor_returns_datetime(self, coordinator):
        coordinator.data = {"rise": "2026-10-23T06:40:29+00:00"}
        sensor = CelesteNumericSensor(coordinator, entry({"object_name": "Sun"}), "Sun", "rise")
        assert isinstance(sensor.native_value, datetime)
        assert sensor.native_value.tzinfo is not None

    def test_text_sensor_has_no_state_class(self, coordinator):
        coordinator.data = {"constellation": "Vierge"}
        sensor = CelesteNumericSensor(coordinator, entry({"object_name": "Sun"}), "Sun", "constellation")
        assert sensor.native_value == "Vierge"
        assert sensor.state_class is None

    def test_above_horizon(self, coordinator):
        coordinator.data = {"altitude": 12.0}
        sensor = CelesteAboveHorizonSensor(coordinator, entry({"object_name": "Sun"}), "Sun")
        assert sensor.is_on is True
        assert sensor.name == "Jour"
        coordinator.data = {"altitude": -3.0}
        assert sensor.is_on is False


class TestCoordinatorDispatch:
    async def test_local_update_runs_in_executor(self):
        stub = MagicMock()
        stub.source = SOURCE_LOCAL
        stub._location = MagicMock(return_value=(49.6337, -1.6222, 10))
        stub.entry.data = {"object_name": "Jupiter"}
        stub.hass.async_add_executor_job = AsyncMock(side_effect=lambda func, *args: func(*args))
        data = await CelesteCoordinator._async_update_data(stub)
        assert data["object_name"] == "Jupiter"
        assert "altitude" in data
        stub.hass.async_add_executor_job.assert_awaited_once()

    async def test_time_update(self):
        stub = MagicMock()
        stub.source = SOURCE_TIME
        stub._location = MagicMock(return_value=(0, 0, 0))
        stub.hass.async_add_executor_job = AsyncMock(side_effect=lambda func, *args: func(*args))
        data = await CelesteCoordinator._async_update_data(stub)
        assert "julian_day" in data
