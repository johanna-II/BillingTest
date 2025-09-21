"""OpenTelemetry instrumentation for test observability."""

import os
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional

from opentelemetry import metrics, trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode


class TestTelemetry:
    """Telemetry collector for test execution metrics."""
    
    def __init__(self, service_name: str = "billing-test"):
        """Initialize telemetry with service name."""
        self.service_name = service_name
        self.resource = Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "test")
        })
        
        # Initialize tracer
        self.tracer_provider = TracerProvider(resource=self.resource)
        trace.set_tracer_provider(self.tracer_provider)
        self.tracer = trace.get_tracer(__name__)
        
        # Initialize meter
        self.meter_provider = MeterProvider(
            resource=self.resource,
            metric_readers=[PrometheusMetricReader()]
        )
        metrics.set_meter_provider(self.meter_provider)
        self.meter = metrics.get_meter(__name__)
        
        # Create metrics
        self._create_metrics()
        
        # Configure exporters
        self._configure_exporters()
        
        # Instrument libraries
        self._instrument_libraries()
    
    def _create_metrics(self):
        """Create test execution metrics."""
        # Test execution counter
        self.test_counter = self.meter.create_counter(
            name="test_executions_total",
            description="Total number of test executions",
            unit="1"
        )
        
        # Test duration histogram
        self.test_duration = self.meter.create_histogram(
            name="test_duration_seconds",
            description="Test execution duration in seconds",
            unit="s"
        )
        
        # API call counter
        self.api_call_counter = self.meter.create_counter(
            name="api_calls_total",
            description="Total number of API calls made during tests",
            unit="1"
        )
        
        # Mock server response time
        self.mock_response_time = self.meter.create_histogram(
            name="mock_server_response_time_ms",
            description="Mock server response time in milliseconds",
            unit="ms"
        )
        
        # Test suite success rate
        self.test_success_gauge = self.meter.create_up_down_counter(
            name="test_success_rate",
            description="Test success rate (1 for success, 0 for failure)",
            unit="1"
        )
    
    def _configure_exporters(self):
        """Configure trace and metric exporters."""
        # Jaeger exporter for traces
        if os.getenv("JAEGER_ENABLED", "false").lower() == "true":
            jaeger_exporter = JaegerExporter(
                agent_host_name=os.getenv("JAEGER_HOST", "localhost"),
                agent_port=int(os.getenv("JAEGER_PORT", "6831")),
            )
            self.tracer_provider.add_span_processor(
                BatchSpanProcessor(jaeger_exporter)
            )
    
    def _instrument_libraries(self):
        """Instrument HTTP libraries for automatic tracing."""
        # Instrument requests library
        RequestsInstrumentor().instrument(
            tracer_provider=self.tracer_provider
        )
        
        # Instrument Flask (for mock server)
        if os.getenv("INSTRUMENT_MOCK_SERVER", "true").lower() == "true":
            FlaskInstrumentor().instrument(
                tracer_provider=self.tracer_provider
            )
    
    @contextmanager
    def trace_test(self, test_name: str, test_type: str = "unit"):
        """Context manager for tracing test execution."""
        span = self.tracer.start_span(
            name=f"test.{test_type}.{test_name}",
            attributes={
                "test.name": test_name,
                "test.type": test_type,
                "test.framework": "pytest"
            }
        )
        
        start_time = time.time()
        success = True
        
        try:
            yield span
        except Exception as e:
            success = False
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise
        else:
            span.set_status(Status(StatusCode.OK))
        finally:
            duration = time.time() - start_time
            
            # Record metrics
            self.test_counter.add(
                1,
                attributes={
                    "test.name": test_name,
                    "test.type": test_type,
                    "test.result": "passed" if success else "failed"
                }
            )
            
            self.test_duration.record(
                duration,
                attributes={
                    "test.name": test_name,
                    "test.type": test_type
                }
            )
            
            self.test_success_gauge.add(
                1 if success else -1,
                attributes={"test.type": test_type}
            )
            
            span.set_attribute("test.duration_seconds", duration)
            span.set_attribute("test.result", "passed" if success else "failed")
            span.end()
    
    def record_api_call(self, endpoint: str, method: str, status_code: int, 
                       response_time_ms: float):
        """Record API call metrics."""
        self.api_call_counter.add(
            1,
            attributes={
                "endpoint": endpoint,
                "method": method,
                "status_code": str(status_code),
                "status_class": f"{status_code // 100}xx"
            }
        )
        
        if "mock" in endpoint.lower():
            self.mock_response_time.record(
                response_time_ms,
                attributes={
                    "endpoint": endpoint,
                    "method": method
                }
            )
    
    def create_span(self, name: str, **attributes) -> trace.Span:
        """Create a new span with attributes."""
        span = self.tracer.start_span(name)
        for key, value in attributes.items():
            span.set_attribute(key, value)
        return span
    
    def get_metrics_endpoint(self) -> str:
        """Get Prometheus metrics endpoint URL."""
        return "http://localhost:9090/metrics"


# Global telemetry instance
_telemetry: Optional[TestTelemetry] = None


def setup_telemetry(service_name: str = "billing-test") -> TestTelemetry:
    """Set up global telemetry instance."""
    global _telemetry
    if _telemetry is None:
        _telemetry = TestTelemetry(service_name)
    return _telemetry


def get_telemetry() -> Optional[TestTelemetry]:
    """Get global telemetry instance."""
    return _telemetry
