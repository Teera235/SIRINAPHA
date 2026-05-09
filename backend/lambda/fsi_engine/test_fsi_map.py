"""
Unit tests for FSI Engine — fsi_map module.

Covers:
  • store_fsi_result: stores FSI result and component scores in Supabase
  • generate_fsi_map: generates a collection of FSI results for all areas
  • run_daily_fsi_update: Lambda handler for daily FSI computation
  • _fetch_latest_data_for_area: fetches latest environmental data
  • Zone classification via the FSI Map pipeline

Requirements: 3.7, 3.8
"""

from __future__ import annotations

import importlib
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

_map = importlib.import_module("lambda.fsi_engine.fsi_map")
store_fsi_result = _map.store_fsi_result
generate_fsi_map = _map.generate_fsi_map
run_daily_fsi_update = _map.run_daily_fsi_update
_fetch_latest_data_for_area = _map._fetch_latest_data_for_area

_calc = importlib.import_module("lambda.fsi_engine.fsi_calculator")
calculate_fsi = _calc.calculate_fsi

_models = importlib.import_module("lambda.shared.models")
GeoPoint = _models.GeoPoint
SeasonData = _models.SeasonData
FSIZone = _models.FSIZone
FSIResult = _models.FSIResult
FSIComponentScores = _models.FSIComponentScores
FSIDataCompleteness = _models.FSIDataCompleteness

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

LOCATION = GeoPoint(lat=13.5, lng=100.3)
SEASON_DRY = SeasonData(season="dry", month=3, is_monsoon=False)
NOW = datetime(2024, 6, 15, 8, 0, 0)
AREA_ID = "area-uuid-001"


def _make_fsi_result(
    fsi_value: float = 0.72,
    zone: FSIZone = FSIZone.GREEN,
    location: GeoPoint = LOCATION,
    calculated_at: datetime = NOW,
) -> FSIResult:
    """Create a sample FSIResult for testing."""
    return FSIResult(
        location=location,
        fsi_value=fsi_value,
        zone=zone,
        component_scores=FSIComponentScores(
            sst_score=0.9,
            chl_a_score=1.0,
            depth_score=1.0,
            lunar_score=0.65,
            ndvi_score=0.85,
            season_score=0.7,
        ),
        data_completeness=FSIDataCompleteness(
            available_sources=["chl_a", "depth", "lunar", "ndvi", "season", "sst"],
            missing_sources=[],
            is_complete=True,
        ),
        calculated_at=calculated_at,
    )


def _make_mock_client(
    fsi_insert_id: str = "fsi-uuid-001",
    scores_insert_id: str = "scores-uuid-001",
) -> MagicMock:
    """Create a mock Supabase client that returns predictable IDs."""
    client = MagicMock()

    # fsi_results insert chain
    fsi_insert_resp = MagicMock()
    fsi_insert_resp.data = [{"id": fsi_insert_id}]

    fsi_table = MagicMock()
    fsi_table.insert.return_value.execute.return_value = fsi_insert_resp

    # fsi_component_scores insert chain
    scores_insert_resp = MagicMock()
    scores_insert_resp.data = [{"id": scores_insert_id}]

    scores_table = MagicMock()
    scores_table.insert.return_value.execute.return_value = scores_insert_resp

    def table_router(name: str):
        if name == "fsi_results":
            return fsi_table
        elif name == "fsi_component_scores":
            return scores_table
        return MagicMock()

    client.table.side_effect = table_router
    return client


# ---------------------------------------------------------------------------
# store_fsi_result
# ---------------------------------------------------------------------------


