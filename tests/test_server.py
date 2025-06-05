import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from autoconfig import server
from flask import Flask


def test_index_without_file(tmp_path):
    original_dir = server.RESULTS_DIR
    server.RESULTS_DIR = tmp_path
    app: Flask = server.app
    with app.test_client() as client:
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Flask server is running" in resp.data
    server.RESULTS_DIR = original_dir
