import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts import collect_and_visualize as cav
import sys


def test_parse_args_defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog"])
    args = cav.parse_args()
    assert args.output_dir == str(cav.DEFAULT_RESULTS_DIR)
    assert args.port == cav.DEFAULT_NGINX_PORT
    assert args.hosts is None


def test_parse_args_hosts(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "--hosts", "a,b"])
    args = cav.parse_args()
    assert args.hosts == ["a", "b"]