class TestStoreFsiResult:
    """Tests for store_fsi_result function."""

    def test_returns_both_ids(self):
        client = _make_mock_client(
            fsi_insert_id="fsi-123", scores_insert_id="scores-456"
        )
        result = _make_fsi_result()
        ids = store_fsi_result(result, AREA_ID, client=client)

        assert ids["fsi_result_id"] == "fsi-123"
        assert ids["component_scores_id"] == "scores-456"

    def test_inserts_into_fsi_results_table(self):
        client = _make_mock_client()
        result = _make_fsi_result(fsi_value=0.55, zone=FSIZone.YELLOW)
        store_fsi_result(result, AREA_ID, client=client)

        # Verify the fsi_results table was called
        client.table.assert_any_call("fsi_results")
        fsi_table = client.table("fsi_results")
        insert_call = fsi_table.insert.call_args
        row = insert_call[0][0]

        assert row["area_id"] == AREA_ID
        assert row["fsi_value"] == 0.55
        assert row["zone"] == "yellow"
        assert row["is_complete"] is True
        assert row["calculated_at"] == NOW.isoformat()
        assert "POINT(100.3 13.5)" in row["location"]

    def test_inserts_into_component_scores_table(self):
        client = _make_mock_client()
        result = _make_fsi_result()
        store_fsi_result(result, AREA_ID, client=client)

        client.table.assert_any_call("fsi_component_scores")
        scores_table = client.table("fsi_component_scores")
        insert_call = scores_table.insert.call_args
        row = insert_call[0][0]

        assert row["sst_score"] == 0.9
        assert row["chl_a_score"] == 1.0
        assert row["depth_score"] == 1.0
        assert row["lunar_score"] == 0.65
        assert row["ndvi_score"] == 0.85
        assert row["season_score"] == 0.7

    def test_component_scores_linked_to_fsi_result(self):
        client = _make_mock_client(fsi_insert_id="fsi-linked-id")
        result = _make_fsi_result()
        store_fsi_result(result, AREA_ID, client=client)

        scores_table = client.table("fsi_component_scores")
        insert_call = scores_table.insert.call_args
        row = insert_call[0][0]

        assert row["fsi_result_id"] == "fsi-linked-id"

    def test_incomplete_data_stored_correctly(self):
        client = _make_mock_client()
        result = FSIResult(
            location=LOCATION,
            fsi_value=0.45,
            zone=FSIZone.YELLOW,
            component_scores=FSIComponentScores(
                sst_score=0.8, chl_a_score=0.0, depth_score=1.0,
                lunar_score=0.0, ndvi_score=0.0, season_score=0.0,
            ),
            data_completeness=FSIDataCompleteness(
                available_sources=["depth", "sst"],
                missing_sources=["chl_a", "lunar", "ndvi", "season"],
                is_complete=False,
            ),
            calculated_at=NOW,
        )
        store_fsi_result(result, AREA_ID, client=client)

        fsi_table = client.table("fsi_results")
        row = fsi_table.insert.call_args[0][0]
        assert row["is_complete"] is False

    def test_zone_value_is_string(self):
        """Zone should be stored as a plain string, not an enum."""
        client = _make_mock_client()
        result = _make_fsi_result(fsi_value=0.2, zone=FSIZone.RED)
        store_fsi_result(result, AREA_ID, client=client)

        fsi_table = client.table("fsi_results")
        row = fsi_table.insert.call_args[0][0]
        assert row["zone"] == "red"
        assert isinstance(row["zone"], str)


# ---------------------------------------------------------------------------
# generate_fsi_map
# ---------------------------------------------------------------------------


class TestGenerateFsiMap:
    """Tests for generate_fsi_map function."""

    def test_empty_input_returns_empty_list(self):
        fsi_map = generate_fsi_map([])
        assert fsi_map == []

    def test_single_area(self):
        result = _make_fsi_result(fsi_value=0.72, zone=FSIZone.GREEN)
        fsi_map = generate_fsi_map([("area-1", result)])

        assert len(fsi_map) == 1
        entry = fsi_map[0]
        assert entry["area_id"] == "area-1"
        assert entry["fsi_value"] == 0.72
        assert entry["zone"] == "green"

    def test_multiple_areas(self):
        results = [
            ("area-1", _make_fsi_result(fsi_value=0.8, zone=FSIZone.GREEN)),
            ("area-2", _make_fsi_result(fsi_value=0.5, zone=FSIZone.YELLOW)),
            ("area-3", _make_fsi_result(fsi_value=0.2, zone=FSIZone.RED)),
        ]
        fsi_map = generate_fsi_map(results)

        assert len(fsi_map) == 3
        zones = [e["zone"] for e in fsi_map]
        assert zones == ["green", "yellow", "red"]

    def test_entry_contains_location(self):
        loc = GeoPoint(lat=9.95, lng=98.55)
        result = _make_fsi_result(location=loc)
        fsi_map = generate_fsi_map([("area-1", result)])

        assert fsi_map[0]["location"] == {"lat": 9.95, "lng": 98.55}

    def test_entry_contains_component_scores(self):
        result = _make_fsi_result()
        fsi_map = generate_fsi_map([("area-1", result)])

        cs = fsi_map[0]["component_scores"]
        assert cs["sst_score"] == 0.9
        assert cs["chl_a_score"] == 1.0
        assert cs["depth_score"] == 1.0
        assert cs["lunar_score"] == 0.65
        assert cs["ndvi_score"] == 0.85
        assert cs["season_score"] == 0.7

    def test_entry_contains_data_completeness(self):
        result = _make_fsi_result()
        fsi_map = generate_fsi_map([("area-1", result)])

        dc = fsi_map[0]["data_completeness"]
        assert dc["is_complete"] is True
        assert dc["missing_sources"] == []
        assert len(dc["available_sources"]) == 6

    def test_entry_contains_calculated_at(self):
        result = _make_fsi_result(calculated_at=NOW)
        fsi_map = generate_fsi_map([("area-1", result)])

        assert fsi_map[0]["calculated_at"] == NOW.isoformat()

    def test_zone_classification_green(self):
        """FSI > 0.7 should map to green zone in the FSI Map."""
        result = _make_fsi_result(fsi_value=0.85, zone=FSIZone.GREEN)
        fsi_map = generate_fsi_map([("area-1", result)])
        assert fsi_map[0]["zone"] == "green"

    def test_zone_classification_yellow(self):
        """FSI 0.4-0.7 should map to yellow zone in the FSI Map."""
        result = _make_fsi_result(fsi_value=0.55, zone=FSIZone.YELLOW)
        fsi_map = generate_fsi_map([("area-1", result)])
        assert fsi_map[0]["zone"] == "yellow"

    def test_zone_classification_red(self):
        """FSI < 0.4 should map to red zone in the FSI Map."""
        result = _make_fsi_result(fsi_value=0.2, zone=FSIZone.RED)
        fsi_map = generate_fsi_map([("area-1", result)])
        assert fsi_map[0]["zone"] == "red"


