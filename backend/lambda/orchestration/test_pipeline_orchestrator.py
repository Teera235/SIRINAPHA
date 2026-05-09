"""
Tests for the daily pipeline orchestrator.

Validates the end-to-end pipeline flow, step execution, error handling,
dependency-based skipping, and event-driven wiring (mangrove alerts,
catch report feedback).

Requirements: 3.8, 6.2, 6.4, 6.7
"""

from __future__ import annotations

import importlib as _il

_mod = _il.import_module("lambda.orchestration.pipeline_orchestrator")
StepStatus = _mod.StepStatus
StepResult = _mod.StepResult
PipelineResult = _mod.PipelineResult
PipelineStep = _mod.PipelineStep
DAILY_PIPELINE_STEPS = _mod.DAILY_PIPELINE_STEPS
execute_step = _mod.execute_step
run_daily_pipeline = _mod.run_daily_pipeline
handle_mangrove_alert_delivery = _mod.handle_mangrove_alert_delivery
handle_catch_report_feedback = _mod.handle_catch_report_feedback
handler = _mod.handler

# Reference to the module object for patching
_po = _mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_step(
    name: str = "test_step",
    handler_fn=None,
    depends_on=None,
    is_critical: bool = False,
) -> PipelineStep:
    """Create a PipelineStep with a local handler for testing."""
    return PipelineStep(
        name=name,
        lambda_function_name=f"sirinapha-{name}",
        payload={"test": True},
        handler=handler_fn,
        depends_on=depends_on or [],
        is_critical=is_critical,
    )


def _success_handler(payload):
    return {"statusCode": 200, "body": {"message": "ok"}}


def _failure_handler(payload):
    raise RuntimeError("Simulated failure")


# ---------------------------------------------------------------------------
# Pipeline step definitions
# ---------------------------------------------------------------------------


class TestDailyPipelineSteps:
    """The default pipeline steps are correctly defined."""

    def test_step_count(self) -> None:
        assert len(DAILY_PIPELINE_STEPS) == 5

    def test_step_names(self) -> None:
        names = [s.name for s in DAILY_PIPELINE_STEPS]
        assert names == [
            "data_pipeline",
            "fsi_engine",
            "mangrove_monitor",
            "yield_predictor",
            "delivery_system",
        ]

    def test_data_pipeline_is_critical(self) -> None:
        dp = DAILY_PIPELINE_STEPS[0]
        assert dp.is_critical is True

    def test_fsi_engine_depends_on_data_pipeline(self) -> None:
        fsi = DAILY_PIPELINE_STEPS[1]
        assert "data_pipeline" in fsi.depends_on

    def test_delivery_depends_on_fsi_engine(self) -> None:
        delivery = DAILY_PIPELINE_STEPS[4]
        assert "fsi_engine" in delivery.depends_on

    def test_mangrove_monitor_depends_on_data_pipeline(self) -> None:
        mm = DAILY_PIPELINE_STEPS[2]
        assert "data_pipeline" in mm.depends_on


# ---------------------------------------------------------------------------
# Single step execution
# ---------------------------------------------------------------------------


class TestExecuteStep:
    """execute_step runs a handler and returns a StepResult."""

    def test_successful_step(self) -> None:
        step = _make_step(handler_fn=_success_handler)
        result = execute_step(step)

        assert result.status == StepStatus.SUCCESS
        assert result.error is None
        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.duration_seconds is not None
        assert result.duration_seconds >= 0

    def test_failed_step(self) -> None:
        step = _make_step(handler_fn=_failure_handler)
        result = execute_step(step)

        assert result.status == StepStatus.FAILED
        assert "Simulated failure" in result.error
        assert result.started_at is not None
        assert result.completed_at is not None

    def test_step_name_preserved(self) -> None:
        step = _make_step(name="my_step", handler_fn=_success_handler)
        result = execute_step(step)
        assert result.step_name == "my_step"

    def test_output_captured_on_success(self) -> None:
        step = _make_step(handler_fn=_success_handler)
        result = execute_step(step)
        assert result.output is not None
        assert "statusCode" in result.output


# ---------------------------------------------------------------------------
# Full pipeline execution
# ---------------------------------------------------------------------------


