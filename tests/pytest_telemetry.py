"""Pytest plugin for automatic test telemetry collection."""

import time
from typing import TYPE_CHECKING, Any

import pytest
from _pytest.config import Config
from _pytest.nodes import Item
from _pytest.runner import CallInfo

from libs.observability import TestTelemetry, setup_telemetry

if TYPE_CHECKING:
    from _pytest.reports import TestReport


class TelemetryPlugin:
    """Pytest plugin for collecting test execution telemetry."""

    def __init__(self, telemetry: TestTelemetry) -> None:
        self.telemetry = telemetry
        self.test_spans: dict[str, Any] = {}
        self.test_start_times: dict[str, float] = {}

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_setup(self, item: Item) -> None:
        """Called before test setup."""
        test_name = item.nodeid
        self.test_start_times[test_name] = time.time()

        # Start span for test
        span = self.telemetry.tracer.start_span(
            name=f"test.{test_name}",
            attributes={
                "test.name": item.name,
                "test.file": str(item.fspath),
                "test.class": item.cls.__name__ if item.cls else "",
                "test.module": item.module.__name__,
                "test.markers": [marker.name for marker in item.iter_markers()],
            },
        )
        self.test_spans[test_name] = span

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: Item, call: CallInfo) -> None:
        """Called after test execution."""
        outcome = yield
        report: TestReport = outcome.get_result()

        if report.when == "call":  # Only process actual test execution
            test_name = item.nodeid
            duration = time.time() - self.test_start_times.get(test_name, time.time())

            # Get span
            span = self.test_spans.get(test_name)
            if span:
                # Update span with results
                span.set_attribute("test.outcome", report.outcome)
                span.set_attribute("test.duration_seconds", duration)

                if report.failed:
                    span.set_attribute("test.error", str(report.longrepr))
                    span.set_status(
                        self.telemetry.tracer._tracer.Status(
                            self.telemetry.tracer._tracer.StatusCode.ERROR,
                            "Test failed",
                        )
                    )

                # Record metrics
                self.telemetry.test_counter.add(
                    1,
                    attributes={
                        "test.name": item.name,
                        "test.outcome": report.outcome,
                        "test.file": str(item.fspath),
                    },
                )

                self.telemetry.test_duration.record(
                    duration,
                    attributes={"test.name": item.name, "test.outcome": report.outcome},
                )

    @pytest.hookimpl(trylast=True)
    def pytest_runtest_teardown(self, item: Item) -> None:
        """Called after test teardown."""
        test_name = item.nodeid

        # End span
        span = self.test_spans.pop(test_name, None)
        if span:
            span.end()

        # Clean up timing
        self.test_start_times.pop(test_name, None)

    @pytest.hookimpl
    def pytest_sessionstart(self, session) -> None:
        """Called at test session start."""
        span = self.telemetry.tracer.start_span(
            name="pytest.session",
            attributes={
                "session.name": session.name,
                "session.config": str(session.config.args),
            },
        )
        self.session_span = span

    @pytest.hookimpl
    def pytest_sessionfinish(self, session, exitstatus) -> None:
        """Called at test session end."""
        if hasattr(self, "session_span"):
            self.session_span.set_attribute("session.exitstatus", exitstatus)
            self.session_span.set_attribute(
                "session.testscollected", session.testscollected
            )
            self.session_span.set_attribute("session.testsfailed", session.testsfailed)
            self.session_span.end()


def pytest_configure(config: Config) -> None:
    """Configure pytest with telemetry plugin."""
    if config.getoption("--enable-telemetry", default=False):
        telemetry = setup_telemetry("billing-test")
        plugin = TelemetryPlugin(telemetry)
        config.pluginmanager.register(plugin, "telemetry")


def pytest_addoption(parser) -> None:
    """Add telemetry command line options."""
    parser.addoption(
        "--enable-telemetry",
        action="store_true",
        default=False,
        help="Enable OpenTelemetry instrumentation for tests",
    )

    parser.addoption(
        "--jaeger-host",
        action="store",
        default="localhost",
        help="Jaeger host for trace export",
    )

    parser.addoption(
        "--jaeger-port",
        action="store",
        default="6831",
        help="Jaeger port for trace export",
    )


# Fixture for manual telemetry usage in tests
@pytest.fixture
def telemetry() -> TestTelemetry | None:
    """Get telemetry instance for manual instrumentation."""
    from libs.observability import get_telemetry

    return get_telemetry()