# ---------------------------------------------------------------------------
# _fetch_latest_data_for_area
# ---------------------------------------------------------------------------


class TestFetchLatestDataForArea:
    """Tests for _fetch_latest_data_for_area helper."""

    def _make_query_client(
        self,
        area_data: Optional[List[Dict]] = None,
        sst_data: Optional[List[Dict]] = None,
        chl_data: Optional[List[Dict]] = None,
        ndvi_data: Optional[List[Dict]] = None,
    ) -> MagicMock:
        """Build a mock client that returns specified query results."""
        client = MagicMock()

        def make_chain(data):
            """Create a chained mock for select().eq().order().limit().execute()."""
            mock = MagicMock()
            # Support various chain patterns
            mock.select.return_value = mock
            mock.eq.return_value = mock
            mock.order.return_value = mock
            mock.limit.return_value = mock
            resp = MagicMock()
            resp.data = data if data is not None else []
            mock.execute.return_value = resp
            return mock

        area_mock = make_chain(area_data or [{"id": AREA_ID, "name": "Test", "region": "mahachai"}])
        sst_mock = make_chain(sst_data)
        chl_mock = make_chain(chl_data)
        ndvi_mock = make_chain(ndvi_data)

        def table_router(name: str):
            if name == "fishing_areas":
                return area_mock
            elif name == "sst_records":
                return sst_mock
            elif name == "chl_a_records":
                return chl_mock
            elif name == "ndvi_records":
                return ndvi_mock
            return MagicMock()

        client.table.side_effect = table_router
        return client

    def test_returns_sst_when_available(self):
        client = self._make_query_client(sst_data=[{"sst_celsius": 28.5}])
        data = _fetch_latest_data_for_area(AREA_ID, client)
        assert data["sst"] == 28.5

    def test_returns_chl_a_when_available(self):
        client = self._make_query_client(chl_data=[{"chl_a_mg_m3": 2.1}])
        data = _fetch_latest_data_for_area(AREA_ID, client)
        assert data["chl_a"] == 2.1

    def test_returns_ndvi_when_available(self):
        client = self._make_query_client(ndvi_data=[{"ndvi_value": 0.65}])
        data = _fetch_latest_data_for_area(AREA_ID, client)
        assert data["ndvi"] == 0.65

    def test_returns_empty_when_no_data(self):
        client = self._make_query_client()
        data = _fetch_latest_data_for_area(AREA_ID, client)
        assert "sst" not in data
        assert "chl_a" not in data
        assert "ndvi" not in data

    def test_returns_empty_when_area_not_found(self):
        client = self._make_query_client(area_data=[])
        data = _fetch_latest_data_for_area(AREA_ID, client)
        assert data == {}

    def test_returns_all_available_data(self):
        client = self._make_query_client(
            sst_data=[{"sst_celsius": 29.0}],
            chl_data=[{"chl_a_mg_m3": 3.5}],
            ndvi_data=[{"ndvi_value": 0.7}],
        )
        data = _fetch_latest_data_for_area(AREA_ID, client)
        assert data["sst"] == 29.0
        assert data["chl_a"] == 3.5
        assert data["ndvi"] == 0.7


