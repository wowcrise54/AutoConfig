import sys
from pathlib import Path
import json
import subprocess

sys.path.append(str(Path(__file__).resolve().parents[1]))

from autoconfig import collect_and_visualize as cav


def test_collect_local_adds_net_and_sensors(tmp_path, monkeypatch):
    sample_net = ["lo: 0 0 0 0"]
    sample_sensors = ["temp: 42C"]

    def fake_check_output(cmd, text=True, shell=False):
        if cmd == ["hostname"]:
            return "testhost\n"
        elif cmd == ["getent", "passwd"]:
            return ""
        elif cmd == ["ss", "-tulwn"]:
            return ""
        elif cmd == "df -h --output=size,used,avail,pcent / | tail -n 1":
            return "disk\n"
        elif cmd == "free -m | grep 'Mem:'":
            return "mem\n"
        elif cmd == ["cat", "/proc/loadavg"]:
            return "0\n"
        elif cmd == ["cat", "/proc/net/dev"]:
            return "\n".join(sample_net) + "\n"
        elif cmd == ["sensors"]:
            return "\n".join(sample_sensors) + "\n"
        else:
            raise FileNotFoundError

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    original_dir = cav.RESULTS_DIR
    cav.RESULTS_DIR = tmp_path

    cav.collect_local_facts()

    result_file = tmp_path / "facts_testhost.json"
    with open(result_file) as f:
        data = json.load(f)

    assert data["net"] == sample_net
    assert data["sensors"] == sample_sensors

    cav.RESULTS_DIR = original_dir
