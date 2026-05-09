"""
Data Management — Cold Storage Migration (Archiver)

Moves aged data from Supabase PostgreSQL (hot storage) to AWS S3 Glacier
(cold storage) based on the data retention policy:

- Raw satellite data older than 1 year  → S3 Glacier
- Processed data (ndvi_records, fsi_results, etc.) older than 5 years → S3 Glacier

Triggered daily via EventBridge.

Requirements: 10.3, 10.5
"""

from __future__ import annotations

import importlib as _il
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_config = _il.import_module("lambda.shared.config")
AWS_REGION = _config.AWS_REGION

# S3 bucket for cold storage (Glacier)
ARCHIVE_BUCKET = os.environ.get("ARCHIVE_S3_BUCKET", "sirinapha-glacier-archive")

# Glacier storage class for archived objects
GLACIER_STORAGE_CLASS = "GLACIER"

# Retention thresholds (in days)
RAW_DATA_CUTOFF_DAYS = 365       # 1 year for raw satellite data
PROCESSED_DATA_CUTOFF_DAYS = 1825  # 5 years for processed data

# Tables and their timestamp columns + cutoff policies
RAW_DATA_TABLES: Dict[str, str] = {
    "satellite_raw_data": "fetched_at",
}

PROCESSED_DATA_TABLES: Dict[str, str] = {
    "ndvi_records": "observed_at",
    "fsi_results": "calculated_at",
    "fsi_component_scores": "calculated_at",
    "sst_records": "observed_at",
    "chl_a_records": "observed_at",
    "yield_predictions": "predicted_at",
    "mangrove_alerts": "detected_at",
    "carbon_reports": "generated_at",
}


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------


@dataclass
class ArchiveResult:
    """Outcome of archiving a single table."""

    table_name: str
    success: bool
    records_archived: int = 0
    records_deleted: int = 0
    s3_key: str = ""
    error: Optional[str] = None


@dataclass
class ArchiveSummary:
    """Summary of a complete archival run."""

    archive_id: str
    timestamp: str
    total_tables_processed: int
    total_records_archived: int
    total_records_deleted: int
    results: List[ArchiveResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Age classification
# ---------------------------------------------------------------------------


def classify_data_age(
    record_date: date,
    cutoff_days: int = PROCESSED_DATA_CUTOFF_DAYS,
    reference_date: Optional[date] = None,
) -> str:
    """Classify a record as ``"hot"`` or ``"cold"`` based on its age.

    Parameters
    ----------
    record_date:
        The date of the record (e.g. ``observed_at``, ``fetched_at``).
    cutoff_days:
        Number of days after which data is considered cold.
        Defaults to 1825 (5 years).
    reference_date:
        The reference "today" date.  Defaults to ``date.today()``.

    Returns
    -------
    str
        ``"hot"`` if the record is within the cutoff, ``"cold"`` otherwise.
    """
    if reference_date is None:
        reference_date = date.today()

    age_days = (reference_date - record_date).days
    return "cold" if age_days > cutoff_days else "hot"


# ---------------------------------------------------------------------------
# S3 Glacier helpers
# ---------------------------------------------------------------------------


def generate_archive_key(table_name: str, timestamp: datetime) -> str:
    """Generate a structured S3 key for archived data.

    Format: ``archive/table_name/YYYY/MM/table_name_YYYYMMDD_HHMMSS.json``
    """
    date_prefix = timestamp.strftime("%Y/%m")
    file_suffix = timestamp.strftime("%Y%m%d_%H%M%S")
    return f"archive/{table_name}/{date_prefix}/{table_name}_{file_suffix}.json"


def upload_to_glacier(
    data: List[Dict[str, Any]],
    bucket: str,
    key: str,
    s3_client: Any = None,
) -> None:
    """Upload JSON data to S3 with Glacier storage class.

    Parameters
    ----------
    data:
        List of row dicts to serialise as JSON.
    bucket:
        S3 bucket name.
    key:
        S3 object key.
    s3_client:
        boto3 S3 client.  If ``None``, creates one.
    """
    if s3_client is None:
        import boto3

        s3_client = boto3.client("s3", region_name=AWS_REGION)

    body = json.dumps(data, default=str, ensure_ascii=False)
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=body.encode("utf-8"),
        ContentType="application/json",
        StorageClass=GLACIER_STORAGE_CLASS,
    )


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------


