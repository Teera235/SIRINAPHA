"""Unit tests for lambda/data_management/archiver.py."""

from __future__ import annotations

import importlib
import json
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock, call, patch

import pytest

_archiver = importlib.import_module("lambda.data_management.archiver")

GLACIER_STORAGE_CLASS = _archiver.GLACIER_STORAGE_CLASS
PROCESSED_DATA_CUTOFF_DAYS = _archiver.PROCESSED_DATA_CUTOFF_DAYS
PROCESSED_DATA_TABLES = _archiver.PROCESSED_DATA_TABLES
RAW_DATA_CUTOFF_DAYS = _archiver.RAW_DATA_CUTOFF_DAYS
RAW_DATA_TABLES = _archiver.RAW_DATA_TABLES
ArchiveResult = _archiver.ArchiveResult
ArchiveSummary = _archiver.ArchiveSummary
archive_old_processed_data = _archiver.archive_old_processed_data
archive_old_satellite_data = _archiver.archive_old_satellite_data
archive_table = _archiver.archive_table
classify_data_age = _archiver.classify_data_age
delete_old_records = _archiver.delete_old_records
fetch_old_records = _archiver.fetch_old_records
generate_archive_key = _archiver.generate_archive_key
handler = _archiver.handler
upload_to_glacier = _archiver.upload_to_glacier


# ---------------------------------------------------------------------------
# classify_data_age
# ---------------------------------------------------------------------------


class TestClassifyDataAge:
    def test_recent_data_is_hot(self):
        today = date(2024, 6, 1)
        record_date = date(2024, 5, 1)  # 31 days old
        assert classify_data_age(record_date, cutoff_days=365, reference_date=today) == "hot"

    def test_old_data_is_cold(self):
        today = date(2024, 6, 1)
        record_date = date(2022, 1, 1)  # ~2.5 years old
        assert classify_data_age(record_date, cutoff_days=365, reference_date=today) == "cold"

    def test_exactly_at_cutoff_is_hot(self):
        today = date(2024, 6, 1)
        record_date = today - timedelta(days=365)  # exactly 365 days
        assert classify_data_age(record_date, cutoff_days=365, reference_date=today) == "hot"

    def test_one_day_past_cutoff_is_cold(self):
        today = date(2024, 6, 1)
        record_date = today - timedelta(days=366)
        assert classify_data_age(record_date, cutoff_days=365, reference_date=today) == "cold"

    def test_five_year_cutoff_for_processed_data(self):
        today = date(2024, 6, 1)
        # 4 years old — still hot
        record_4y = today - timedelta(days=4 * 365)
        assert classify_data_age(record_4y, cutoff_days=1825, reference_date=today) == "hot"

        # 6 years old — cold
        record_6y = today - timedelta(days=6 * 365)
        assert classify_data_age(record_6y, cutoff_days=1825, reference_date=today) == "cold"

    def test_default_cutoff_is_five_years(self):
        today = date(2024, 6, 1)
        record_date = today - timedelta(days=1826)  # just past 5 years
        assert classify_data_age(record_date, reference_date=today) == "cold"

    def test_same_day_is_hot(self):
        today = date(2024, 6, 1)
        assert classify_data_age(today, cutoff_days=365, reference_date=today) == "hot"


# ---------------------------------------------------------------------------
# generate_archive_key
# ---------------------------------------------------------------------------


class TestGenerateArchiveKey:
    def test_key_format(self):
        ts = datetime(2024, 3, 15, 8, 30, 0, tzinfo=timezone.utc)
        key = generate_archive_key("satellite_raw_data", ts)
        assert key == "archive/satellite_raw_data/2024/03/satellite_raw_data_20240315_083000.json"

    def test_key_contains_table_name(self):
        ts = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        key = generate_archive_key("ndvi_records", ts)
        assert "ndvi_records" in key

    def test_key_ends_with_json(self):
        ts = datetime(2024, 6, 20, 12, 0, 0, tzinfo=timezone.utc)
        key = generate_archive_key("fsi_results", ts)
        assert key.endswith(".json")


# ---------------------------------------------------------------------------
# upload_to_glacier
# ---------------------------------------------------------------------------


