import sys
from pathlib import Path
import json
import sqlite3

sys.path.append(str(Path(__file__).resolve().parents[1]))

from autoconfig import server


def _prepare_db(tmp_path):
    original_db = server.DB_PATH
    server.DB_PATH = tmp_path / "data.db"
    server.init_db()
    sample = [
        {"hostname": "alpha", "memory": 2048},
        {"hostname": "beta", "memory": 1024},
        {"hostname": "gamma", "memory": 3072},
    ]
    with sqlite3.connect(server.DB_PATH) as conn:
        cur = conn.cursor()
        for h in sample:
            cur.execute(
                "INSERT INTO hosts(hostname, data) VALUES(?, ?)",
                (h["hostname"], json.dumps(h)),
            )
    return sample, original_db


def test_get_hosts_search(tmp_path):
    hosts, original_db = _prepare_db(tmp_path)
    result = server.get_hosts(search="bet")
    assert len(result) == 1
    assert result[0]["hostname"] == "beta"
    server.DB_PATH = original_db


def test_get_hosts_sort(tmp_path):
    hosts, original_db = _prepare_db(tmp_path)
    result = server.get_hosts(sort="memory")
    assert [h["hostname"] for h in result] == ["beta", "alpha", "gamma"]
    server.DB_PATH = original_db


def test_get_hosts_order_desc(tmp_path):
    hosts, original_db = _prepare_db(tmp_path)
    result = server.get_hosts(sort="hostname", order="desc")
    assert [h["hostname"] for h in result] == ["gamma", "beta", "alpha"]
    server.DB_PATH = original_db