def fetch_old_records(
    table_name: str,
    timestamp_column: str,
    cutoff_date: str,
    supabase_client: Any = None,
) -> List[Dict[str, Any]]:
    """Fetch records older than the cutoff date from a Supabase table.

    Parameters
    ----------
    table_name:
        Database table to query.
    timestamp_column:
        Column name containing the record timestamp.
    cutoff_date:
        ISO-format date string.  Records with ``timestamp_column < cutoff_date``
        are returned.
    supabase_client:
        Supabase client instance.

    Returns
    -------
    list[dict]
        Matching rows.
    """
    if supabase_client is None:
        _sc = _il.import_module("lambda.shared.supabase_client")
        supabase_client = _sc.get_supabase_client()

    response = (
        supabase_client.table(table_name)
        .select("*")
        .lt(timestamp_column, cutoff_date)
        .execute()
    )
    return response.data if response.data else []


def delete_old_records(
    table_name: str,
    timestamp_column: str,
    cutoff_date: str,
    supabase_client: Any = None,
) -> int:
    """Delete records older than the cutoff date from a Supabase table.

    Parameters
    ----------
    table_name:
        Database table to delete from.
    timestamp_column:
        Column name containing the record timestamp.
    cutoff_date:
        ISO-format date string.  Records with ``timestamp_column < cutoff_date``
        are deleted.
    supabase_client:
        Supabase client instance.

    Returns
    -------
    int
        Number of records deleted.
    """
    if supabase_client is None:
        _sc = _il.import_module("lambda.shared.supabase_client")
        supabase_client = _sc.get_supabase_client()

    response = (
        supabase_client.table(table_name)
        .delete()
        .lt(timestamp_column, cutoff_date)
        .execute()
    )
    return len(response.data) if response.data else 0


# ---------------------------------------------------------------------------
# Core archival logic
# ---------------------------------------------------------------------------


def archive_table(
    table_name: str,
    timestamp_column: str,
    cutoff_days: int,
    archive_timestamp: datetime,
    bucket: str = ARCHIVE_BUCKET,
    supabase_client: Any = None,
    s3_client: Any = None,
    reference_date: Optional[date] = None,
) -> ArchiveResult:
    """Archive old records from a single table to S3 Glacier.

    1. Query records older than ``cutoff_days``.
    2. Upload them to S3 Glacier.
    3. Delete the archived records from the database.

    Parameters
    ----------
    table_name:
        Database table to archive.
    timestamp_column:
        Column containing the record timestamp.
    cutoff_days:
        Age threshold in days.
    archive_timestamp:
        Timestamp for the archive run (used in S3 key).
    bucket:
        Target S3 bucket.
    supabase_client:
        Optional Supabase client (for testing).
    s3_client:
        Optional S3 client (for testing).
    reference_date:
        Override "today" for cutoff calculation (for testing).

    Returns
    -------
    ArchiveResult
    """
    ref = reference_date or date.today()
    cutoff_date = (ref - timedelta(days=cutoff_days)).isoformat()
    s3_key = generate_archive_key(table_name, archive_timestamp)

    try:
        # 1. Fetch old records
        old_records = fetch_old_records(
            table_name,
            timestamp_column,
            cutoff_date,
            supabase_client=supabase_client,
        )

        if not old_records:
            logger.info(
                "No records to archive for table=%s (cutoff=%s)",
                table_name,
                cutoff_date,
            )
            return ArchiveResult(
                table_name=table_name,
                success=True,
                records_archived=0,
                records_deleted=0,
            )

        # 2. Upload to S3 Glacier
        upload_to_glacier(
            old_records,
            bucket,
            s3_key,
            s3_client=s3_client,
        )

        # 3. Delete archived records from database
        deleted_count = delete_old_records(
            table_name,
            timestamp_column,
            cutoff_date,
            supabase_client=supabase_client,
        )

        logger.info(
            "Archived table=%s: %d records → s3://%s/%s, deleted %d",
            table_name,
            len(old_records),
            bucket,
            s3_key,
            deleted_count,
        )

        return ArchiveResult(
            table_name=table_name,
            success=True,
            records_archived=len(old_records),
            records_deleted=deleted_count,
            s3_key=s3_key,
        )

    except Exception as exc:
        logger.error("Failed to archive table=%s: %s", table_name, exc)
        return ArchiveResult(
            table_name=table_name,
            success=False,
            error=str(exc),
        )


