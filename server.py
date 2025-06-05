import json
import sqlite3
from pathlib import Path
from flask import Flask, jsonify, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / 'results'
DB_PATH = RESULTS_DIR / 'data.db'
DATA_JSON = RESULTS_DIR / 'data.json'

app = Flask(__name__)


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS hosts (hostname TEXT PRIMARY KEY, data TEXT)"
    )
    conn.commit()
    conn.close()


def load_data():
    if DATA_JSON.exists():
        with open(DATA_JSON) as f:
            hosts = json.load(f)
    else:
        hosts = []
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM hosts")
    for h in hosts:
        cur.execute(
            "INSERT OR REPLACE INTO hosts(hostname, data) VALUES(?, ?)",
            (h.get("hostname"), json.dumps(h)),
        )
    conn.commit()
    conn.close()


def get_hosts(search=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if search:
        cur.execute(
            "SELECT data FROM hosts WHERE hostname LIKE ?",
            (f"%{search}%",),
        )
    else:
        cur.execute("SELECT data FROM hosts")
    rows = cur.fetchall()
    conn.close()
    return [json.loads(r[0]) for r in rows]


@app.route('/api/hosts')
def hosts():
    search = None
    # In a real app we would parse request.args for filters and sorting
    hosts_list = get_hosts(search)
    return jsonify(hosts_list)


@app.route('/')
def index():
    index_file = RESULTS_DIR / 'index.html'
    if index_file.exists():
        return send_from_directory(RESULTS_DIR, 'index.html')
    return 'Flask server is running. Use /api/hosts to get data.'


if __name__ == '__main__':
    init_db()
    load_data()
    app.run(host='0.0.0.0', port=5000)
