import json
import sqlite3
from pathlib import Path
from flask import Flask, jsonify, send_from_directory, request
import os
import logging
import argparse

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

app = Flask(__name__)


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS hosts (hostname TEXT PRIMARY KEY, data TEXT)"
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
