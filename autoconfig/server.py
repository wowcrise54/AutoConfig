import json
import sqlite3
from pathlib import Path
from flask import Flask, jsonify, send_from_directory, request
import os
import logging
import argparse
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime

level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, level_name, logging.INFO))
logger = logging.getLogger(__name__)

# Authentication token for API requests
API_TOKEN = os.environ.get("API_TOKEN")

# ``server.py`` now lives inside the ``autoconfig`` package. ``BASE_DIR``
# should therefore point to the project root to keep the default ``results``
# directory unchanged.
BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"
DB_PATH = RESULTS_DIR / "data.db"
DATA_JSON = RESULTS_DIR / "data.json"


@dataclass
class Template:
    id: str
    name: str
    description: str | None
    version: int
    config: dict
    created_at: str
    updated_at: str
    active: int = 0

    def to_dict(self):
        return asdict(self)


app = Flask(__name__)


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS hosts (hostname TEXT PRIMARY KEY, data TEXT)"
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                version INTEGER NOT NULL,
                config TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                active INTEGER DEFAULT 0,
                UNIQUE(name, version)
            )
            """
        )
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_templates_name_version "
            "ON templates(name, version)"
        )


def load_data():
    """Load hosts from ``DATA_JSON`` into the SQLite database."""
    if DATA_JSON.exists():
        with open(DATA_JSON) as f:
            hosts = json.load(f)
    else:
        hosts = []
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM hosts")
        for h in hosts:
            cur.execute(
                "INSERT OR REPLACE INTO hosts(hostname, data) VALUES(?, ?)",
                (h.get("hostname"), json.dumps(h)),
            )


def _now() -> str:
    return datetime.utcnow().isoformat()


def create_template(name: str, description: str | None, config: dict) -> Template:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT MAX(version) FROM templates WHERE name = ?", (name,))
        row = cur.fetchone()
        version = (row[0] or 0) + 1
        tid = str(uuid.uuid4())
        ts = _now()
        cur.execute(
            (
                "INSERT INTO templates(id, name, description, version, config, "
                "created_at, updated_at) VALUES(?,?,?,?,?,?,?)"
            ),
            (tid, name, description, version, json.dumps(config), ts, ts),
        )
        conn.commit()
    return Template(tid, name, description, version, config, ts, ts)


def list_latest_templates(limit: int = 100, offset: int = 0) -> list[Template]:
    query = """
    SELECT t1.* FROM templates t1
    JOIN (SELECT name, MAX(version) AS ver FROM templates GROUP BY name) t2
      ON t1.name = t2.name AND t1.version = t2.ver
    ORDER BY t1.name LIMIT ? OFFSET ?
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(query, (limit, offset))
        rows = cur.fetchall()
    return [
        Template(
            r[0],
            r[1],
            r[2],
            r[3],
            json.loads(r[4]),
            r[5],
            r[6],
            r[7],
        )
        for r in rows
    ]


def get_template(template_id: str) -> Template | None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM templates WHERE id = ?", (template_id,))
        row = cur.fetchone()
    if not row:
        return None
    return Template(
        row[0],
        row[1],
        row[2],
        row[3],
        json.loads(row[4]),
        row[5],
        row[6],
        row[7],
    )


def update_template(
    template_id: str, description: str | None, config: dict | None
) -> Template | None:
    tpl = get_template(template_id)
    if not tpl:
        return None
    new_desc = description if description is not None else tpl.description
    new_config = config if config is not None else tpl.config
    ts = _now()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            (
                "UPDATE templates SET description = ?, config = ?, updated_at = ? "
                "WHERE id = ?"
            ),
            (new_desc, json.dumps(new_config), ts, template_id),
        )
        conn.commit()
    return Template(
        tpl.id,
        tpl.name,
        new_desc,
        tpl.version,
        new_config,
        tpl.created_at,
        ts,
        tpl.active,
    )


