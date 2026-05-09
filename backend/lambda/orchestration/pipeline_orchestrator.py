"""
Orchestration — Daily Pipeline Orchestrator

Lambda handler that orchestrates the daily end-to-end pipeline flow:

    Data Pipeline → FSI Engine → Mangrove Monitor → Yield Predictor → Delivery System

Each step invokes the corresponding Lambda function (or calls the module
directly in a monolith deployment).  Errors at any step are caught and
logged so that remaining steps can still execute.

Wiring overview
---------------
- **Data Pipeline** fetches SST + Chl-a → stores in DB
- **FSI Engine** reads latest data → calculates FSI → stores results
- **Mangrove Monitor** analyses NDVI → generates alerts if thresholds breached
- **Yield Predictor** runs inference on latest environmental data
- **Delivery System** pushes daily FSI summaries + any mangrove alerts

Additional event-driven flows (wired via EventBridge / webhooks):
- LINE webhook → catch report → Yield Predictor feedback loop
- Mangrove Monitor alerts → Delivery System alert notifications

Requirements: 3.8, 6.2, 6.4, 6.7
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-1")


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------


class StepStatus(str, Enum):
    """Execution status of a pipeline step."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    """Outcome of a single pipeline step."""

    step_name: str
    status: StepStatus
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class PipelineResult:
    """Summary of a complete pipeline execution."""

    pipeline_id: str
    started_at: str
    completed_at: Optional[str] = None
    total_steps: int = 0
    successful_steps: int = 0
    failed_steps: int = 0
    skipped_steps: int = 0
    steps: List[StepResult] = field(default_factory=list)

    @property
    def all_succeeded(self) -> bool:
        """Return ``True`` if every step succeeded."""
        return self.failed_steps == 0 and self.skipped_steps == 0


# ---------------------------------------------------------------------------
# Pipeline Step Definitions
# ---------------------------------------------------------------------------


@dataclass
class PipelineStep:
    """Definition of a single step in the daily pipeline.

    Attributes
    ----------
    name:
        Human-readable step name.
    lambda_function_name:
        Name of the Lambda function to invoke (used in AWS mode).
    payload:
        JSON payload to pass to the Lambda function.
    handler:
        Optional callable for direct invocation (used in local/test mode).
    depends_on:
        Steps that must succeed before this step runs.
    is_critical:
        If ``True``, failure of this step prevents dependent steps from
        running.  If ``False``, the pipeline continues regardless.
    """

    name: str
    lambda_function_name: str
    payload: Dict[str, Any] = field(default_factory=dict)
    handler: Optional[Callable[..., Dict[str, Any]]] = None
    depends_on: List[str] = field(default_factory=list)
    is_critical: bool = False


# The daily pipeline steps in execution order.
DAILY_PIPELINE_STEPS: List[PipelineStep] = [
    PipelineStep(
        name="data_pipeline",
        lambda_function_name="sirinapha-data-pipeline",
        payload={"sources": ["noaa_oisst", "nasa_modis"]},
        is_critical=True,
    ),
    PipelineStep(
        name="fsi_engine",
        lambda_function_name="sirinapha-fsi-engine",
        payload={"trigger": "orchestrator", "recalculate_all_areas": True},
        depends_on=["data_pipeline"],
        is_critical=True,
    ),
    PipelineStep(
        name="mangrove_monitor",
        lambda_function_name="sirinapha-mangrove-monitor",
        payload={"trigger": "orchestrator", "run_change_detection": True},
        depends_on=["data_pipeline"],
        is_critical=False,
    ),
    PipelineStep(
        name="yield_predictor",
        lambda_function_name="sirinapha-yield-predictor",
        payload={"trigger": "orchestrator"},
        is_critical=False,
    ),
    PipelineStep(
        name="delivery_system",
        lambda_function_name="sirinapha-delivery-system",
        payload={"trigger": "orchestrator", "message_type": "daily_fsi"},
        depends_on=["fsi_engine"],
        is_critical=False,
    ),
]


# ---------------------------------------------------------------------------
# Lambda invocation helper
# ---------------------------------------------------------------------------


def invoke_lambda(
    function_name: str,
    payload: Dict[str, Any],
    lambda_client: Any = None,
) -> Dict[str, Any]:
    """Invoke an AWS Lambda function synchronously.

    Parameters
    ----------
    function_name:
        Name or ARN of the Lambda function.
    payload:
        JSON-serialisable payload.
    lambda_client:
        boto3 Lambda client.  If ``None``, creates one.

    Returns
    -------
    dict
        Parsed response payload from the Lambda function.

    Raises
    ------
    RuntimeError
        If the invocation returns a ``FunctionError``.
    """
    if lambda_client is None:
        import boto3

        lambda_client = boto3.client("lambda", region_name=AWS_REGION)

    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload).encode("utf-8"),
    )

    response_payload = json.loads(response["Payload"].read())

    if "FunctionError" in response:
        raise RuntimeError(
            f"Lambda {function_name} returned error: "
            f"{response_payload.get('errorMessage', 'Unknown error')}"
        )

    return response_payload


# ---------------------------------------------------------------------------
# Step execution
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def execute_step(
    step: PipelineStep,
    lambda_client: Any = None,
) -> StepResult:
    """Execute a single pipeline step.

    If the step has a ``handler`` callable, it is invoked directly.
    Otherwise the corresponding Lambda function is invoked via
    :func:`invoke_lambda`.

    Parameters
    ----------
    step:
        The pipeline step to execute.
    lambda_client:
        Optional boto3 Lambda client (for testing).

    Returns
    -------
    StepResult
    """
    started_at = _now_iso()
    start_ts = datetime.now(timezone.utc)

    logger.info("Starting step '%s' (lambda=%s)", step.name, step.lambda_function_name)

    try:
        if step.handler is not None:
            output = step.handler(step.payload)
        else:
            output = invoke_lambda(
                step.lambda_function_name,
                step.payload,
                lambda_client=lambda_client,
            )

        end_ts = datetime.now(timezone.utc)
        duration = (end_ts - start_ts).total_seconds()

        logger.info(
            "Step '%s' completed successfully in %.1fs",
            step.name,
            duration,
        )

        return StepResult(
            step_name=step.name,
            status=StepStatus.SUCCESS,
            started_at=started_at,
            completed_at=_now_iso(),
            duration_seconds=duration,
            output=output if isinstance(output, dict) else {"result": str(output)},
        )

    except Exception as exc:
        end_ts = datetime.now(timezone.utc)
        duration = (end_ts - start_ts).total_seconds()

        logger.error(
            "Step '%s' failed after %.1fs: %s",
            step.name,
            duration,
            exc,
        )

        return StepResult(
            step_name=step.name,
            status=StepStatus.FAILED,
            started_at=started_at,
            completed_at=_now_iso(),
            duration_seconds=duration,
            error=str(exc),
        )


# ---------------------------------------------------------------------------
# Pipeline orchestration
# ---------------------------------------------------------------------------


def run_daily_pipeline(
    steps: Optional[List[PipelineStep]] = None,
    lambda_client: Any = None,
    pipeline_id: Optional[str] = None,
) -> PipelineResult:
    """Execute the full daily pipeline in dependency order.

    Each step is executed sequentially.  If a *critical* step fails, any
    step that depends on it is skipped.  Non-critical failures are logged
    but do not block downstream steps.

    Parameters
    ----------
    steps:
        Pipeline steps to execute.  Defaults to :data:`DAILY_PIPELINE_STEPS`.
    lambda_client:
        Optional boto3 Lambda client (for testing).
    pipeline_id:
        Override pipeline run ID (for testing).

    Returns
    -------
    PipelineResult
    """
    if steps is None:
        steps = DAILY_PIPELINE_STEPS

    pid = pipeline_id or str(uuid.uuid4())
    started_at = _now_iso()

    logger.info("Starting daily pipeline %s with %d steps", pid, len(steps))

    step_results: Dict[str, StepResult] = {}
    failed_critical: set[str] = set()

    for step in steps:
        # Check if any dependency failed critically
        blocked_by = [
            dep for dep in step.depends_on
            if dep in failed_critical
        ]

        if blocked_by:
            logger.warning(
                "Skipping step '%s' — blocked by failed critical step(s): %s",
                step.name,
                ", ".join(blocked_by),
            )
            result = StepResult(
                step_name=step.name,
                status=StepStatus.SKIPPED,
                error=f"Blocked by failed critical step(s): {', '.join(blocked_by)}",
            )
        else:
            result = execute_step(step, lambda_client=lambda_client)

        step_results[step.name] = result

        # Track critical failures
        if result.status == StepStatus.FAILED and step.is_critical:
            failed_critical.add(step.name)

    # Build summary
    all_results = list(step_results.values())
    successful = sum(1 for r in all_results if r.status == StepStatus.SUCCESS)
    failed = sum(1 for r in all_results if r.status == StepStatus.FAILED)
    skipped = sum(1 for r in all_results if r.status == StepStatus.SKIPPED)

    pipeline_result = PipelineResult(
        pipeline_id=pid,
        started_at=started_at,
        completed_at=_now_iso(),
        total_steps=len(all_results),
        successful_steps=successful,
        failed_steps=failed,
        skipped_steps=skipped,
        steps=all_results,
    )

    logger.info(
        "Daily pipeline %s complete: %d/%d succeeded, %d failed, %d skipped",
        pid,
        successful,
        len(all_results),
        failed,
        skipped,
    )

    return pipeline_result


# ---------------------------------------------------------------------------
# Event-driven flow helpers
# ---------------------------------------------------------------------------


def handle_mangrove_alert_delivery(
    alert_payload: Dict[str, Any],
    lambda_client: Any = None,
) -> StepResult:
    """Wire a mangrove alert to the Delivery System for notification.

    Called when the Mangrove Monitor detects a warning or critical NDVI
    drop.  Forwards the alert to the Delivery System Lambda which pushes
    notifications to Community_Rep users via LINE and Web Dashboard.

    Requirements: 6.4
    """
    step = PipelineStep(
        name="mangrove_alert_delivery",
        lambda_function_name="sirinapha-delivery-system",
        payload={
            "trigger": "mangrove_alert",
            "message_type": "alert",
            "alert": alert_payload,
        },
    )
    return execute_step(step, lambda_client=lambda_client)


def handle_catch_report_feedback(
    catch_report_payload: Dict[str, Any],
    lambda_client: Any = None,
) -> StepResult:
    """Wire a catch report from LINE webhook to the Yield Predictor.

    Called when a fisherman submits a catch report via LINE.  Forwards
    the parsed catch data to the Yield Predictor's catch ingestion
    endpoint for model retraining feedback.

    Requirements: 6.7
    """
    step = PipelineStep(
        name="catch_report_feedback",
        lambda_function_name="sirinapha-yield-predictor",
        payload={
            "trigger": "catch_report",
            "catch_data": catch_report_payload,
        },
    )
    return execute_step(step, lambda_client=lambda_client)


# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------


def handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """AWS Lambda entry point for the pipeline orchestrator.

    Supports three trigger modes via the ``trigger`` field in the event:

    - ``"daily_pipeline"`` (default): Run the full daily pipeline.
    - ``"mangrove_alert"``: Forward a mangrove alert to the Delivery System.
    - ``"catch_report"``: Forward a catch report to the Yield Predictor.

    Triggered by EventBridge (daily) or by other Lambda functions (event-driven).
    """
    trigger = event.get("trigger", "daily_pipeline")

    try:
        if trigger == "mangrove_alert":
            alert_payload = event.get("alert", {})
            result = handle_mangrove_alert_delivery(alert_payload)
            return {
                "statusCode": 200,
                "body": {
                    "message": "Mangrove alert forwarded to Delivery System",
                    "step": result.step_name,
                    "status": result.status.value,
                    "error": result.error,
                },
            }

        elif trigger == "catch_report":
            catch_data = event.get("catch_data", {})
            result = handle_catch_report_feedback(catch_data)
            return {
                "statusCode": 200,
                "body": {
                    "message": "Catch report forwarded to Yield Predictor",
                    "step": result.step_name,
                    "status": result.status.value,
                    "error": result.error,
                },
            }

        else:
            # Default: run the full daily pipeline
            pipeline_result = run_daily_pipeline()
            status_code = 200 if pipeline_result.all_succeeded else 207

            return {
                "statusCode": status_code,
                "body": {
                    "message": "Daily pipeline completed",
                    "pipeline_id": pipeline_result.pipeline_id,
                    "started_at": pipeline_result.started_at,
                    "completed_at": pipeline_result.completed_at,
                    "total_steps": pipeline_result.total_steps,
                    "successful_steps": pipeline_result.successful_steps,
                    "failed_steps": pipeline_result.failed_steps,
                    "skipped_steps": pipeline_result.skipped_steps,
                    "steps": [
                        {
                            "name": s.step_name,
                            "status": s.status.value,
                            "duration_seconds": s.duration_seconds,
                            "error": s.error,
                        }
                        for s in pipeline_result.steps
                    ],
                },
            }

    except Exception as exc:
        logger.exception("Unexpected error in pipeline orchestrator")
        return {
            "statusCode": 500,
            "body": {"error": f"Pipeline orchestrator failed: {exc}"},
        }