class TestRunDailyPipeline:
    """run_daily_pipeline orchestrates steps with dependency handling."""

    def test_all_steps_succeed(self) -> None:
        steps = [
            _make_step("step_a", handler_fn=_success_handler, is_critical=True),
            _make_step("step_b", handler_fn=_success_handler, depends_on=["step_a"]),
        ]
        result = run_daily_pipeline(steps=steps, pipeline_id="test-001")

        assert result.pipeline_id == "test-001"
        assert result.total_steps == 2
        assert result.successful_steps == 2
        assert result.failed_steps == 0
        assert result.skipped_steps == 0
        assert result.all_succeeded is True

    def test_non_critical_failure_does_not_block(self) -> None:
        steps = [
            _make_step("step_a", handler_fn=_failure_handler, is_critical=False),
            _make_step("step_b", handler_fn=_success_handler),
        ]
        result = run_daily_pipeline(steps=steps, pipeline_id="test-002")

        assert result.total_steps == 2
        assert result.failed_steps == 1
        assert result.successful_steps == 1
        assert result.skipped_steps == 0

    def test_critical_failure_skips_dependents(self) -> None:
        steps = [
            _make_step("step_a", handler_fn=_failure_handler, is_critical=True),
            _make_step("step_b", handler_fn=_success_handler, depends_on=["step_a"]),
            _make_step("step_c", handler_fn=_success_handler),
        ]
        result = run_daily_pipeline(steps=steps, pipeline_id="test-003")

        assert result.total_steps == 3
        assert result.failed_steps == 1
        assert result.skipped_steps == 1
        assert result.successful_steps == 1

        # step_b should be skipped
        step_b = result.steps[1]
        assert step_b.step_name == "step_b"
        assert step_b.status == StepStatus.SKIPPED
        assert "step_a" in step_b.error

        # step_c should succeed (no dependency on step_a)
        step_c = result.steps[2]
        assert step_c.step_name == "step_c"
        assert step_c.status == StepStatus.SUCCESS

    def test_all_succeeded_false_on_failure(self) -> None:
        steps = [
            _make_step("step_a", handler_fn=_failure_handler, is_critical=False),
        ]
        result = run_daily_pipeline(steps=steps)
        assert result.all_succeeded is False

    def test_all_succeeded_false_on_skip(self) -> None:
        steps = [
            _make_step("step_a", handler_fn=_failure_handler, is_critical=True),
            _make_step("step_b", handler_fn=_success_handler, depends_on=["step_a"]),
        ]
        result = run_daily_pipeline(steps=steps)
        assert result.all_succeeded is False

    def test_empty_pipeline(self) -> None:
        result = run_daily_pipeline(steps=[], pipeline_id="test-empty")
        assert result.total_steps == 0
        assert result.all_succeeded is True

    def test_pipeline_result_has_timestamps(self) -> None:
        steps = [_make_step("step_a", handler_fn=_success_handler)]
        result = run_daily_pipeline(steps=steps)
        assert result.started_at is not None
        assert result.completed_at is not None

    def test_chained_dependency_skip(self) -> None:
        """If A fails (critical), B depends on A, C depends on B (critical),
        then B is skipped and C runs (since B didn't fail critically, it was skipped)."""
        steps = [
            _make_step("a", handler_fn=_failure_handler, is_critical=True),
            _make_step("b", handler_fn=_success_handler, depends_on=["a"], is_critical=True),
            _make_step("c", handler_fn=_success_handler, depends_on=["b"]),
        ]
        result = run_daily_pipeline(steps=steps)

        statuses = {s.step_name: s.status for s in result.steps}
        assert statuses["a"] == StepStatus.FAILED
        assert statuses["b"] == StepStatus.SKIPPED
        # c depends on b, but b was skipped (not failed critically),
        # so c should run
        assert statuses["c"] == StepStatus.SUCCESS


# ---------------------------------------------------------------------------
# Event-driven flows
# ---------------------------------------------------------------------------