def delete_template(template_id: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM templates WHERE id = ?", (template_id,))
        conn.commit()
        return cur.rowcount > 0


def get_hosts(search=None, sort=None, order="asc"):
    """Return hosts filtered by search and ordered via SQL."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        query = "SELECT data FROM hosts"
        params = []
        if search:
            query += " WHERE hostname LIKE ?"
            params.append(f"%{search}%")

        if sort:
            allowed = {"hostname", "cpu_load", "memory", "disk", "net", "sensors"}
            if sort == "hostname":
                order_field = "hostname"
            elif sort in allowed:
                order_field = f"json_extract(data, '$.{sort}')"
            else:
                order_field = "hostname"

            query += f" ORDER BY {order_field}"
            if order and order.lower() == "desc":
                query += " DESC"
            else:
                query += " ASC"

        cur.execute(query, params)
        rows = cur.fetchall()

    return [json.loads(r[0]) for r in rows]


@app.route("/api/hosts")
def hosts():
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {API_TOKEN}":
        return "", 401
    search = request.args.get("search")
    sort = request.args.get("sort")
    order = request.args.get("order", "asc")
    hosts_list = get_hosts(search=search, sort=sort, order=order)
    return jsonify(hosts_list)


@app.route("/api/v1/templates", methods=["POST"])
def create_template_endpoint():
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {API_TOKEN}":
        return "", 401
    data = request.get_json(force=True)
    name = data.get("name")
    if not name:
        return jsonify({"error": "name required"}), 400
    description = data.get("description")
    config = data.get("config")
    if not isinstance(config, dict):
        return jsonify({"error": "config must be object"}), 400
    tpl = create_template(name, description, config)
    return jsonify(tpl.to_dict()), 201


@app.route("/api/v1/templates", methods=["GET"])
def list_templates_endpoint():
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {API_TOKEN}":
        return "", 401
    try:
        limit = int(request.args.get("limit", 100))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return jsonify({"error": "invalid pagination"}), 400
    templates = [t.to_dict() for t in list_latest_templates(limit, offset)]
    return jsonify(templates)


@app.route("/api/v1/templates/<template_id>", methods=["GET"])
def get_template_endpoint(template_id):
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {API_TOKEN}":
        return "", 401
    tpl = get_template(template_id)
    if not tpl:
        return jsonify({"error": "Template not found"}), 404
    return jsonify(tpl.to_dict())


@app.route("/api/v1/templates/<template_id>", methods=["PUT"])
def update_template_endpoint(template_id):
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {API_TOKEN}":
        return "", 401
    data = request.get_json(force=True)
    description = data.get("description")
    config = data.get("config")
    if config is not None and not isinstance(config, dict):
        return jsonify({"error": "config must be object"}), 400
    tpl = update_template(template_id, description, config)
    if not tpl:
        return jsonify({"error": "Template not found"}), 404
    return jsonify(tpl.to_dict())


@app.route("/api/v1/templates/<template_id>", methods=["DELETE"])
def delete_template_endpoint(template_id):
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {API_TOKEN}":
        return "", 401
    deleted = delete_template(template_id)
    if not deleted:
        return jsonify({"error": "Template not found"}), 404
    return "", 204


@app.route("/api/reload", methods=["POST"])
def reload_data_endpoint():
    """Reload host information from ``DATA_JSON``. Requires API token."""
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {API_TOKEN}":
        return "", 401
    load_data()
    return jsonify({"status": "reloaded"})


@app.route("/")
def index():
    index_file = RESULTS_DIR / "index.html"
    if index_file.exists():
        return send_from_directory(RESULTS_DIR, "index.html")
    return (
        "Flask server is running. Use /api/hosts to get data. "
        "POST /api/reload to refresh."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AutoConfig Flask API")
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to run the server on",
    )
    parser.add_argument(
        "--results-dir",
        default=str(RESULTS_DIR),
        help="Directory containing rendered results",
    )
    args = parser.parse_args()

    RESULTS_DIR = Path(args.results_dir)
    DB_PATH = RESULTS_DIR / "data.db"
    DATA_JSON = RESULTS_DIR / "data.json"

    init_db()
    load_data()
    logger.info("Starting Flask server on port %s", args.port)
    app.run(host="0.0.0.0", port=args.port)
