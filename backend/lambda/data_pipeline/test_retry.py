"""
Unit tests for the data pipeline retry mechanism.

Tests cover retry logic (max 3 attempts, 5-minute delay), admin
notification after exhausted retries, and successful early return.

Requirements: 1.7, 1.8
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Optional
from unittest.mock import MagicMock, call, patch

import pytest

_retry = importlib.import_module("lambda.data_pipeline.retry")

retry_fetch = _retry.retry_fetch
send_admin_notification = _retry.send_admin_notification
RetryResult = _retry.RetryResult
RETRY_MAX_ATTEMPTS = _retry.RETRY_MAX_ATTEMPTS
RETRY_DELAY_MINUTES = _retry.RETRY_DELAY_MINUTES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass
class MockFetchResult:
    """Mimics a FetchResult with a status attribute."""

    status: str
    error: Optional[str] = None


def _make_sleep_mock():
    """Return a mock sleep function that records calls."""
    return MagicMock()


def _make_notify_mock(return_value=True):
    """Return a mock notification function."""
    return MagicMock(return_value=return_value)


# ---------------------------------------------------------------------------
# retry_fetch — success scenarios
# ---------------------------------------------------------------------------


class TestRetryFetchSuccess:
    """Tests for successful fetch scenarios."""

    def test_succeeds_on_first_attempt(self):
        fetch_fn = MagicMock(return_value=MockFetchResult(status="success"))
        sleep_fn = _make_sleep_mock()
        notify_fn = _make_notify_mock()

        result = retry_fetch(
            fetch_fn, "noaa_oisst",
            sleep_fn=sleep_fn, notify_fn=notify_fn,
        )

        assert result.success is True
        assert result.attempts == 1
        assert result.last_error is None
        assert result.admin_notified is False
        fetch_fn.assert_called_once()
        sleep_fn.assert_not_called()
        notify_fn.assert_not_called()

    def test_succeeds_on_second_attempt(self):
        fetch_fn = MagicMock(
            side_effect=[
                MockFetchResult(status="failed", error="timeout"),
                MockFetchResult(status="success"),
            ]
        )
        sleep_fn = _make_sleep_mock()
        notify_fn = _make_notify_mock()

        result = retry_fetch(
            fetch_fn, "noaa_oisst",
            sleep_fn=sleep_fn, notify_fn=notify_fn,
        )

        assert result.success is True
        assert result.attempts == 2
        assert result.last_error is None
        sleep_fn.assert_called_once_with(RETRY_DELAY_MINUTES * 60)
        notify_fn.assert_not_called()

    def test_succeeds_on_third_attempt(self):
        fetch_fn = MagicMock(
            side_effect=[
                MockFetchResult(status="failed", error="err1"),
                MockFetchResult(status="failed", error="err2"),
                MockFetchResult(status="success"),
            ]
        )
        sleep_fn = _make_sleep_mock()
        notify_fn = _make_notify_mock()

        result = retry_fetch(
            fetch_fn, "sentinel2_ndvi",
            sleep_fn=sleep_fn, notify_fn=notify_fn,
        )

        assert result.success is True
        assert result.attempts == 3
        assert sleep_fn.call_count == 2
        notify_fn.assert_not_called()

    def test_returns_result_from_successful_attempt(self):
        expected_result = MockFetchResult(status="success")
        fetch_fn = MagicMock(return_value=expected_result)

        result = retry_fetch(
            fetch_fn, "test_source",
            sleep_fn=_make_sleep_mock(), notify_fn=_make_notify_mock(),
        )

        assert result.result is expected_result

    def test_passes_args_and_kwargs_to_fetch_fn(self):
        fetch_fn = MagicMock(return_value=MockFetchResult(status="success"))

        retry_fetch(
            fetch_fn, "test_source",
            RETRY_MAX_ATTEMPTS, RETRY_DELAY_MINUTES,
            _make_sleep_mock(), _make_notify_mock(),
            "arg1", "arg2", key="value",
        )

        fetch_fn.assert_called_once_with("arg1", "arg2", key="value")


# ---------------------------------------------------------------------------
# retry_fetch — failure scenarios
# ---------------------------------------------------------------------------


class TestRetryFetchFailure:
    """Tests for failed fetch scenarios (all retries exhausted)."""

    def test_fails_after_max_attempts_with_failed_status(self):
        fetch_fn = MagicMock(
            return_value=MockFetchResult(status="failed", error="connection refused")
        )
        sleep_fn = _make_sleep_mock()
        notify_fn = _make_notify_mock(return_value=True)

        result = retry_fetch(
            fetch_fn, "noaa_oisst",
            sleep_fn=sleep_fn, notify_fn=notify_fn,
        )

        assert result.success is False
        assert result.attempts == RETRY_MAX_ATTEMPTS
        assert result.last_error == "connection refused"
        assert result.admin_notified is True
        assert fetch_fn.call_count == RETRY_MAX_ATTEMPTS

    def test_fails_after_max_attempts_with_exceptions(self):
        fetch_fn = MagicMock(side_effect=ConnectionError("Network unreachable"))
        sleep_fn = _make_sleep_mock()
        notify_fn = _make_notify_mock(return_value=True)

        result = retry_fetch(
            fetch_fn, "nasa_modis",
            sleep_fn=sleep_fn, notify_fn=notify_fn,
        )

        assert result.success is False
        assert result.attempts == RETRY_MAX_ATTEMPTS
        assert "Network unreachable" in result.last_error
        assert result.admin_notified is True

    def test_delay_between_attempts(self):
        fetch_fn = MagicMock(
            return_value=MockFetchResult(status="failed", error="timeout")
        )
        sleep_fn = _make_sleep_mock()
        notify_fn = _make_notify_mock()

        retry_fetch(
            fetch_fn, "test_source",
            sleep_fn=sleep_fn, notify_fn=notify_fn,
        )

        expected_delay = RETRY_DELAY_MINUTES * 60
        # Should sleep between attempts but not after the last one
        assert sleep_fn.call_count == RETRY_MAX_ATTEMPTS - 1
        for c in sleep_fn.call_args_list:
            assert c == call(expected_delay)

    def test_no_sleep_after_last_attempt(self):
        fetch_fn = MagicMock(
            return_value=MockFetchResult(status="failed", error="err")
        )
        sleep_fn = _make_sleep_mock()
        notify_fn = _make_notify_mock()

        retry_fetch(
            fetch_fn, "test_source",
            max_attempts=1,
            sleep_fn=sleep_fn, notify_fn=notify_fn,
        )

        sleep_fn.assert_not_called()

    def test_admin_notified_after_all_retries_exhausted(self):
        fetch_fn = MagicMock(
            return_value=MockFetchResult(status="failed", error="API down")
        )
        notify_fn = _make_notify_mock(return_value=True)

        result = retry_fetch(
            fetch_fn, "noaa_oisst",
            sleep_fn=_make_sleep_mock(), notify_fn=notify_fn,
        )

        notify_fn.assert_called_once_with("noaa_oisst", "API down", RETRY_MAX_ATTEMPTS)
        assert result.admin_notified is True

    def test_admin_notification_failure_recorded(self):
        fetch_fn = MagicMock(
            return_value=MockFetchResult(status="failed", error="err")
        )
        notify_fn = _make_notify_mock(return_value=False)

        result = retry_fetch(
            fetch_fn, "test_source",
            sleep_fn=_make_sleep_mock(), notify_fn=notify_fn,
        )

        assert result.admin_notified is False

    def test_mixed_exceptions_and_failed_status(self):
        fetch_fn = MagicMock(
            side_effect=[
                ConnectionError("timeout"),
                MockFetchResult(status="failed", error="bad data"),
                ValueError("parse error"),
            ]
        )
        sleep_fn = _make_sleep_mock()
        notify_fn = _make_notify_mock(return_value=True)

        result = retry_fetch(
            fetch_fn, "test_source",
            sleep_fn=sleep_fn, notify_fn=notify_fn,
        )

        assert result.success is False
        assert result.attempts == 3
        assert "parse error" in result.last_error


# ---------------------------------------------------------------------------
# retry_fetch — custom parameters
# ---------------------------------------------------------------------------


class TestRetryFetchCustomParams:
    """Tests for custom retry parameters."""

    def test_custom_max_attempts(self):
        fetch_fn = MagicMock(
            return_value=MockFetchResult(status="failed", error="err")
        )
        notify_fn = _make_notify_mock()

        result = retry_fetch(
            fetch_fn, "test_source",
            max_attempts=5,
            sleep_fn=_make_sleep_mock(), notify_fn=notify_fn,
        )

        assert result.attempts == 5
        assert fetch_fn.call_count == 5

    def test_custom_delay_minutes(self):
        fetch_fn = MagicMock(
            return_value=MockFetchResult(status="failed", error="err")
        )
        sleep_fn = _make_sleep_mock()

        retry_fetch(
            fetch_fn, "test_source",
            max_attempts=2,
            delay_minutes=10.0,
            sleep_fn=sleep_fn, notify_fn=_make_notify_mock(),
        )

        sleep_fn.assert_called_once_with(600.0)  # 10 minutes in seconds

    def test_result_without_status_attribute_is_success(self):
        """A plain return value (no .status) is treated as success."""
        fetch_fn = MagicMock(return_value={"data": [1, 2, 3]})

        result = retry_fetch(
            fetch_fn, "test_source",
            sleep_fn=_make_sleep_mock(), notify_fn=_make_notify_mock(),
        )

        assert result.success is True
        assert result.result == {"data": [1, 2, 3]}


# ---------------------------------------------------------------------------
# send_admin_notification
# ---------------------------------------------------------------------------


class TestSendAdminNotification:
    """Tests for the SNS admin notification function."""

    @patch.dict("sys.modules", {"boto3": MagicMock()})
    def test_sends_sns_message(self):
        import sys
        mock_boto3 = sys.modules["boto3"]
        mock_sns = MagicMock()
        mock_boto3.client.return_value = mock_sns

        success = send_admin_notification(
            source="noaa_oisst",
            error_message="Connection timeout",
            attempts=3,
            topic_arn="arn:aws:sns:ap-southeast-1:123456:admin-alerts",
        )

        assert success is True
        mock_boto3.client.assert_called_once_with("sns")
        mock_sns.publish.assert_called_once()
        publish_kwargs = mock_sns.publish.call_args[1]
        assert "noaa_oisst" in publish_kwargs["Subject"]
        assert "Connection timeout" in publish_kwargs["Message"]
        assert publish_kwargs["TopicArn"] == "arn:aws:sns:ap-southeast-1:123456:admin-alerts"

    def test_returns_false_when_topic_arn_empty(self):
        success = send_admin_notification(
            source="test",
            error_message="err",
            attempts=3,
            topic_arn="",
        )
        assert success is False

    @patch.dict("sys.modules", {"boto3": MagicMock()})
    def test_returns_false_on_sns_error(self):
        import sys
        mock_boto3 = sys.modules["boto3"]
        mock_sns = MagicMock()
        mock_sns.publish.side_effect = Exception("SNS error")
        mock_boto3.client.return_value = mock_sns

        success = send_admin_notification(
            source="test",
            error_message="err",
            attempts=3,
            topic_arn="arn:aws:sns:test",
        )

        assert success is False
