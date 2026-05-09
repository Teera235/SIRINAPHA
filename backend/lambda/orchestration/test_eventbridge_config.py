"""
Tests for EventBridge schedule configuration.

Validates that all schedule definitions are well-formed, have unique names,
correct dependency references, and proper execution ordering.

Requirements: 1.1, 1.2, 1.3, 3.8
"""

from __future__ import annotations

import importlib as _il

_mod = _il.import_module("lambda.orchestration.eventbridge_config")
ScheduleConfig = _mod.ScheduleConfig
ALL_SCHEDULES = _mod.ALL_SCHEDULES
DATA_PIPELINE_SCHEDULE = _mod.DATA_PIPELINE_SCHEDULE
SENTINEL2_NDVI_SCHEDULE = _mod.SENTINEL2_NDVI_SCHEDULE
FSI_ENGINE_SCHEDULE = _mod.FSI_ENGINE_SCHEDULE
MANGROVE_MONITOR_SCHEDULE = _mod.MANGROVE_MONITOR_SCHEDULE
YIELD_PREDICTOR_SCHEDULE = _mod.YIELD_PREDICTOR_SCHEDULE
DELIVERY_SYSTEM_SCHEDULE = _mod.DELIVERY_SYSTEM_SCHEDULE
DAILY_BACKUP_SCHEDULE = _mod.DAILY_BACKUP_SCHEDULE
COLD_STORAGE_ARCHIVER_SCHEDULE = _mod.COLD_STORAGE_ARCHIVER_SCHEDULE
get_schedule_by_name = _mod.get_schedule_by_name
get_schedules_by_component = _mod.get_schedules_by_component
get_execution_order = _mod.get_execution_order
validate_schedules = _mod.validate_schedules


# ---------------------------------------------------------------------------
# Schedule validation
# ---------------------------------------------------------------------------


class TestScheduleValidation:
    """All schedule configurations pass validation."""

    def test_validate_schedules_returns_no_issues(self) -> None:
        issues = validate_schedules()
        assert issues == [], f"Validation issues found: {issues}"

    def test_all_schedule_names_are_unique(self) -> None:
        names = [s.name for s in ALL_SCHEDULES]
        assert len(names) == len(set(names))

    def test_all_schedules_have_non_empty_expression(self) -> None:
        for s in ALL_SCHEDULES:
            assert s.schedule_expression.strip(), f"{s.name} has empty expression"

    def test_all_schedules_have_non_empty_lambda_name(self) -> None:
        for s in ALL_SCHEDULES:
            assert s.lambda_function_name.strip(), f"{s.name} has empty lambda name"

    def test_all_schedules_have_project_tag(self) -> None:
        for s in ALL_SCHEDULES:
            assert s.tags.get("Project") == "SIRINAPHA", (
                f"{s.name} missing Project tag"
            )

    def test_total_schedule_count(self) -> None:
        assert len(ALL_SCHEDULES) == 8


# ---------------------------------------------------------------------------
# Individual schedule definitions
# ---------------------------------------------------------------------------


class TestDataPipelineSchedule:
    """Data Pipeline runs daily at 06:00 ICT (23:00 UTC)."""

    def test_schedule_expression_is_daily_cron(self) -> None:
        assert "cron" in DATA_PIPELINE_SCHEDULE.schedule_expression

    def test_runs_at_23_utc(self) -> None:
        # cron(0 23 * * ? *) = 23:00 UTC = 06:00 ICT
        assert "23" in DATA_PIPELINE_SCHEDULE.schedule_expression

    def test_fetches_sst_and_chl_a(self) -> None:
        sources = DATA_PIPELINE_SCHEDULE.input_payload.get("sources", [])
        assert "noaa_oisst" in sources
        assert "nasa_modis" in sources

    def test_component_tag(self) -> None:
        assert DATA_PIPELINE_SCHEDULE.tags["Component"] == "DataPipeline"


class TestSentinel2Schedule:
    """Sentinel-2 NDVI fetch runs every 5 days."""

    def test_schedule_expression_is_rate_5_days(self) -> None:
        assert SENTINEL2_NDVI_SCHEDULE.schedule_expression == "rate(5 days)"

    def test_source_is_sentinel2(self) -> None:
        assert SENTINEL2_NDVI_SCHEDULE.input_payload.get("source") == "sentinel2_ndvi"


class TestFSIEngineSchedule:
    """FSI Engine runs daily after Data Pipeline."""

    def test_depends_on_data_pipeline(self) -> None:
        assert DATA_PIPELINE_SCHEDULE.name in FSI_ENGINE_SCHEDULE.depends_on

    def test_runs_at_00_utc(self) -> None:
        # cron(0 0 * * ? *) = 00:00 UTC = 07:00 ICT
        assert "cron(0 0" in FSI_ENGINE_SCHEDULE.schedule_expression

    def test_component_tag(self) -> None:
        assert FSI_ENGINE_SCHEDULE.tags["Component"] == "FSIEngine"


