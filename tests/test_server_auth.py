import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import server


def _setup(tmp_path, monkeypatch):
    original_db = server.DB_PATH
    server.DB_PATH = tmp_path / "data.db"
    server.init_db()
    monkeypatch.setattr(server, "API_TOKEN", "secret")
    return original_db


def test_hosts_requires_token(tmp_path, monkeypatch):
    original_db = _setup(tmp_path, monkeypatch)
    app = server.app
    with app.test_client() as client:
        resp = client.get("/api/hosts")
        assert resp.status_code == 401
    server.DB_PATH = original_db


def test_hosts_invalid_token(tmp_path, monkeypatch):
    original_db = _setup(tmp_path, monkeypatch)
    app = server.app
    with app.test_client() as client:
        resp = client.get("/api/hosts", headers={"Authorization": "Bearer wrong"})
        assert resp.status_code == 401
    server.DB_PATH = original_db


def test_hosts_valid_token(tmp_path, monkeypatch):
    original_db = _setup(tmp_path, monkeypatch)
    app = server.app
    with app.test_client() as client:
        resp = client.get("/api/hosts", headers={"Authorization": "Bearer secret"})
        assert resp.status_code == 200
    server.DB_PATH = original_db