class TestUploadToGlacier:
    def test_uploads_with_glacier_storage_class(self):
        mock_s3 = MagicMock()
        data = [{"id": "1", "value": 42}]

        upload_to_glacier(data, "archive-bucket", "archive/key.json", s3_client=mock_s3)

        mock_s3.put_object.assert_called_once()
        call_kwargs = mock_s3.put_object.call_args[1]
        assert call_kwargs["Bucket"] == "archive-bucket"
        assert call_kwargs["Key"] == "archive/key.json"
        assert call_kwargs["StorageClass"] == GLACIER_STORAGE_CLASS
        assert call_kwargs["ContentType"] == "application/json"

    def test_body_is_valid_json(self):
        mock_s3 = MagicMock()
        data = [{"name": "มหาชัย", "ndvi": 0.65}]

        upload_to_glacier(data, "bucket", "key.json", s3_client=mock_s3)

        body = mock_s3.put_object.call_args[1]["Body"].decode("utf-8")
        parsed = json.loads(body)
        assert parsed == data


# ---------------------------------------------------------------------------
# fetch_old_records
# ---------------------------------------------------------------------------


class TestFetchOldRecords:
    def test_returns_matching_records(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{"id": "old-1"}, {"id": "old-2"}]
        mock_client.table.return_value.select.return_value.lt.return_value.execute.return_value = (
            mock_response
        )

        rows = fetch_old_records(
            "satellite_raw_data",
            "fetched_at",
            "2023-06-01",
            supabase_client=mock_client,
        )

        assert len(rows) == 2
        mock_client.table.assert_called_once_with("satellite_raw_data")

    def test_returns_empty_when_no_old_records(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = None
        mock_client.table.return_value.select.return_value.lt.return_value.execute.return_value = (
            mock_response
        )

        rows = fetch_old_records(
            "ndvi_records",
            "observed_at",
            "2020-01-01",
            supabase_client=mock_client,
        )

        assert rows == []


# ---------------------------------------------------------------------------
# delete_old_records
# ---------------------------------------------------------------------------


class TestDeleteOldRecords:
    def test_returns_deleted_count(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
        mock_client.table.return_value.delete.return_value.lt.return_value.execute.return_value = (
            mock_response
        )

        count = delete_old_records(
            "satellite_raw_data",
            "fetched_at",
            "2023-06-01",
            supabase_client=mock_client,
        )

        assert count == 3

    def test_returns_zero_when_nothing_deleted(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = None
        mock_client.table.return_value.delete.return_value.lt.return_value.execute.return_value = (
            mock_response
        )

        count = delete_old_records(
            "ndvi_records",
            "observed_at",
            "2020-01-01",
            supabase_client=mock_client,
        )

        assert count == 0


# ---------------------------------------------------------------------------
# archive_table
# ---------------------------------------------------------------------------


class TestArchiveTable:
    def _make_mock_client(self, select_data=None, delete_data=None):
        """Build a mock Supabase client with configurable responses."""
        mock_client = MagicMock()

        # select chain
        select_resp = MagicMock()
        select_resp.data = select_data
        mock_client.table.return_value.select.return_value.lt.return_value.execute.return_value = (
            select_resp
        )

        # delete chain
        delete_resp = MagicMock()
        delete_resp.data = delete_data
        mock_client.table.return_value.delete.return_value.lt.return_value.execute.return_value = (
            delete_resp
        )

        return mock_client

    def test_archives_old_records(self):
        old_records = [{"id": "1"}, {"id": "2"}]
        mock_client = self._make_mock_client(
            select_data=old_records,
            delete_data=old_records,
        )
        mock_s3 = MagicMock()
        ts = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)

        result = archive_table(
            "satellite_raw_data",
            "fetched_at",
            cutoff_days=365,
            archive_timestamp=ts,
            supabase_client=mock_client,
            s3_client=mock_s3,
            reference_date=date(2024, 6, 1),
        )

        assert result.success is True
        assert result.records_archived == 2
        assert result.records_deleted == 2
        assert result.s3_key != ""
        mock_s3.put_object.assert_called_once()

    def test_no_records_to_archive(self):
        mock_client = self._make_mock_client(select_data=[], delete_data=None)
        mock_s3 = MagicMock()
        ts = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)

        result = archive_table(
            "ndvi_records",
            "observed_at",
            cutoff_days=1825,
            archive_timestamp=ts,
            supabase_client=mock_client,
            s3_client=mock_s3,
            reference_date=date(2024, 6, 1),
        )

        assert result.success is True
        assert result.records_archived == 0
        assert result.records_deleted == 0
        mock_s3.put_object.assert_not_called()

    def test_handles_fetch_error(self):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.lt.return_value.execute.side_effect = (
            Exception("DB timeout")
        )
        mock_s3 = MagicMock()
        ts = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)

        result = archive_table(
            "satellite_raw_data",
            "fetched_at",
            cutoff_days=365,
            archive_timestamp=ts,
            supabase_client=mock_client,
            s3_client=mock_s3,
        )

        assert result.success is False
        assert "DB timeout" in result.error