class TestMangroveMonitorSchedule:
    """Mangrove Monitor runs daily after Data Pipeline."""

    def test_depends_on_data_pipeline(self) -> None:
        assert DATA_PIPELINE_SCHEDULE.name in MANGROVE_MONITOR_SCHEDULE.depends_on

    def test_runs_at_00_15_utc(self) -> None:
        # cron(15 0 * * ? *) = 00:15 UTC = 07:15 ICT
        assert "cron(15 0" in MANGROVE_MONITOR_SCHEDULE.schedule_expression


class TestYieldPredictorSchedule:
    """Yield Predictor runs daily."""

    def test_schedule_expression_is_cron(self) -> None:
        assert "cron" in YIELD_PREDICTOR_SCHEDULE.schedule_expression

    def test_runs_at_00_30_utc(self) -> None:
        # cron(30 0 * * ? *) = 00:30 UTC = 07:30 ICT
        assert "cron(30 0" in YIELD_PREDICTOR_SCHEDULE.schedule_expression


class TestDeliverySystemSchedule:
    """Delivery System runs daily after FSI Engine."""

    def test_depends_on_fsi_engine(self) -> None:
        assert FSI_ENGINE_SCHEDULE.name in DELIVERY_SYSTEM_SCHEDULE.depends_on

    def test_runs_at_01_utc(self) -> None:
        # cron(0 1 * * ? *) = 01:00 UTC = 08:00 ICT
        assert "cron(0 1" in DELIVERY_SYSTEM_SCHEDULE.schedule_expression

    def test_message_type_is_daily_fsi(self) -> None:
        assert DELIVERY_SYSTEM_SCHEDULE.input_payload.get("message_type") == "daily_fsi"


class TestDailyBackupSchedule:
    """Daily backup runs at 02:00 ICT."""

    def test_runs_at_19_utc(self) -> None:
        # cron(0 19 * * ? *) = 19:00 UTC = 02:00 ICT
        assert "cron(0 19" in DAILY_BACKUP_SCHEDULE.schedule_expression


class TestColdStorageArchiverSchedule:
    """Cold storage archiver runs after daily backup."""

    def test_depends_on_daily_backup(self) -> None:
        assert DAILY_BACKUP_SCHEDULE.name in COLD_STORAGE_ARCHIVER_SCHEDULE.depends_on


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------


class TestGetScheduleByName:
    """get_schedule_by_name returns the correct schedule or None."""

    def test_existing_schedule(self) -> None:
        result = get_schedule_by_name("sirinapha-data-pipeline-daily")
        assert result is DATA_PIPELINE_SCHEDULE

    def test_nonexistent_schedule(self) -> None:
        result = get_schedule_by_name("does-not-exist")
        assert result is None


class TestGetSchedulesByComponent:
    """get_schedules_by_component filters by component tag."""

    def test_data_pipeline_component(self) -> None:
        results = get_schedules_by_component("DataPipeline")
        names = {s.name for s in results}
        assert DATA_PIPELINE_SCHEDULE.name in names
        assert SENTINEL2_NDVI_SCHEDULE.name in names

    def test_data_management_component(self) -> None:
        results = get_schedules_by_component("DataManagement")
        names = {s.name for s in results}
        assert DAILY_BACKUP_SCHEDULE.name in names
        assert COLD_STORAGE_ARCHIVER_SCHEDULE.name in names

    def test_unknown_component_returns_empty(self) -> None:
        results = get_schedules_by_component("NonExistent")
        assert results == []


# ---------------------------------------------------------------------------
# Execution order
# ---------------------------------------------------------------------------


class TestGetExecutionOrder:
    """get_execution_order returns a dependency-aware ordering."""

    def test_returns_all_schedules(self) -> None:
        ordered = get_execution_order()
        assert len(ordered) == len(ALL_SCHEDULES)

    def test_data_pipeline_before_fsi_engine(self) -> None:
        ordered = get_execution_order()
        names = [s.name for s in ordered]
        dp_idx = names.index(DATA_PIPELINE_SCHEDULE.name)
        fsi_idx = names.index(FSI_ENGINE_SCHEDULE.name)
        assert dp_idx < fsi_idx

    def test_data_pipeline_before_mangrove_monitor(self) -> None:
        ordered = get_execution_order()
        names = [s.name for s in ordered]
        dp_idx = names.index(DATA_PIPELINE_SCHEDULE.name)
        mm_idx = names.index(MANGROVE_MONITOR_SCHEDULE.name)
        assert dp_idx < mm_idx

    def test_fsi_engine_before_delivery_system(self) -> None:
        ordered = get_execution_order()
        names = [s.name for s in ordered]
        fsi_idx = names.index(FSI_ENGINE_SCHEDULE.name)
        ds_idx = names.index(DELIVERY_SYSTEM_SCHEDULE.name)
        assert fsi_idx < ds_idx

    def test_backup_before_archiver(self) -> None:
        ordered = get_execution_order()
        names = [s.name for s in ordered]
        bk_idx = names.index(DAILY_BACKUP_SCHEDULE.name)
        ar_idx = names.index(COLD_STORAGE_ARCHIVER_SCHEDULE.name)
        assert bk_idx < ar_idx
