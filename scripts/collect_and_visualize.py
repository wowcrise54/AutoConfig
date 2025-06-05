#!/usr/bin/env python3
import json
import os
import subprocess
import sqlite3
import shutil
from pathlib import Path
from jinja2 import Template

NGINX_PORT = 8080

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR.parent / "results"
NGINX_CONFIG = RESULTS_DIR / "nginx.conf"
TEMPLATES_DIR = BASE_DIR / ".." / "templates"
HTML_TEMPLATE_PATH = TEMPLATES_DIR / "index.html.j2"
NGINX_TEMPLATE_PATH = TEMPLATES_DIR / "nginx.conf.j2"
DB_PATH = RESULTS_DIR / "data.db"

PLAYBOOK = BASE_DIR / ".." / "ansible" / "collect_facts.yml"
INVENTORY = BASE_DIR / ".." / "ansible" / "hosts.ini"


def run_playbook():
    """Run the Ansible playbook if available or collect facts locally."""
    if shutil.which("ansible-playbook"):
        env = os.environ.copy()
        env["OUTPUT_DIR"] = str(RESULTS_DIR)
        subprocess.run([
            "ansible-playbook",
            "-i",
            str(INVENTORY),
            str(PLAYBOOK)
        ], check=True, env=env)
    else:
        print("ansible-playbook not found, collecting local facts only")
        collect_local_facts()


def collect_local_facts():
    """Collect basic host facts without Ansible."""
    hostname = subprocess.check_output(["hostname"], text=True).strip()
    users = subprocess.check_output(["getent", "passwd"], text=True).splitlines()
    try:
        ports = subprocess.check_output(["ss", "-tulwn"], text=True).splitlines()
    except FileNotFoundError:
        ports = []
    disk = subprocess.check_output(
        "df -h --output=size,used,avail,pcent / | tail -n 1",
        shell=True,
        text=True,
    ).strip()
    memory = subprocess.check_output(
        "free -m | grep 'Mem:'",
        shell=True,
        text=True,
    ).strip()
    cpu_load = subprocess.check_output(["cat", "/proc/loadavg"], text=True).strip()

    RESULTS_DIR.mkdir(exist_ok=True)
    data = {
        "hostname": hostname,
        "users": users,
        "ports": ports,
        "disk": disk,
        "memory": memory,
        "cpu_load": cpu_load,
    }
    with open(RESULTS_DIR / f"facts_{hostname}.json", "w") as f:
        json.dump(data, f, indent=2)


def load_results():
    hosts = []
    for path in RESULTS_DIR.glob("facts_*.json"):
        with open(path, "r") as f:
            data = json.load(f)
            hosts.append(data)
    return hosts


def save_to_db(hosts):
    """Store hosts data in a small SQLite database for the API."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS hosts (hostname TEXT PRIMARY KEY, data TEXT)"
        )
        cur.execute("DELETE FROM hosts")
        for h in hosts:
            cur.execute(
                "INSERT OR REPLACE INTO hosts(hostname, data) VALUES(?, ?)",
                (h.get("hostname"), json.dumps(h)),
            )


with open(HTML_TEMPLATE_PATH, "r") as f:
    HTML_TEMPLATE = Template(f.read())

with open(NGINX_TEMPLATE_PATH, "r") as f:
    NGINX_TEMPLATE = Template(f.read())


def generate_site(hosts):
    """Generate the React web site and JSON data."""
    html = HTML_TEMPLATE.render()
    output_file = RESULTS_DIR / "index.html"
    with open(output_file, "w") as f:
        f.write(html)

    data_file = RESULTS_DIR / "data.json"
    with open(data_file, "w") as f:
        json.dump(hosts, f, indent=2)

    save_to_db(hosts)

    print(f"Report written to {output_file}")


def generate_nginx_config(port=NGINX_PORT):
    """Create an nginx config to serve the results directory."""
    config_text = NGINX_TEMPLATE.render(port=port, root=RESULTS_DIR)
    with open(NGINX_CONFIG, "w") as f:
        f.write(config_text)
    return NGINX_CONFIG


def start_nginx(config_path):
    """Start nginx using the generated config if available."""
    try:
        subprocess.run([
            "nginx",
            "-c",
            str(config_path),
            "-p",
            str(RESULTS_DIR),
            "-g",
            "daemon off;",
        ], check=True)
    except FileNotFoundError:
        print("nginx is not installed. Please install nginx to serve the site.")


if __name__ == "__main__":
    RESULTS_DIR.mkdir(exist_ok=True)
    run_playbook()
    hosts = load_results()
    generate_site(hosts)
    cfg = generate_nginx_config()
    print(f"nginx configuration written to {cfg}")
    print(f"Serving results on http://localhost:{NGINX_PORT}")
    start_nginx(cfg)