# ---------------------------------------------------------------------------
# run_daily_fsi_update
# ---------------------------------------------------------------------------


class TestRunDailyFsiUpdate:
    """Tests for the daily FSI update Lambda handler."""

    def _make_daily_client(
        self,
        areas: Optional[List[Dict]] = None,
        sst_val: Optional[float] = 28.5,
        chl_val: Optional[float] = 2.0,
        ndvi_val: Optional[float] = 0.6,
    ) -> MagicMock:
        """Build a mock client for the daily update flow."""
        client = MagicMock()

        if areas is None:
            areas = [
                {"id": "area-1", "name": "Mahachai", "region": "mahachai", "boundary": None},
            ]

        # Track insert calls
        fsi_insert_resp = MagicMock()
        fsi_insert_resp.data = [{"id": "fsi-new-id"}]

        scores_insert_resp = MagicMock()
        scores_insert_resp.data = [{"id": "scores-new-id"}]

        def make_chain(data):
            mock = MagicMock()
            mock.select.return_value = mock
            mock.eq.return_value = mock
            mock.order.return_value = mock
            mock.limit.return_value = mock
            resp = MagicMock()
            resp.data = data if data is not None else []
            mock.execute.return_value = resp
            mock.insert.return_value.execute.return_value = resp
            return mock

        areas_mock = make_chain(areas)
        area_detail_mock = make_chain([{"id": "area-1", "name": "Mahachai", "region": "mahachai"}])
        sst_mock = make_chain([{"sst_celsius": sst_val}] if sst_val is not None else [])
        chl_mock = make_chain([{"chl_a_mg_m3": chl_val}] if chl_val is not None else [])
        ndvi_mock = make_chain([{"ndvi_value": ndvi_val}] if ndvi_val is not None else [])

        fsi_table_mock = MagicMock()
        fsi_table_mock.insert.return_value.execute.return_value = fsi_insert_resp

        scores_table_mock = MagicMock()
        scores_table_mock.insert.return_value.execute.return_value = scores_insert_resp

        call_count = {"fishing_areas": 0}

        def table_router(name: str):
            if name == "fishing_areas":
                call_count["fishing_areas"] += 1
                if call_count["fishing_areas"] == 1:
                    return areas_mock  # First call: list all areas
                return area_detail_mock  # Subsequent: area detail lookup
            elif name == "sst_records":
                return sst_mock
            elif name == "chl_a_records":
                return chl_mock
            elif name == "ndvi_records":
                return ndvi_mock
            elif name == "fsi_results":
                return fsi_table_mock
            elif name == "fsi_component_scores":
                return scores_table_mock
            return MagicMock()

        client.table.side_effect = table_router
        return client

    @patch("lambda.fsi_engine.fsi_map.get_supabase_client")
    @patch("ephem.Moon")
    def test_processes_areas_successfully(self, mock_moon_cls, mock_get_client):
        mock_moon = MagicMock()
        mock_moon.phase = 25.0  # 25% illuminated
        mock_moon_cls.return_value = mock_moon

        client = self._make_daily_client()
        mock_get_client.return_value = client

        result = run_daily_fsi_update(event={}, context=None)

        assert result["status"] == "completed"
        assert result["areas_processed"] == 1
        assert len(result["fsi_map"]) == 1
        assert result["errors"] == []

    @patch("lambda.fsi_engine.fsi_map.get_supabase_client")
    @patch("ephem.Moon")
    def test_no_areas_returns_no_areas_status(self, mock_moon_cls, mock_get_client):
        mock_moon = MagicMock()
        mock_moon.phase = 50.0
        mock_moon_cls.return_value = mock_moon

        client = self._make_daily_client(areas=[])
        mock_get_client.return_value = client

        result = run_daily_fsi_update(event={}, context=None)

        assert result["status"] == "no_areas"
        assert result["areas_processed"] == 0
        assert result["fsi_map"] == []

    @patch("lambda.fsi_engine.fsi_map.get_supabase_client")
    @patch("ephem.Moon")
    def test_handles_area_with_no_data(self, mock_moon_cls, mock_get_client):
        """When an area has no environmental data at all, it should be
        recorded as an error (ValueError from calculate_fsi)."""
        mock_moon = MagicMock()
        mock_moon.phase = 50.0
        mock_moon_cls.return_value = mock_moon

        # Client returns areas but no environmental data, and also
        # the lunar_phase will still be provided via ephem, plus season.
        # So calculate_fsi will still get lunar_phase and season — it won't
        # raise ValueError. Let's verify it processes successfully.
        client = self._make_daily_client(sst_val=None, chl_val=None, ndvi_val=None)
        mock_get_client.return_value = client

        result = run_daily_fsi_update(event={}, context=None)

        # Even with no SST/Chl-a/NDVI, lunar_phase and season are always
        # available, so FSI should still be computed (graceful degradation).
        assert result["status"] == "completed"
        assert result["areas_processed"] == 1

    @patch("lambda.fsi_engine.fsi_map.get_supabase_client")
    @patch("ephem.Moon")
    def test_fsi_map_contains_zone_classification(self, mock_moon_cls, mock_get_client):
        mock_moon = MagicMock()
        mock_moon.phase = 0.0  # New moon → high lunar score
        mock_moon_cls.return_value = mock_moon

        client = self._make_daily_client(sst_val=28.5, chl_val=2.0, ndvi_val=0.8)
        mock_get_client.return_value = client

        result = run_daily_fsi_update(event={}, context=None)

        assert len(result["fsi_map"]) == 1
        entry = result["fsi_map"][0]
        assert entry["zone"] in ("green", "yellow", "red")
        assert 0.0 <= entry["fsi_value"] <= 1.0

    @patch("lambda.fsi_engine.fsi_map.get_supabase_client")
    @patch("ephem.Moon")
    def test_multiple_areas_processed(self, mock_moon_cls, mock_get_client):
        mock_moon = MagicMock()
        mock_moon.phase = 50.0
        mock_moon_cls.return_value = mock_moon

        areas = [
            {"id": "area-1", "name": "Mahachai", "region": "mahachai", "boundary": None},
            {"id": "area-2", "name": "Ranong", "region": "ranong", "boundary": None},
        ]
        client = self._make_daily_client(areas=areas)
        mock_get_client.return_value = client

        result = run_daily_fsi_update(event={}, context=None)

        assert result["status"] == "completed"
        assert result["areas_processed"] == 2
        assert len(result["fsi_map"]) == 2


