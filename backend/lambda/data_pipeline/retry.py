"""
Retry Mechanism for Data Pipeline External API Calls.

Provides a generic retry wrapper that can wrap any fetch function:
- Max 3 attempts with 5-minute delay between attempts
- After 3 failed attempts, sends admin notification via SNS
- Returns the result from the first successful attempt
- Logs each retry attempt

Requirements: 1.7, 1.8
"""

from __future__ import annotations

import importlib as _il
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional, TypeVar

_config = _il.import_module("lambda.shared.config")
RETRY_MAX_ATTEMPTS = _config.RETRY_MAX_ATTEMPTS
RETRY_DELAY_MINUTES = _config.RETRY_DELAY_MINUTES
SNS_ADMIN_TOPIC_ARN = _config.SNS_ADMIN_TOPIC_ARN

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class RetryResult:
    """Outcome of a retried operation."""

    success: bool
    result: Any = None
    attempts: int = 0
    last_error: Optional[str] = None
    admin_notified: bool = False


# ---------------------------------------------------------------------------
# SNS notification
# ---------------------------------------------------------------------------


def send_admin_notification(
    source: str,
    error_message: str,
    attempts: int,
    topic_arn: str = SNS_ADMIN_TOPIC_ARN,
) -> bool:
    """Send an admin notification via AWS SNS after all retries are exhausted.

    Parameters
    ----------
    source:
        Name of the data source that failed (e.g. ``"noaa_oisst"``).
    error_message:
        Description of the last error encountered.
    attempts:
        Total number of attempts made.
    topic_arn:
        SNS topic ARN for admin notifications.

    Returns
    -------
    bool
        ``True`` if the notification was sent successfully, ``False`` otherwise.
    """
    if not topic_arn:
        logger.warning(
            "SNS_ADMIN_TOPIC_ARN not configured — cannot send admin notification "
            "for source=%s after %d attempts",
            source,
            attempts,
        )
        return False

    subject = f"[SIRINAPHA] Data Pipeline Alert: {source} failed after {attempts} attempts"
    message = (
        f"Data Pipeline Failure Report\n"
        f"============================\n"
        f"Source: {source}\n"
        f"Attempts: {attempts}\n"
        f"Last Error: {error_message}\n"
        f"\n"
        f"Action Required: Please investigate the data source connectivity "
        f"and retry manually if needed."
    )

    try:
        import boto3

        sns_client = boto3.client("sns")
        sns_client.publish(
            TopicArn=topic_arn,
            Subject=subject[:100],  # SNS subject max 100 chars
            Message=message,
        )
        logger.info(
            "Admin notification sent for source=%s (topic=%s)",
            source,
            topic_arn,
        )
        return True
    except Exception as exc:
        logger.error(
            "Failed to send admin notification for source=%s: %s",
            source,
            exc,
        )
        return False


# ---------------------------------------------------------------------------
# Retry wrapper
# ---------------------------------------------------------------------------


def retry_fetch(
    fetch_fn: Callable[..., Any],
    source: str,
    max_attempts: int = RETRY_MAX_ATTEMPTS,
    delay_minutes: float = RETRY_DELAY_MINUTES,
    sleep_fn: Callable[[float], None] = time.sleep,
    notify_fn: Optional[Callable[[str, str, int], bool]] = None,
    *args: Any,
    **kwargs: Any,
) -> RetryResult:
    """Execute a fetch function with retry logic.

    Retries the given function up to ``max_attempts`` times with a
    ``delay_minutes`` pause between each attempt. If all attempts fail,
    sends an admin notification.

    Parameters
    ----------
    fetch_fn:
        The function to call. Should raise an exception on failure or
        return a result with a ``status`` attribute (``"failed"`` triggers
        retry).
    source:
        Human-readable name of the data source (for logging/notifications).
    max_attempts:
        Maximum number of attempts (default: 3).
    delay_minutes:
        Delay in minutes between retry attempts (default: 5).
    sleep_fn:
        Sleep function (injectable for testing).
    notify_fn:
        Admin notification function (injectable for testing). Defaults to
        ``send_admin_notification``.
    *args, **kwargs:
        Passed through to ``fetch_fn``.

    Returns
    -------
    RetryResult
        Contains the result on success, or error details on failure.
    """
    if notify_fn is None:
        notify_fn = lambda src, err, att: send_admin_notification(src, err, att)

    last_error: Optional[str] = None
    delay_seconds = delay_minutes * 60

    for attempt in range(1, max_attempts + 1):
        logger.info(
            "Attempt %d/%d for source=%s",
            attempt,
            max_attempts,
            source,
        )

        try:
            result = fetch_fn(*args, **kwargs)

            # Check if the result indicates failure via a status attribute
            if hasattr(result, "status") and result.status == "failed":
                last_error = getattr(result, "error", None) or "Fetch returned failed status"
                logger.warning(
                    "Attempt %d/%d for source=%s returned failed status: %s",
                    attempt,
                    max_attempts,
                    source,
                    last_error,
                )
            else:
                # Success
                logger.info(
                    "Source=%s succeeded on attempt %d/%d",
                    source,
                    attempt,
                    max_attempts,
                )
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempt,
                    last_error=None,
                    admin_notified=False,
                )
        except Exception as exc:
            last_error = str(exc)
            logger.warning(
                "Attempt %d/%d for source=%s raised exception: %s",
                attempt,
                max_attempts,
                source,
                exc,
            )

        # Wait before next attempt (but not after the last attempt)
        if attempt < max_attempts:
            logger.info(
                "Waiting %.1f minutes before retry %d for source=%s",
                delay_minutes,
                attempt + 1,
                source,
            )
            sleep_fn(delay_seconds)

    # All attempts exhausted — send admin notification
    logger.error(
        "All %d attempts exhausted for source=%s. Last error: %s",
        max_attempts,
        source,
        last_error,
    )

    admin_notified = notify_fn(source, last_error or "Unknown error", max_attempts)

    return RetryResult(
        success=False,
        result=None,
        attempts=max_attempts,
        last_error=last_error,
        admin_notified=admin_notified,
    )