# ---------------------------------------------------------------------------
# archive_old_satellite_data
# ---------------------------------------------------------------------------


class TestArchiveOldSatelliteData:
    def test_processes_raw_data_tables(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.table.return_value.select.return_value.lt.return_value.execute.return_value = (
            mock_response
        )
        mock_s3 = MagicMock()
        ts = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)

        results = archive_old_satellite_data(
            supabase_client=mock_client,
            s3_client=mock_s3,
            now=ts,
        )

        assert len(results) == len(RAW_DATA_TABLES)
        for r in results:
            assert r.table_name in RAW_DATA_TABLES

    def test_uses_one_year_cutoff_by_default(self):
        """Verify the default cutoff is 365 days."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.table.return_value.select.return_value.lt.return_value.execute.return_value = (
            mock_response
        )
        mock_s3 = MagicMock()
        ref = date(2024, 6, 1)
        ts = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)

        results = archive_old_satellite_data(
            cutoff_days=RAW_DATA_CUTOFF_DAYS,
            supabase_client=mock_client,
            s3_client=mock_s3,
            now=ts,
            reference_date=ref,
        )

        # The lt() call should use a date ~1 year before ref
        expected_cutoff = (ref - timedelta(days=365)).isoformat()
        lt_call = mock_client.table.return_value.select.return_value.lt
        lt_call.assert_called_with("fetched_at", expected_cutoff)


# ---------------------------------------------------------------------------
# archive_old_processed_data
# ---------------------------------------------------------------------------


class TestArchiveOldProcessedData:
    def test_processes_all_processed_tables(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.table.return_value.select.return_value.lt.return_value.execute.return_value = (
            mock_response
        )
        mock_s3 = MagicMock()
        ts = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)

        results = archive_old_processed_data(
            supabase_client=mock_client,
            s3_client=mock_s3,
            now=ts,
        )

        assert len(results) == len(PROCESSED_DATA_TABLES)

    def test_uses_five_year_cutoff_by_default(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.table.return_value.select.return_value.lt.return_value.execute.return_value = (
            mock_response
        )
        mock_s3 = MagicMock()
        ref = date(2024, 6, 1)
        ts = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)

        archive_old_processed_data(
            cutoff_days=PROCESSED_DATA_CUTOFF_DAYS,
            supabase_client=mock_client,
            s3_client=mock_s3,
            now=ts,
            reference_date=ref,
        )

        expected_cutoff = (ref - timedelta(days=1825)).isoformat()
        lt_call = mock_client.table.return_value.select.return_value.lt
        # Should have been called for each processed table
        assert lt_call.call_count == len(PROCESSED_DATA_TABLES)


# ---------------------------------------------------------------------------
# handler
# ---------------------------------------------------------------------------


class TestHandler:
    def test_success_response(self):
        mock_raw = [
            ArchiveResult(
                table_name="satellite_raw_data",
                success=True,
                records_archived=10,
                records_deleted=10,
            )
        ]
        mock_processed = [
            ArchiveResult(
                table_name="ndvi_records",
                success=True,
                records_archived=5,
                records_deleted=5,
            )
        ]

        with patch.object(_archiver, "archive_old_satellite_data", return_value=mock_raw), \
             patch.object(_archiver, "archive_old_processed_data", return_value=mock_processed):
            response = handler({})

        assert response["statusCode"] == 200
        assert response["body"]["total_records_archived"] == 15
        assert response["body"]["total_records_deleted"] == 15

    def test_error_response(self):
        with patch.object(
            _archiver,
            "archive_old_satellite_data",
            side_effect=RuntimeError("S3 unavailable"),
        ):
            response = handler({})

        assert response["statusCode"] == 500
        assert "error" in response["body"]


# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_raw_data_cutoff_is_one_year(self):
        assert RAW_DATA_CUTOFF_DAYS == 365

    def test_processed_data_cutoff_is_five_years(self):
        assert PROCESSED_DATA_CUTOFF_DAYS == 1825

    def test_glacier_storage_class(self):
        assert GLACIER_STORAGE_CLASS == "GLACIER"

    def test_raw_data_tables_include_satellite(self):
        assert "satellite_raw_data" in RAW_DATA_TABLES

    def test_processed_tables_include_key_tables(self):
        assert "ndvi_records" in PROCESSED_DATA_TABLES
        assert "fsi_results" in PROCESSED_DATA_TABLES
