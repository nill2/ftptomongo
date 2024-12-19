"""Orchestrate it all in a main file."""

import os
import sys
import signal  # Import the signal module without using it directly
from typing import Optional
from types import FrameType

from opentelemetry.sdk.resources import SERVICE_NAME, Resource

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

#  import pyroscope  # pylint: disable=import-error
import ftptomongo

#  from config import PYROSCOPE_SERVER_ADDRESS  # pylint: disable=import-error


# if PYROSCOPE_SERVER_ADDRESS is not None:
#    pyroscope.configure(
#        application_name="ftptomongo",
#        # replace this with some name for your application
#        server_address=PYROSCOPE_SERVER_ADDRESS,
#        # replace this with the address of your Pyroscope server
#        sample_rate=1000,  # default is 100
#        detect_subprocesses=True,  # detect subprocesses started by the main process; default is False
#        oncpu=True,  # report cpu time only; default is True
#        gil_only=True,
#        # only include traces for threads that are holding on to the Global Interpreter Lock;
#        # default is True
#        enable_logging=True,  # does enable logging facility; default is False
#        tags={
#            "region": '{os.getenv("REGION")}',
#        },
#    )
sys.path.append(os.path.dirname(os.path.realpath(__file__)))


def signal_handler(sig: int, frame: Optional[FrameType]) -> None:  # pylint: disable=unused-argument
    """Signal handler function to handle KeyboardInterrupt (Ctrl+C)."""
    print("Ctrl+C detected. Exiting...")
    sys.exit(0)


def main() -> None:
    """Initialize the main function to start the execution."""
    print("Executing ftptomongo package as a script")

    # setup OTLP
    # Service name is required for most backends
    resource = Resource(attributes={SERVICE_NAME: "ftptomongo"})

    trace_provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:9090/v1/traces"))
    trace_provider.add_span_processor(processor)
    trace.set_tracer_provider(trace_provider)

    reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint="<http://localhost:9090/v1/metrics"))
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)

    # Set the signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    # Your main application logic goes here
    ftptomongo.run_ftp_server()


if __name__ == "__main__":
    main()
