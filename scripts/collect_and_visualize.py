#!/usr/bin/env python3
import json
import os
import subprocess
import sqlite3
import shutil
from pathlib import Path
from jinja2 import Template
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor

level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, level_name, logging.INFO))
logger = logging.getLogger(__name__)

DEFAULT_NGINX_PORT = 8080

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_RESULTS_DIR = BASE_DIR.parent / "results"
DEFAULT_NGINX_CONFIG = DEFAULT_RESULTS_DIR / "nginx.conf"
TEMPLATES_DIR = BASE_DIR / ".." / "templates"
HTML_TEMPLATE_PATH = TEMPLATES_DIR / "index.html.j2"
NGINX_TEMPLATE_PATH = TEMPLATES_DIR / "nginx.conf.j2"
DEFAULT_DB_PATH = DEFAULT_RESULTS_DIR / "data.db"
DEFAULT_INVENTORY = BASE_DIR / ".." / "ansible" / "hosts.ini"

# These variables may be overridden by command line options
RESULTS_DIR = DEFAULT_RESULTS_DIR
NGINX_CONFIG = DEFAULT_NGINX_CONFIG
DB_PATH = DEFAULT_DB_PATH
INVENTORY = DEFAULT_INVENTORY

PLAYBOOK = BASE_DIR / ".." / "ansible" / "collect_facts.yml"


def run_playbook(hosts=None):
    """Run the Ansible playbook if available or collect facts locally."""
    if shutil.which("ansible-playbook"):
        env = os.environ.copy()
        env["OUTPUT_DIR"] = str(RESULTS_DIR)

        def run_host(host):
            cmd = ["ansible-playbook", "-i", str(INVENTORY), str(PLAYBOOK)]
            if host:
                cmd.extend(["--limit", host])
            subprocess.run(cmd, check=True, env=env)

        if hosts:
            with ThreadPoolExecutor() as exc:
                exc.map(run_host, hosts)
        else:
            run_host(None)
    else:
        logger.info("ansible-playbook not found, collecting local facts only")
        if hosts:
            with ThreadPoolExecutor() as exc:
                exc.map(collect_local_facts, hosts)
        else:
            collect_local_facts()


def collect_local_facts(host=None):
    """Collect basic host facts locally or via SSH."""

    def run_cmd(cmd, shell=False):
        if host and host != "localhost":
            if shell:
                remote_cmd = ["ssh", host, cmd]
            else:
                remote_cmd = ["ssh", host] + cmd
            return subprocess.check_output(remote_cmd, text=True)
        return subprocess.check_output(cmd, text=True, shell=shell)

    hostname = run_cmd(["hostname"]).strip()
    users = run_cmd(["getent", "passwd"]).splitlines()
    try:
        ports = run_cmd(["ss", "-tulwn"]).splitlines()
    except FileNotFoundError:
        ports = []
    disk = run_cmd("df -h --output=size,used,avail,pcent / | tail -n 1", shell=True).strip()
    memory = run_cmd("free -m | grep 'Mem:'", shell=True).strip()
    cpu_load = run_cmd(["cat", "/proc/loadavg"]).strip()

    net_stats = run_cmd(["cat", "/proc/net/dev"]).splitlines()

    try:
        sensors_out = run_cmd(["sensors"]).splitlines()
    except FileNotFoundError:
        sensors_out = []

    RESULTS_DIR.mkdir(exist_ok=True)
    data = {
        "hostname": hostname,
        "users": users,
        "ports": ports,
        "disk": disk,
        "memory": memory,
        "cpu_load": cpu_load,
        "net": net_stats,
        "sensors": sensors_out,
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


def parse_args():
    parser = argparse.ArgumentParser(
        description="Collect system facts and serve a small report"
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=str(DEFAULT_RESULTS_DIR),
        help="directory to store collected results",
    )
    parser.add_argument(
        "-i",
        "--inventory",
        default=str(DEFAULT_INVENTORY),
        help="path to Ansible inventory file",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=DEFAULT_NGINX_PORT,
        help="port for the temporary nginx server",
    )
    parser.add_argument(
        "--skip-nginx",
        action="store_true",
        help="collect data only and do not launch nginx",
    )
    parser.add_argument(
        "--hosts",
        type=lambda s: s.split(","),
        help="comma separated list of hosts to process in parallel",
    )
    return parser.parse_args()


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

    logger.info("Report written to %s", output_file)


def generate_nginx_config(port=DEFAULT_NGINX_PORT):
    """Create an nginx config to serve the results directory."""
    config_text = NGINX_TEMPLATE.render(port=port, root=RESULTS_DIR)
    with open(NGINX_CONFIG, "w") as f:
        f.write(config_text)
    return NGINX_CONFIG


def start_nginx(config_path):
    """Start nginx using the generated config if available."""
    try:
        subprocess.run(
            [
                "nginx",
                "-c",
                str(config_path),
                "-p",
                str(RESULTS_DIR),
                "-g",
                "daemon off;",
            ],
            check=True,
        )
    except FileNotFoundError:
        logger.warning(
            "nginx is not installed. Please install nginx to serve the site."
        )


def main():
    args = parse_args()

    global RESULTS_DIR, DB_PATH, NGINX_CONFIG, INVENTORY
    RESULTS_DIR = Path(args.output_dir)
    INVENTORY = Path(args.inventory)
    DB_PATH = RESULTS_DIR / "data.db"
    NGINX_CONFIG = RESULTS_DIR / "nginx.conf"

    RESULTS_DIR.mkdir(exist_ok=True)
    run_playbook(hosts=args.hosts)
    hosts = load_results()
    generate_site(hosts)
    cfg = generate_nginx_config(port=args.port)
    logger.info("nginx configuration written to %s", cfg)
    if args.skip_nginx:
        logger.info("Skipping nginx startup")
        return
    logger.info("Serving results on http://localhost:%s", args.port)
    start_nginx(cfg)


if __name__ == "__main__":
    main()
