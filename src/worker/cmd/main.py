import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import json

from worker.config import settings
from worker.internal.broker import BrokerClient
from worker.pkg.plugins import get_plugin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def health_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
            else:
                self.send_response(404)
                self.end_headers()

    server = HTTPServer(("0.0.0.0", settings.health_port), Handler)
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
    for event in plugin.start(**params):
        logger.info("event: %s", event)


def main():
    threading.Thread(target=health_server, daemon=True).start()
    broker = BrokerClient(settings.broker_url)
    broker.subscribe("simulations.start", on_message)


if __name__ == "__main__":
    main()
