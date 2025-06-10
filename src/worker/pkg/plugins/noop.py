import time
from . import ScenarioPlugin, register_plugin


class NoopPlugin(ScenarioPlugin):
    def start(self, **params):
        for i in range(3):
            yield {"progress": i / 3, "timestamp": time.time()}
            time.sleep(0.1)


register_plugin("noop", NoopPlugin)