# ---------------------------------------------------------------------------
# Integration-style: zone classification through the full pipeline
# ---------------------------------------------------------------------------


class TestZoneClassificationIntegration:
    """Verify zone classification is correct when FSI results flow
    through store and map generation."""

    def test_green_zone_through_pipeline(self):
        """Optimal inputs → green zone in FSI Map."""
        result = calculate_fsi(
            location=LOCATION,
            sst=28.5,
            chl_a=2.0,
            depth=20.0,
            lunar_phase=0.0,
            ndvi=1.0,
            season=SEASON_DRY,
            calculated_at=NOW,
        )
        fsi_map = generate_fsi_map([("area-1", result)])

        assert result.fsi_value > 0.7
        assert fsi_map[0]["zone"] == "green"

    def test_yellow_zone_through_pipeline(self):
        """Moderate inputs → yellow zone in FSI Map."""
        result = calculate_fsi(
            location=LOCATION,
            sst=22.0,  # below optimal → score 0.5
            chl_a=2.0,
            depth=20.0,
            lunar_phase=0.8,  # near full moon → low score
            ndvi=-0.4,  # low NDVI → score 0.3
            season=SEASON_DRY,
            calculated_at=NOW,
        )
        fsi_map = generate_fsi_map([("area-1", result)])

        assert 0.4 <= result.fsi_value <= 0.7
        assert fsi_map[0]["zone"] == "yellow"

    def test_red_zone_through_pipeline(self):
        """Poor inputs → red zone in FSI Map."""
        season_monsoon = SeasonData(season="monsoon", month=7, is_monsoon=True)
        result = calculate_fsi(
            location=LOCATION,
            sst=5.0,
            chl_a=0.0,
            depth=0.0,
            lunar_phase=1.0,
            ndvi=-1.0,
            season=season_monsoon,
            calculated_at=NOW,
        )
        fsi_map = generate_fsi_map([("area-1", result)])

        assert result.fsi_value < 0.4
        assert fsi_map[0]["zone"] == "red"

    def test_store_and_map_preserve_zone(self):
        """Zone classification is preserved through store + map generation."""
        result = _make_fsi_result(fsi_value=0.55, zone=FSIZone.YELLOW)
        client = _make_mock_client()

        # Store
        ids = store_fsi_result(result, AREA_ID, client=client)
        assert ids["fsi_result_id"] is not None

        # Map
        fsi_map = generate_fsi_map([(AREA_ID, result)])
        assert fsi_map[0]["zone"] == "yellow"
        assert fsi_map[0]["fsi_value"] == 0.55
