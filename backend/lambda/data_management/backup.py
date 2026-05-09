"""
Data Management — Daily Automated Backup

Exports key database tables to AWS S3 as JSON files for disaster recovery.
Triggered daily via EventBridge.

Requirements: 10.3
"""

from __future__ import annotations

import importlib as _il
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_config = _il.import_module("lambda.shared.config")
AWS_REGION = _config.AWS_REGION

# Tables to back up daily
BACKUP_TABLES: List[str] = [
    "users",
    "fishing_areas",
    "ndvi_records",
    "sst_records",
    "chl_a_records",
    "fsi_results",
    "fsi_component_scores",
    "yield_predictions",
    "mangrove_alerts",
    "restoration_sites",
    "carbon_reports",
    "catch_reports",
    "delivery_logs",
    "satellite_raw_data",
]

# Default S3 bucket (overridable via env)
import os

BACKUP_BUCKET = os.environ.get("BACKUP_S3_BUCKET", "sirinapha-backups")


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------


@dataclass
class BackupResult:
    """Outcome of a single table backup."""

    table_name: str
    success: bool
    record_count: int = 0
    s3_key: str = ""
    error: Optional[str] = None


@dataclass
class DailyBackupSummary:
    """Summary of a complete daily backup run."""

    backup_id: str
    timestamp: str
    total_tables: int
    successful: int
    failed: int
    results: List[BackupResult]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def generate_s3_key(table_name: str, timestamp: datetime) -> str:
    """Generate a structured S3 key for a table backup.

    Format: ``backups/YYYY/MM/DD/table_name_YYYYMMDD_HHMMSS.json``
    """
    date_prefix = timestamp.strftime("%Y/%m/%d")
    file_suffix = timestamp.strftime("%Y%m%d_%H%M%S")
    return f"backups/{date_prefix}/{table_name}_{file_suffix}.json"


def fetch_table_data(
    table_name: str,
    supabase_client: Any = None,
) -> List[Dict[str, Any]]:
    """Fetch all rows from a Supabase table.

    Parameters
    ----------
    table_name:
        Name of the table to export.
    supabase_client:
        Supabase client instance.  If ``None``, creates one via the
        shared client factory.

    Returns
    -------
    list[dict]
        Rows from the table as dictionaries.
    """
    if supabase_client is None:
        _sc = _il.import_module("lambda.shared.supabase_client")
        supabase_client = _sc.get_supabase_client()

    response = supabase_client.table(table_name).select("*").execute()
    return response.data if response.data else []


def upload_to_s3(
    data: List[Dict[str, Any]],
    bucket: str,
    key: str,
    s3_client: Any = None,
) -> None:
    """Upload JSON data to S3.

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
    )


# ---------------------------------------------------------------------------
# Core backup logic
# ---------------------------------------------------------------------------


def backup_table(
    table_name: str,
    timestamp: datetime,
    bucket: str = BACKUP_BUCKET,
    supabase_client: Any = None,
    s3_client: Any = None,
) -> BackupResult:
    """Back up a single table to S3.

    Parameters
    ----------
    table_name:
        Database table to export.
    timestamp:
        Backup timestamp (used for S3 key generation).
    bucket:
        Target S3 bucket.
    supabase_client:
        Optional Supabase client (for testing).
    s3_client:
        Optional S3 client (for testing).

    Returns
    -------
    BackupResult
    """
    s3_key = generate_s3_key(table_name, timestamp)

    try:
        rows = fetch_table_data(table_name, supabase_client=supabase_client)
        upload_to_s3(rows, bucket, s3_key, s3_client=s3_client)

        logger.info(
            "Backed up table=%s rows=%d to s3://%s/%s",
            table_name,
            len(rows),
            bucket,
            s3_key,
        )
        return BackupResult(
            table_name=table_name,
            success=True,
            record_count=len(rows),
            s3_key=s3_key,
        )

    except Exception as exc:
        logger.error("Failed to back up table=%s: %s", table_name, exc)
        return BackupResult(
            table_name=table_name,
            success=False,
            error=str(exc),
        )


def create_daily_backup(
    tables: Optional[List[str]] = None,
    bucket: str = BACKUP_BUCKET,
    supabase_client: Any = None,
    s3_client: Any = None,
    now: Optional[datetime] = None,
) -> DailyBackupSummary:
    """Run a full daily backup of all configured tables.

    Parameters
    ----------
    tables:
        List of table names to back up.  Defaults to :data:`BACKUP_TABLES`.
    bucket:
        Target S3 bucket.
    supabase_client:
        Optional Supabase client (for testing).
    s3_client:
        Optional S3 client (for testing).
    now:
        Override current timestamp (for testing).

    Returns
    -------
    DailyBackupSummary
    """
    if tables is None:
        tables = BACKUP_TABLES

    timestamp = now or datetime.now(timezone.utc)
    backup_id = str(uuid.uuid4())

    logger.info(
        "Starting daily backup %s at %s for %d tables",
        backup_id,
        timestamp.isoformat(),
        len(tables),
    )

    results: List[BackupResult] = []
    for table_name in tables:
        result = backup_table(
            table_name,
            timestamp,
            bucket=bucket,
            supabase_client=supabase_client,
            s3_client=s3_client,
        )
        results.append(result)

    successful = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)

    summary = DailyBackupSummary(
        backup_id=backup_id,
        timestamp=timestamp.isoformat(),
        total_tables=len(tables),
        successful=successful,
        failed=failed,
        results=results,
    )

    logger.info(
        "Daily backup %s complete: %d/%d tables succeeded",
        backup_id,
        successful,
        len(tables),
    )

    return summary


# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------


def handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """AWS Lambda entry point for daily backup.

    Triggered by EventBridge on a daily schedule.
    """
    try:
        summary = create_daily_backup()

        return {
            "statusCode": 200,
            "body": {
                "message": "Daily backup completed",
                "backup_id": summary.backup_id,
                "timestamp": summary.timestamp,
                "total_tables": summary.total_tables,
                "successful": summary.successful,
                "failed": summary.failed,
            },
        }

    except Exception as exc:
        logger.exception("Unexpected error during daily backup")
        return {
            "statusCode": 500,
            "body": {"error": f"Backup failed: {exc}"},
        }
