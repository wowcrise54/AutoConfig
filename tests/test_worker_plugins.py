import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from worker.pkg.plugins import get_plugin


def test_noop_plugin():
    plugin_cls = get_plugin("noop")
    assert plugin_cls is not None
    plugin = plugin_cls()
    events = list(plugin.start())
    assert len(events) == 3
    assert all("progress" in e for e in events)
