import time
import requests
from . import ScenarioPlugin, register_plugin


class DDoSPlugin(ScenarioPlugin):
    def start(self, target_ip: str, duration: int = 10, rate: int = 1, **_):
        end = time.time() + duration
        sent = 0
        while time.time() < end:
            try:
                requests.get(f"http://{target_ip}", timeout=1)
            except Exception:
                pass
            sent += 1
            yield {"progress": (sent / (duration * rate)), "timestamp": time.time()}
            time.sleep(max(1 / rate, 0))


register_plugin("ddos", DDoSPlugin)