def archive_old_satellite_data(
    cutoff_days: int = RAW_DATA_CUTOFF_DAYS,
    bucket: str = ARCHIVE_BUCKET,
    supabase_client: Any = None,
    s3_client: Any = None,
    now: Optional[datetime] = None,
    reference_date: Optional[date] = None,
) -> List[ArchiveResult]:
    """Move raw satellite data older than ``cutoff_days`` to S3 Glacier.

    Default cutoff is 365 days (1 year).

    Parameters
    ----------
    cutoff_days:
        Age threshold in days.  Defaults to 365.
    bucket:
        Target S3 bucket.
    supabase_client:
        Optional Supabase client (for testing).
    s3_client:
        Optional S3 client (for testing).
    now:
        Override current timestamp (for testing).
    reference_date:
        Override "today" for cutoff calculation (for testing).

    Returns
    -------
    list[ArchiveResult]
    """
    timestamp = now or datetime.now(timezone.utc)
    results: List[ArchiveResult] = []

    for table_name, ts_col in RAW_DATA_TABLES.items():
        result = archive_table(
            table_name=table_name,
            timestamp_column=ts_col,
            cutoff_days=cutoff_days,
            archive_timestamp=timestamp,
            bucket=bucket,
            supabase_client=supabase_client,
            s3_client=s3_client,
            reference_date=reference_date,
        )
        results.append(result)

    return results


def archive_old_processed_data(
    cutoff_days: int = PROCESSED_DATA_CUTOFF_DAYS,
    bucket: str = ARCHIVE_BUCKET,
    supabase_client: Any = None,
    s3_client: Any = None,
    now: Optional[datetime] = None,
    reference_date: Optional[date] = None,
) -> List[ArchiveResult]:
    """Move processed data older than ``cutoff_days`` to S3 Glacier.

    Default cutoff is 1825 days (5 years).

    Parameters
    ----------
    cutoff_days:
        Age threshold in days.  Defaults to 1825.
    bucket:
        Target S3 bucket.
    supabase_client:
        Optional Supabase client (for testing).
    s3_client:
        Optional S3 client (for testing).
    now:
        Override current timestamp (for testing).
    reference_date:
        Override "today" for cutoff calculation (for testing).

    Returns
    -------
    list[ArchiveResult]
    """
    timestamp = now or datetime.now(timezone.utc)
    results: List[ArchiveResult] = []

    for table_name, ts_col in PROCESSED_DATA_TABLES.items():
        result = archive_table(
            table_name=table_name,
            timestamp_column=ts_col,
            cutoff_days=cutoff_days,
            archive_timestamp=timestamp,
            bucket=bucket,
            supabase_client=supabase_client,
            s3_client=s3_client,
            reference_date=reference_date,
        )
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------


def handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """AWS Lambda entry point for cold storage migration.

    Triggered by EventBridge on a daily schedule.  Archives both raw
    satellite data (>1 year) and processed data (>5 years).
    """
    try:
        timestamp = datetime.now(timezone.utc)
        archive_id = str(uuid.uuid4())

        logger.info("Starting archival run %s at %s", archive_id, timestamp.isoformat())

        # Archive raw satellite data (>1 year)
        raw_results = archive_old_satellite_data(now=timestamp)

        # Archive processed data (>5 years)
        processed_results = archive_old_processed_data(now=timestamp)

        all_results = raw_results + processed_results
        total_archived = sum(r.records_archived for r in all_results)
        total_deleted = sum(r.records_deleted for r in all_results)

        summary = ArchiveSummary(
            archive_id=archive_id,
            timestamp=timestamp.isoformat(),
            total_tables_processed=len(all_results),
            total_records_archived=total_archived,
            total_records_deleted=total_deleted,
            results=all_results,
        )

        logger.info(
            "Archival run %s complete: %d tables, %d records archived, %d deleted",
            archive_id,
            summary.total_tables_processed,
            total_archived,
            total_deleted,
        )

        return {
            "statusCode": 200,
            "body": {
                "message": "Archival completed",
                "archive_id": summary.archive_id,
                "timestamp": summary.timestamp,
                "total_tables_processed": summary.total_tables_processed,
                "total_records_archived": summary.total_records_archived,
                "total_records_deleted": summary.total_records_deleted,
            },
        }

    except Exception as exc:
        logger.exception("Unexpected error during archival")
        return {
            "statusCode": 500,
            "body": {"error": f"Archival failed: {exc}"},
        }
