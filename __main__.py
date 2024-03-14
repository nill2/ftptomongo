'''
This is a main file to start it all
'''
import os
import sys
import signal  # Import the signal module without using it directly

from opentelemetry.sdk.resources import SERVICE_NAME, Resource

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

import ftptomongo
sys.path.append(os.path.dirname(os.path.realpath(__file__)))


def signal_handler(sig, frame):  # pylint: disable=unused-argument
    """
    Signal handler function to handle KeyboardInterrupt (Ctrl+C).
    """
    print("Ctrl+C detected. Exiting...")
    sys.exit(0)


def main():
    """
    Main function to start
    """
    print("Executing ftptomongo package as a script")

    # setup OTLP
    # Service name is required for most backends
    resource = Resource(attributes={
                        SERVICE_NAME: "ftptomongo"
                        })

    trace_provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:9090/v1/traces"))
    trace_provider.add_span_processor(processor)
    trace.set_tracer_provider(trace_provider)

    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint="<http://localhost:9090/v1/metrics")
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)

    # Set the signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    # Your main application logic goes here
    ftptomongo.run_ftp_server()


if __name__ == "__main__":
    main()
