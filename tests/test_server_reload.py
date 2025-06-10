import sys
from pathlib import Path
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))

from autoconfig import server


def _setup(tmp_path, monkeypatch):
    data = [{"hostname": "alpha"}]
    data_file = tmp_path / "data.json"
    with open(data_file, "w") as f:
        json.dump(data, f)
    original_db = server.DB_PATH
    original_json = server.DATA_JSON
    original_results = server.RESULTS_DIR
    server.DB_PATH = tmp_path / "data.db"
    server.DATA_JSON = data_file
    server.RESULTS_DIR = tmp_path
    server.init_db()
    monkeypatch.setattr(server, "JWT_SECRET", "secret")
    server.USERS = {"admin": {"password": "admin", "role": "admin"}}
    return original_db, original_json, original_results


def _teardown(originals):
    db, data_json, results_dir = originals
    server.DB_PATH = db
    server.DATA_JSON = data_json
    server.RESULTS_DIR = results_dir


def test_reload_requires_token(tmp_path, monkeypatch):
    originals = _setup(tmp_path, monkeypatch)
    app = server.app
    with app.test_client() as client:
        resp = client.post("/api/reload")
        assert resp.status_code == 401
    _teardown(originals)


def test_reload_invalid_token(tmp_path, monkeypatch):
    originals = _setup(tmp_path, monkeypatch)
    app = server.app
    with app.test_client() as client:
        resp = client.post("/api/reload", headers={"Authorization": "Bearer wrong"})
        assert resp.status_code == 401
    _teardown(originals)


def test_reload_valid_token(tmp_path, monkeypatch):
    originals = _setup(tmp_path, monkeypatch)
    app = server.app
    with app.test_client() as client:
        login = client.post("/auth/login", json={"username": "admin", "password": "admin"})
        token = login.get_json()["token"]
        resp = client.post("/api/reload", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.get_json() == {"status": "reloaded"}
    hosts = server.get_hosts()
    assert hosts[0]["hostname"] == "alpha"
    _teardown(originals)

