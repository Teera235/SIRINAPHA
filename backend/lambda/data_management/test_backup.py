"""Unit tests for lambda/data_management/backup.py."""

from __future__ import annotations

import importlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

_backup = importlib.import_module("lambda.data_management.backup")

BACKUP_TABLES = _backup.BACKUP_TABLES
BackupResult = _backup.BackupResult
DailyBackupSummary = _backup.DailyBackupSummary
backup_table = _backup.backup_table
create_daily_backup = _backup.create_daily_backup
fetch_table_data = _backup.fetch_table_data
generate_s3_key = _backup.generate_s3_key
handler = _backup.handler
upload_to_s3 = _backup.upload_to_s3


# ---------------------------------------------------------------------------
# generate_s3_key
# ---------------------------------------------------------------------------


class TestGenerateS3Key:
    def test_key_format(self):
        ts = datetime(2024, 3, 15, 8, 30, 0, tzinfo=timezone.utc)
        key = generate_s3_key("ndvi_records", ts)
        assert key == "backups/2024/03/15/ndvi_records_20240315_083000.json"

    def test_key_contains_table_name(self):
        ts = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        key = generate_s3_key("fsi_results", ts)
        assert "fsi_results" in key

    def test_key_ends_with_json(self):
        ts = datetime(2024, 6, 20, 12, 0, 0, tzinfo=timezone.utc)
        key = generate_s3_key("users", ts)
        assert key.endswith(".json")


# ---------------------------------------------------------------------------
# fetch_table_data
# ---------------------------------------------------------------------------


class TestFetchTableData:
    def test_returns_rows(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{"id": "1", "name": "test"}]
        mock_client.table.return_value.select.return_value.execute.return_value = (
            mock_response
        )

        rows = fetch_table_data("users", supabase_client=mock_client)
        assert rows == [{"id": "1", "name": "test"}]
        mock_client.table.assert_called_once_with("users")

    def test_returns_empty_list_when_no_data(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = None
        mock_client.table.return_value.select.return_value.execute.return_value = (
            mock_response
        )

        rows = fetch_table_data("users", supabase_client=mock_client)
        assert rows == []


# ---------------------------------------------------------------------------
# upload_to_s3
# ---------------------------------------------------------------------------


class TestUploadToS3:
    def test_uploads_json(self):
        mock_s3 = MagicMock()
        data = [{"id": "1", "value": 42}]

        upload_to_s3(data, "my-bucket", "path/file.json", s3_client=mock_s3)

        mock_s3.put_object.assert_called_once()
        call_kwargs = mock_s3.put_object.call_args[1]
        assert call_kwargs["Bucket"] == "my-bucket"
        assert call_kwargs["Key"] == "path/file.json"
        assert call_kwargs["ContentType"] == "application/json"

        # Verify the body is valid JSON
        body = call_kwargs["Body"].decode("utf-8")
        parsed = json.loads(body)
        assert parsed == data

    def test_handles_unicode(self):
        mock_s3 = MagicMock()
        data = [{"name": "มหาชัย"}]

        upload_to_s3(data, "bucket", "key.json", s3_client=mock_s3)

        body = mock_s3.put_object.call_args[1]["Body"].decode("utf-8")
        assert "มหาชัย" in body


# ---------------------------------------------------------------------------
# backup_table
# ---------------------------------------------------------------------------


class TestBackupTable:
    def test_successful_backup(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{"id": "1"}, {"id": "2"}]
        mock_client.table.return_value.select.return_value.execute.return_value = (
            mock_response
        )
        mock_s3 = MagicMock()
        ts = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)

        result = backup_table(
            "ndvi_records",
            ts,
            bucket="test-bucket",
            supabase_client=mock_client,
            s3_client=mock_s3,
        )

        assert result.success is True
        assert result.table_name == "ndvi_records"
        assert result.record_count == 2
        assert result.s3_key != ""
        assert result.error is None

    def test_failed_backup_returns_error(self):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.execute.side_effect = (
            Exception("Connection refused")
        )
        mock_s3 = MagicMock()
        ts = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)

        result = backup_table(
            "ndvi_records",
            ts,
            supabase_client=mock_client,
            s3_client=mock_s3,
        )

        assert result.success is False
        assert "Connection refused" in result.error
        assert result.record_count == 0


# ---------------------------------------------------------------------------
# create_daily_backup
# ---------------------------------------------------------------------------


class TestCreateDailyBackup:
    def test_backs_up_all_tables(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{"id": "1"}]
        mock_client.table.return_value.select.return_value.execute.return_value = (
            mock_response
        )
        mock_s3 = MagicMock()
        ts = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)

        summary = create_daily_backup(
            tables=["users", "fsi_results"],
            supabase_client=mock_client,
            s3_client=mock_s3,
            now=ts,
        )

        assert isinstance(summary, DailyBackupSummary)
        assert summary.total_tables == 2
        assert summary.successful == 2
        assert summary.failed == 0
        assert len(summary.results) == 2

    def test_counts_failures(self):
        mock_client = MagicMock()
        # First table succeeds, second fails
        mock_response_ok = MagicMock()
        mock_response_ok.data = [{"id": "1"}]

        call_count = 0

        def side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_response_ok
            raise Exception("DB error")

        mock_client.table.return_value.select.return_value.execute = side_effect
        mock_s3 = MagicMock()
        ts = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)

        summary = create_daily_backup(
            tables=["users", "fsi_results"],
            supabase_client=mock_client,
            s3_client=mock_s3,
            now=ts,
        )

        assert summary.total_tables == 2
        assert summary.successful == 1
        assert summary.failed == 1

    def test_defaults_to_backup_tables(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.table.return_value.select.return_value.execute.return_value = (
            mock_response
        )
        mock_s3 = MagicMock()
        ts = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)

        summary = create_daily_backup(
            supabase_client=mock_client,
            s3_client=mock_s3,
            now=ts,
        )

        assert summary.total_tables == len(BACKUP_TABLES)

    def test_backup_id_is_set(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.table.return_value.select.return_value.execute.return_value = (
            mock_response
        )
        mock_s3 = MagicMock()
        ts = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)

        summary = create_daily_backup(
            tables=["users"],
            supabase_client=mock_client,
            s3_client=mock_s3,
            now=ts,
        )

        assert summary.backup_id  # non-empty UUID string
        assert summary.timestamp == ts.isoformat()


# ---------------------------------------------------------------------------
# handler
# ---------------------------------------------------------------------------


class TestHandler:
    def test_success_response(self):
        mock_summary = DailyBackupSummary(
            backup_id="test-id",
            timestamp="2024-06-01T10:00:00+00:00",
            total_tables=2,
            successful=2,
            failed=0,
            results=[],
        )

        with patch.object(_backup, "create_daily_backup", return_value=mock_summary):
            response = handler({})

        assert response["statusCode"] == 200
        assert response["body"]["successful"] == 2
        assert response["body"]["failed"] == 0

    def test_error_response(self):
        with patch.object(
            _backup, "create_daily_backup", side_effect=RuntimeError("Unexpected failure")
        ):
            response = handler({})

        assert response["statusCode"] == 500
        assert "error" in response["body"]
