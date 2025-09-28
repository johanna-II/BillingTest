"""Test telemetry implementation using OpenTelemetry."""

import logging
import os
from contextlib import contextmanager
from typing import Any

# Optional imports - telemetry is optional feature
try:
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.trace import Status, StatusCode

    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False

logger = logging.getLogger(__name__)


class TelemetryManager:
    """Test telemetry for monitoring test execution and API calls."""

    def __init__(self) -> None:
        """Initialize telemetry components."""
        if not TELEMETRY_AVAILABLE:
            self.tracer = None
            self.meter = None
            return

        # Initialize tracer
        self.tracer = trace.get_tracer(__name__)

        # Initialize meter
        self.meter = metrics.get_meter(__name__)

        # Create metrics
        self.test_counter = self.meter.create_counter(
            name="test_executions",
            description="Number of test executions",
            unit="1",
        )

        self.test_duration = self.meter.create_histogram(
            name="test_duration",
            description="Test execution duration",
            unit="seconds",
        )

        self.api_counter = self.meter.create_counter(
            name="api_calls",
            description="Number of API calls",
            unit="1",
        )

        self.api_histogram = self.meter.create_histogram(
            name="api_response_time",
            description="API response time",
            unit="milliseconds",
        )

    def record_test_execution(
        self, test_name: str, status: str, duration: float
    ) -> None:
        """Record test execution metrics."""
        if not TELEMETRY_AVAILABLE:
            return

        self.test_counter.add(1, {"test_name": test_name, "status": status})

        self.test_duration.record(duration, {"test_name": test_name, "status": status})

    def record_api_call(
        self, method: str, endpoint: str, status_code: int, response_time: float
    ) -> None:
        """Record API call metrics."""
        if not TELEMETRY_AVAILABLE:
            return

        self.api_counter.add(
            1, {"method": method, "endpoint": endpoint, "status_code": status_code}
        )

        self.api_histogram.record(
            int(response_time * 1000),  # Convert to milliseconds
            {"method": method, "endpoint": endpoint},
        )

    def create_span(
        self,
        name: str,
        operation_type: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Any:
        """Create a new span."""
        if not TELEMETRY_AVAILABLE or not self.tracer:
            return None

        span = self.tracer.start_span(name)

        if operation_type:
            span.set_attribute("operation.type", operation_type)

        if attributes:
            for key, value in attributes.items():
                if value is not None:
                    span.set_attribute(key, value)

        return span

    @contextmanager
    def trace_test(self, test_name: str, test_type: str = "unit") -> Any:
        """Context manager to trace test execution."""
        if not TELEMETRY_AVAILABLE or not self.tracer:
            yield None
            return

        with self.tracer.start_as_current_span(test_name) as span:
            span.set_attribute("test.type", test_type)
            span.set_attribute("test.framework", "pytest")

            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise


# Singleton instance
_telemetry_instance: TelemetryManager | None = None


def get_telemetry() -> TelemetryManager | None:
    """Get telemetry instance (singleton)."""
    global _telemetry_instance

    if (
        _telemetry_instance is None
        and os.environ.get("ENABLE_TELEMETRY", "true").lower() != "false"
    ):
        _telemetry_instance = TelemetryManager()

    return _telemetry_instance


def setup_telemetry(service_name: str = "billing-test") -> TelemetryManager | None:
    """Setup telemetry with providers."""
    if not TELEMETRY_AVAILABLE:
        logger.info("Telemetry not available - dependencies not installed")
        return None

    if os.environ.get("ENABLE_TELEMETRY", "true").lower() == "false":
        logger.info("Telemetry disabled via environment variable")
        return None

    # Configure telemetry providers
    configure_telemetry(service_name)

    return get_telemetry()


def configure_telemetry(service_name: str = "billing-test") -> None:
    """Configure OpenTelemetry providers."""
    if not TELEMETRY_AVAILABLE:
        return

    # Create resource
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": "1.0.0",
        }
    )

    # Setup tracer provider
    tracer_provider = TracerProvider(resource=resource)

    # Add OTLP exporter if configured (compatible with Jaeger's OTLP receiver)
    if os.environ.get("OTLP_ENABLED", "false").lower() == "true":
        otlp_exporter = OTLPSpanExporter(
            endpoint=os.environ.get("OTLP_ENDPOINT", "localhost:4317"),
            insecure=os.environ.get("OTLP_INSECURE", "true").lower() == "true",
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Add console exporter for debugging
    if os.environ.get("TELEMETRY_CONSOLE", "false").lower() == "true":
        tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(tracer_provider)

    # Setup meter provider
    meter_provider = MeterProvider(resource=resource)
    metrics.set_meter_provider(meter_provider)
