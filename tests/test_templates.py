import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from autoconfig import server


def _setup(tmp_path, monkeypatch):
    server.DB_PATH = tmp_path / "data.db"
    server.RESULTS_DIR = tmp_path
    server.init_db()
    monkeypatch.setattr(server, "API_TOKEN", "secret")


def test_create_and_get_template(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    app = server.app
    with app.test_client() as client:
        resp = client.post(
            "/api/v1/templates",
            json={"name": "foo", "description": "d", "config": {"a": 1}},
            headers={"Authorization": "Bearer secret"},
        )
        assert resp.status_code == 201
        data = resp.get_json()
        tid = data["id"]
        assert data["version"] == 1

        resp = client.get(
            f"/api/v1/templates/{tid}", headers={"Authorization": "Bearer secret"}
        )
        assert resp.status_code == 200
        fetched = resp.get_json()
        assert fetched["id"] == tid
        assert fetched["version"] == 1


def test_version_increment(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    app = server.app
    with app.test_client() as client:
        for i in range(2):
            resp = client.post(
                "/api/v1/templates",
                json={"name": "foo", "description": "d", "config": {"a": i}},
                headers={"Authorization": "Bearer secret"},
            )
            assert resp.status_code == 201
            assert resp.get_json()["version"] == i + 1

        resp = client.get(
            "/api/v1/templates",
            headers={"Authorization": "Bearer secret"},
        )
        assert resp.status_code == 200
        items = resp.get_json()
        assert len(items) == 1
        assert items[0]["version"] == 2