class TestMangroveAlertDelivery:
    """handle_mangrove_alert_delivery wires alerts to Delivery System."""

    def test_successful_alert_delivery(self) -> None:
        import io
        import json as _json

        class MockLambdaClient:
            def invoke(self, **kwargs):
                payload = _json.dumps({"statusCode": 200}).encode()
                return {"Payload": io.BytesIO(payload)}

        result = handle_mangrove_alert_delivery(
            alert_payload={"alert_level": "critical", "area_id": "mahachai"},
            lambda_client=MockLambdaClient(),
        )
        assert result.status == StepStatus.SUCCESS
        assert result.step_name == "mangrove_alert_delivery"

    def test_failed_alert_delivery(self) -> None:
        class FailingLambdaClient:
            def invoke(self, **kwargs):
                raise RuntimeError("Lambda invocation failed")

        result = handle_mangrove_alert_delivery(
            alert_payload={"alert_level": "warning"},
            lambda_client=FailingLambdaClient(),
        )
        assert result.status == StepStatus.FAILED
        assert result.error is not None


class TestCatchReportFeedback:
    """handle_catch_report_feedback wires catch reports to Yield Predictor."""

    def test_successful_catch_report(self) -> None:
        import io
        import json as _json

        class MockLambdaClient:
            def invoke(self, **kwargs):
                payload = _json.dumps({"statusCode": 200}).encode()
                return {"Payload": io.BytesIO(payload)}

        result = handle_catch_report_feedback(
            catch_report_payload={
                "user_id": "fisher-001",
                "species_catch": [{"species": "กุ้ง", "kg": 15.0}],
            },
            lambda_client=MockLambdaClient(),
        )
        assert result.status == StepStatus.SUCCESS
        assert result.step_name == "catch_report_feedback"


# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------


class TestHandler:
    """Lambda handler dispatches based on trigger type."""

    def test_daily_pipeline_trigger(self) -> None:
        original_steps = _po.DAILY_PIPELINE_STEPS
        _po.DAILY_PIPELINE_STEPS = [
            _make_step("step_a", handler_fn=_success_handler),
        ]
        try:
            response = handler({"trigger": "daily_pipeline"})
            assert response["statusCode"] == 200
            assert "pipeline_id" in response["body"]
            assert response["body"]["total_steps"] == 1
            assert response["body"]["successful_steps"] == 1
        finally:
            _po.DAILY_PIPELINE_STEPS = original_steps

    def test_default_trigger_is_daily_pipeline(self) -> None:
        original_steps = _po.DAILY_PIPELINE_STEPS
        _po.DAILY_PIPELINE_STEPS = [
            _make_step("step_a", handler_fn=_success_handler),
        ]
        try:
            response = handler({})
            assert response["statusCode"] == 200
            assert "pipeline_id" in response["body"]
        finally:
            _po.DAILY_PIPELINE_STEPS = original_steps

    def test_mangrove_alert_trigger(self) -> None:
        original_invoke = _po.invoke_lambda

        def mock_invoke(fn, payload, lambda_client=None):
            return {"statusCode": 200}

        _po.invoke_lambda = mock_invoke
        try:
            response = handler({
                "trigger": "mangrove_alert",
                "alert": {"alert_level": "critical"},
            })
            assert response["statusCode"] == 200
            assert "Mangrove alert" in response["body"]["message"]
        finally:
            _po.invoke_lambda = original_invoke

    def test_catch_report_trigger(self) -> None:
        original_invoke = _po.invoke_lambda

        def mock_invoke(fn, payload, lambda_client=None):
            return {"statusCode": 200}

        _po.invoke_lambda = mock_invoke
        try:
            response = handler({
                "trigger": "catch_report",
                "catch_data": {"user_id": "fisher-001"},
            })
            assert response["statusCode"] == 200
            assert "Catch report" in response["body"]["message"]
        finally:
            _po.invoke_lambda = original_invoke

    def test_partial_failure_returns_207(self) -> None:
        original_steps = _po.DAILY_PIPELINE_STEPS
        _po.DAILY_PIPELINE_STEPS = [
            _make_step("step_a", handler_fn=_success_handler),
            _make_step("step_b", handler_fn=_failure_handler),
        ]
        try:
            response = handler({"trigger": "daily_pipeline"})
            assert response["statusCode"] == 207
            assert response["body"]["failed_steps"] == 1
        finally:
            _po.DAILY_PIPELINE_STEPS = original_steps
