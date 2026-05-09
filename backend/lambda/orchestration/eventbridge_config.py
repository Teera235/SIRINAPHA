"""
Orchestration — EventBridge Schedule Configuration

Defines the EventBridge schedule rules for all Lambda functions in the
SIRINAPHA Baan-Pla Link platform.  These configurations are consumed by
infrastructure-as-code tools (CDK, SAM, Terraform) to create the actual
AWS EventBridge Scheduler resources.

Schedule overview
-----------------
- **Data Pipeline** (SST + Chl-a): daily at 06:00 ICT (23:00 UTC)
- **Sentinel-2 NDVI fetch**: every 5 days at 06:30 ICT (23:30 UTC)
- **FSI Engine**: daily at 07:00 ICT (00:00 UTC+1), after Data Pipeline
- **Mangrove Monitor**: daily at 07:15 ICT (00:15 UTC+1), after Data Pipeline
- **Yield Predictor**: daily at 07:30 ICT (00:30 UTC+1)
- **Delivery System**: daily at 08:00 ICT (01:00 UTC+1), after FSI calculation
- **Daily Backup**: daily at 02:00 ICT (19:00 UTC)
- **Cold Storage Archiver**: daily at 03:00 ICT (20:00 UTC)

Requirements: 1.1, 1.2, 1.3, 3.8
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScheduleConfig:
    """Configuration for a single EventBridge schedule rule.

    Attributes
    ----------
    name:
        Unique rule name (used as the EventBridge rule identifier).
    description:
        Human-readable description of the schedule.
    schedule_expression:
        EventBridge schedule expression.  Either a ``cron()`` or ``rate()``
        expression.
    lambda_function_name:
        Logical name of the target Lambda function.
    input_payload:
        Optional JSON payload passed to the Lambda function on invocation.
    enabled:
        Whether the rule is active.
    retry_attempts:
        Number of retry attempts EventBridge should make on invocation
        failure (0–185).
    max_event_age_seconds:
        Maximum age of an event before EventBridge discards it.
    depends_on:
        List of schedule names that should complete before this one runs.
        This is advisory metadata — actual sequencing is handled by the
        pipeline orchestrator or Step Functions.
    tags:
        Key-value tags applied to the EventBridge rule.
    """

    name: str
    description: str
    schedule_expression: str
    lambda_function_name: str
    input_payload: Optional[Dict[str, Any]] = None
    enabled: bool = True
    retry_attempts: int = 2
    max_event_age_seconds: int = 3600
    depends_on: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# ICT timezone offset note
# ---------------------------------------------------------------------------
# ICT = UTC+7.  EventBridge cron expressions use UTC.
# 06:00 ICT = 23:00 UTC (previous day)
# 07:00 ICT = 00:00 UTC
# 08:00 ICT = 01:00 UTC
# ---------------------------------------------------------------------------

# Common tags applied to all rules
_COMMON_TAGS: Dict[str, str] = {
    "Project": "SIRINAPHA",
    "Module": "BaanPlaLink",
    "Environment": "production",
}


# ---------------------------------------------------------------------------
# Schedule Definitions
# ---------------------------------------------------------------------------


DATA_PIPELINE_SCHEDULE = ScheduleConfig(
    name="sirinapha-data-pipeline-daily",
    description="Daily SST + Chl-a data fetch at 06:00 ICT (23:00 UTC)",
    schedule_expression="cron(0 23 * * ? *)",
    lambda_function_name="sirinapha-data-pipeline",
    input_payload={"sources": ["noaa_oisst", "nasa_modis"]},
    tags={**_COMMON_TAGS, "Component": "DataPipeline"},
)

SENTINEL2_NDVI_SCHEDULE = ScheduleConfig(
    name="sirinapha-sentinel2-ndvi-fetch",
    description="Sentinel-2 NDVI fetch every 5 days at 06:30 ICT (23:30 UTC)",
    schedule_expression="rate(5 days)",
    lambda_function_name="sirinapha-sentinel2-ndvi",
    input_payload={"source": "sentinel2_ndvi"},
    tags={**_COMMON_TAGS, "Component": "DataPipeline"},
)

FSI_ENGINE_SCHEDULE = ScheduleConfig(
    name="sirinapha-fsi-engine-daily",
    description="Daily FSI calculation at 07:00 ICT (00:00 UTC), after Data Pipeline",
    schedule_expression="cron(0 0 * * ? *)",
    lambda_function_name="sirinapha-fsi-engine",
    input_payload={"trigger": "scheduled", "recalculate_all_areas": True},
    depends_on=["sirinapha-data-pipeline-daily"],
    tags={**_COMMON_TAGS, "Component": "FSIEngine"},
)

MANGROVE_MONITOR_SCHEDULE = ScheduleConfig(
    name="sirinapha-mangrove-monitor-daily",
    description="Daily mangrove health analysis at 07:15 ICT (00:15 UTC), after Data Pipeline",
    schedule_expression="cron(15 0 * * ? *)",
    lambda_function_name="sirinapha-mangrove-monitor",
    input_payload={"trigger": "scheduled", "run_change_detection": True},
    depends_on=["sirinapha-data-pipeline-daily"],
    tags={**_COMMON_TAGS, "Component": "MangroveMonitor"},
)

YIELD_PREDICTOR_SCHEDULE = ScheduleConfig(
    name="sirinapha-yield-predictor-daily",
    description="Daily yield prediction inference at 07:30 ICT (00:30 UTC)",
    schedule_expression="cron(30 0 * * ? *)",
    lambda_function_name="sirinapha-yield-predictor",
    input_payload={"trigger": "scheduled"},
    tags={**_COMMON_TAGS, "Component": "YieldPredictor"},
)

DELIVERY_SYSTEM_SCHEDULE = ScheduleConfig(
    name="sirinapha-delivery-system-daily",
    description="Daily FSI summary push at 08:00 ICT (01:00 UTC), after FSI calculation",
    schedule_expression="cron(0 1 * * ? *)",
    lambda_function_name="sirinapha-delivery-system",
    input_payload={"trigger": "scheduled", "message_type": "daily_fsi"},
    depends_on=["sirinapha-fsi-engine-daily"],
    tags={**_COMMON_TAGS, "Component": "DeliverySystem"},
)

DAILY_BACKUP_SCHEDULE = ScheduleConfig(
    name="sirinapha-daily-backup",
    description="Daily automated backup at 02:00 ICT (19:00 UTC)",
    schedule_expression="cron(0 19 * * ? *)",
    lambda_function_name="sirinapha-daily-backup",
    tags={**_COMMON_TAGS, "Component": "DataManagement"},
)

COLD_STORAGE_ARCHIVER_SCHEDULE = ScheduleConfig(
    name="sirinapha-cold-storage-archiver",
    description="Daily cold storage migration at 03:00 ICT (20:00 UTC)",
    schedule_expression="cron(0 20 * * ? *)",
    lambda_function_name="sirinapha-cold-storage-archiver",
    depends_on=["sirinapha-daily-backup"],
    tags={**_COMMON_TAGS, "Component": "DataManagement"},
)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


ALL_SCHEDULES: List[ScheduleConfig] = [
    DATA_PIPELINE_SCHEDULE,
    SENTINEL2_NDVI_SCHEDULE,
    FSI_ENGINE_SCHEDULE,
    MANGROVE_MONITOR_SCHEDULE,
    YIELD_PREDICTOR_SCHEDULE,
    DELIVERY_SYSTEM_SCHEDULE,
    DAILY_BACKUP_SCHEDULE,
    COLD_STORAGE_ARCHIVER_SCHEDULE,
]
"""All EventBridge schedule configurations for the platform."""


def get_schedule_by_name(name: str) -> Optional[ScheduleConfig]:
    """Look up a schedule configuration by its rule name.

    Returns ``None`` if no schedule with the given name exists.
    """
    for schedule in ALL_SCHEDULES:
        if schedule.name == name:
            return schedule
    return None


def get_schedules_by_component(component: str) -> List[ScheduleConfig]:
    """Return all schedules tagged with the given component name.

    Parameters
    ----------
    component:
        Component tag value (e.g. ``"DataPipeline"``, ``"FSIEngine"``).

    Returns
    -------
    list[ScheduleConfig]
        Matching schedules (may be empty).
    """
    return [
        s for s in ALL_SCHEDULES
        if s.tags.get("Component") == component
    ]


def get_execution_order() -> List[ScheduleConfig]:
    """Return schedules in dependency-aware execution order.

    Schedules with no dependencies come first, followed by those that
    depend on earlier schedules.  This is a simple topological sort
    suitable for the linear daily pipeline.

    Returns
    -------
    list[ScheduleConfig]
        Schedules ordered so that dependencies are satisfied.
    """
    name_to_schedule = {s.name: s for s in ALL_SCHEDULES}
    visited: set[str] = set()
    ordered: List[ScheduleConfig] = []

    def _visit(name: str) -> None:
        if name in visited:
            return
        schedule = name_to_schedule.get(name)
        if schedule is None:
            return
        for dep in schedule.depends_on:
            _visit(dep)
        visited.add(name)
        ordered.append(schedule)

    for s in ALL_SCHEDULES:
        _visit(s.name)

    return ordered


def validate_schedules() -> List[str]:
    """Validate all schedule configurations and return a list of issues.

    Checks performed:
    - Unique rule names
    - Non-empty schedule expressions
    - Dependencies reference existing schedules
    - No circular dependencies (simple check)

    Returns
    -------
    list[str]
        List of validation error messages (empty if all valid).
    """
    issues: List[str] = []
    names = [s.name for s in ALL_SCHEDULES]

    # Check for duplicate names
    seen: set[str] = set()
    for name in names:
        if name in seen:
            issues.append(f"Duplicate schedule name: {name}")
        seen.add(name)

    for s in ALL_SCHEDULES:
        # Non-empty schedule expression
        if not s.schedule_expression.strip():
            issues.append(f"Schedule '{s.name}' has empty schedule_expression")

        # Non-empty lambda function name
        if not s.lambda_function_name.strip():
            issues.append(f"Schedule '{s.name}' has empty lambda_function_name")

        # Dependencies reference existing schedules
        for dep in s.depends_on:
            if dep not in seen:
                issues.append(
                    f"Schedule '{s.name}' depends on unknown schedule '{dep}'"
                )

        # Simple self-dependency check
        if s.name in s.depends_on:
            issues.append(f"Schedule '{s.name}' depends on itself")

    return issues
