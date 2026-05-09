"""
Unit tests for Yield Predictor — catch_ingestion module.

Covers:
  • Catch report validation (required fields, types, ranges)
  • Parsing raw data into CatchReport objects
  • Serialisation to database row format
  • Retraining data preparation
  • Lambda handler success and error paths

Requirements: 4.5
"""

from __future__ import annotations

import importlib
from datetime import date, datetime

import pytest

_ci = importlib.import_module("lambda.yield_predictor.catch_ingestion")
validate_catch_data = _ci.validate_catch_data
parse_catch_report = _ci.parse_catch_report
catch_report_to_row = _ci.catch_report_to_row
prepare_retraining_data = _ci.prepare_retraining_data
handler = _ci.handler
CatchIngestionError = _ci.CatchIngestionError
CatchReport = _ci.CatchReport
SpeciesCatch = _ci.SpeciesCatch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _valid_data(**overrides):
    """Return a valid catch report payload."""
    defaults = {
        "user_id": "user-001",
        "area_id": "mahachai-01",
        "species_catch": [
            {"species_name": "กุ้ง", "weight_kg": 15.0},
            {"species_name": "ปลาทู", "weight_kg": 8.5},
        ],
        "catch_date": "2024-06-15",
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# validate_catch_data
# ---------------------------------------------------------------------------


class TestValidateCatchData:
    def test_valid_data_passes(self):
        validate_catch_data(_valid_data())  # should not raise

    def test_missing_user_id(self):
        with pytest.raises(CatchIngestionError, match="user_id"):
            validate_catch_data(_valid_data(user_id=None))

    def test_missing_area_id(self):
        with pytest.raises(CatchIngestionError, match="area_id"):
            validate_catch_data(_valid_data(area_id=None))

    def test_missing_species_catch(self):
        with pytest.raises(CatchIngestionError, match="species_catch"):
            validate_catch_data(_valid_data(species_catch=None))

    def test_empty_species_catch(self):
        with pytest.raises(CatchIngestionError, match="non-empty"):
            validate_catch_data(_valid_data(species_catch=[]))

    def test_missing_catch_date(self):
        with pytest.raises(CatchIngestionError, match="catch_date"):
            validate_catch_data(_valid_data(catch_date=None))

    def test_species_catch_not_list(self):
        with pytest.raises(CatchIngestionError, match="non-empty"):
            validate_catch_data(_valid_data(species_catch="not a list"))

    def test_species_entry_not_dict(self):
        with pytest.raises(CatchIngestionError, match="must be a dict"):
            validate_catch_data(_valid_data(species_catch=["not a dict"]))

    def test_missing_species_name(self):
        with pytest.raises(CatchIngestionError, match="species_name"):
            validate_catch_data(_valid_data(
                species_catch=[{"weight_kg": 10.0}]
            ))

    def test_empty_species_name(self):
        with pytest.raises(CatchIngestionError, match="species_name"):
            validate_catch_data(_valid_data(
                species_catch=[{"species_name": "", "weight_kg": 10.0}]
            ))

    def test_missing_weight_kg(self):
        with pytest.raises(CatchIngestionError, match="weight_kg"):
            validate_catch_data(_valid_data(
                species_catch=[{"species_name": "กุ้ง"}]
            ))

    def test_negative_weight_kg(self):
        with pytest.raises(CatchIngestionError, match="non-negative"):
            validate_catch_data(_valid_data(
                species_catch=[{"species_name": "กุ้ง", "weight_kg": -5.0}]
            ))

    def test_weight_kg_string(self):
        with pytest.raises(CatchIngestionError, match="non-negative"):
            validate_catch_data(_valid_data(
                species_catch=[{"species_name": "กุ้ง", "weight_kg": "ten"}]
            ))


# ---------------------------------------------------------------------------
# parse_catch_report
# ---------------------------------------------------------------------------


class TestParseCatchReport:
    def test_parses_valid_data(self):
        report = parse_catch_report(_valid_data())
        assert isinstance(report, CatchReport)
        assert report.user_id == "user-001"
        assert report.area_id == "mahachai-01"
        assert len(report.species_catch) == 2
        assert report.total_kg == pytest.approx(23.5)
        assert report.catch_date == date(2024, 6, 15)

    def test_id_is_uuid(self):
        report = parse_catch_report(_valid_data())
        assert len(report.id) == 36  # UUID format

    def test_reported_at_is_set(self):
        report = parse_catch_report(_valid_data())
        assert isinstance(report.reported_at, datetime)

    def test_total_kg_sums_species(self):
        data = _valid_data(species_catch=[
            {"species_name": "กุ้ง", "weight_kg": 10.0},
            {"species_name": "ปลาทู", "weight_kg": 5.0},
            {"species_name": "หมึก", "weight_kg": 3.0},
        ])
        report = parse_catch_report(data)
        assert report.total_kg == pytest.approx(18.0)

    def test_catch_date_as_date_object(self):
        data = _valid_data(catch_date=date(2024, 1, 1))
        report = parse_catch_report(data)
        assert report.catch_date == date(2024, 1, 1)

    def test_invalid_date_format(self):
        with pytest.raises(CatchIngestionError, match="Invalid catch_date"):
            parse_catch_report(_valid_data(catch_date="not-a-date"))

    def test_invalid_date_type(self):
        with pytest.raises(CatchIngestionError, match="catch_date must be"):
            parse_catch_report(_valid_data(catch_date=12345))


# ---------------------------------------------------------------------------
# catch_report_to_row
# ---------------------------------------------------------------------------


class TestCatchReportToRow:
    def test_row_has_required_keys(self):
        report = parse_catch_report(_valid_data())
        row = catch_report_to_row(report)
        assert "id" in row
        assert "user_id" in row
        assert "area_id" in row
        assert "species_catch" in row
        assert "total_kg" in row
        assert "catch_date" in row
        assert "reported_at" in row

    def test_species_catch_serialised(self):
        report = parse_catch_report(_valid_data())
        row = catch_report_to_row(report)
        assert isinstance(row["species_catch"], list)
        assert row["species_catch"][0]["species_name"] == "กุ้ง"
        assert row["species_catch"][0]["weight_kg"] == 15.0

    def test_dates_are_iso_strings(self):
        report = parse_catch_report(_valid_data())
        row = catch_report_to_row(report)
        assert isinstance(row["catch_date"], str)
        assert isinstance(row["reported_at"], str)


# ---------------------------------------------------------------------------
# prepare_retraining_data
# ---------------------------------------------------------------------------


class TestPrepareRetrainingData:
    def test_flattens_species(self):
        report = parse_catch_report(_valid_data())
        records = prepare_retraining_data([report])
        # 2 species → 2 records
        assert len(records) == 2

    def test_record_fields(self):
        report = parse_catch_report(_valid_data())
        records = prepare_retraining_data([report])
        rec = records[0]
        assert "area_id" in rec
        assert "catch_date" in rec
        assert "species_name" in rec
        assert "weight_kg" in rec
        assert "total_kg" in rec

    def test_multiple_reports(self):
        r1 = parse_catch_report(_valid_data())
        r2 = parse_catch_report(_valid_data(
            user_id="user-002",
            species_catch=[{"species_name": "หมึก", "weight_kg": 5.0}],
        ))
        records = prepare_retraining_data([r1, r2])
        # r1 has 2 species, r2 has 1 → 3 records
        assert len(records) == 3

    def test_empty_reports(self):
        assert prepare_retraining_data([]) == []


# ---------------------------------------------------------------------------
# handler (Lambda entry point)
# ---------------------------------------------------------------------------


class TestHandler:
    def test_success_response(self):
        result = handler(_valid_data())
        assert result["statusCode"] == 200
        assert "report_id" in result["body"]
        assert result["body"]["total_kg"] == pytest.approx(23.5)

    def test_validation_error_returns_400(self):
        result = handler({"user_id": "u1"})  # missing fields
        assert result["statusCode"] == 400
        assert "error" in result["body"]

    def test_empty_event_returns_400(self):
        result = handler({})
        assert result["statusCode"] == 400
