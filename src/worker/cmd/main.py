import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
import ssl
import threading
import json
import time

from prometheus_client import (
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

from worker.config import settings
from worker.internal.broker import BrokerClient
from worker.pkg.plugins import get_plugin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SIMULATION_DURATION_SECONDS = Histogram(
    "simulation_duration_seconds",
    "Duration of simulation runs in seconds",
    ["plugin"],
)
SIMULATION_ERRORS_TOTAL = Counter(
    "simulation_errors_total",
    "Total simulation errors",
    ["plugin"],
)


def health_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                self.send_response(200)
                self.send_header(
                    "Strict-Transport-Security",
                    "max-age=31536000; includeSubDomains",
                )
                self.end_headers()
                self.wfile.write(b"OK")
            elif self.path == "/metrics":
                data = generate_latest()
                self.send_response(200)
                self.send_header("Content-Type", CONTENT_TYPE_LATEST)
                self.send_header("Content-Length", str(len(data)))
                self.send_header(
                    "Strict-Transport-Security",
                    "max-age=31536000; includeSubDomains",
                )
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(404)
                self.send_header(
                    "Strict-Transport-Security",
                    "max-age=31536000; includeSubDomains",
                )
                self.end_headers()

    server = HTTPServer(("0.0.0.0", settings.health_port), Handler)
    if settings.tls_cert and settings.tls_key:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(settings.tls_cert, settings.tls_key)
        server.socket = context.wrap_socket(server.socket, server_side=True)
    logger.info("Healthcheck on port %s", settings.health_port)
    server.serve_forever()


def on_message(body: bytes):
    logger.info("Received message: %s", body)
    try:
        data = json.loads(body)
        plugin_name = data.get("template_type", "noop")
        params = data.get("params", {})
    except Exception:
        logger.error("Invalid message")
        return
    plugin_cls = get_plugin(plugin_name)
    if not plugin_cls:
        logger.error("Unknown plugin %s", plugin_name)
        return
    plugin = plugin_cls()
    start = time.perf_counter()
    try:
        for event in plugin.start(**params):
            logger.info("event: %s", event)
    except Exception:
        logger.exception("Simulation error")
        SIMULATION_ERRORS_TOTAL.labels(plugin_name).inc()
    else:
        duration = time.perf_counter() - start
        SIMULATION_DURATION_SECONDS.labels(plugin_name).observe(duration)


def main():
    threading.Thread(target=health_server, daemon=True).start()
    broker = BrokerClient(settings.broker_url)
    broker.subscribe("simulations.start", on_message)


if __name__ == "__main__":
    main()
