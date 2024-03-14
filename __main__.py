import os
import sys
import signal
from opentelemetry import metrics
from opentelemetry.sdk.metrics import Counter, MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricsExporter
import ftptomongo

sys.path.append(os.path.dirname(os.path.realpath(__file__)))


def signal_handler(sig, frame):  
    """
    Signal handler  function to handle KeyboardInterrupt (Ctrl+C).
    """
    print("Ctrl+C detected. Exiting...")
    sys.exit(0)


def main():
    """
    Main function to start
    """
    print("Executing ftptomongo package as a script")

    # Set up OpenTelemetry metrics
    meter_provider = MeterProvider()
    meter = meter_provider.get_meter(__name__)
    exporter = PrometheusMetricsExporter(endpoint="http://localhost:9090")
    meter_provider.start(meter, exporter)

    # Define metrics
    requests_counter = meter.create_metric(
        "requests",
        "Number of requests",
        "requests",
        Counter,
        int,
    )

    # Set the signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    # Your main application logic goes here
    while True:
        ftptomongo.run_ftp_server()
        # Increment requests counter
        requests_counter.add(1)

if __name__ == "__main__":
    main()
