#!/usr/bin/env python3
import json
import os
import subprocess
from pathlib import Path
from jinja2 import Template

NGINX_PORT = 8080

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR.parent / "results"
NGINX_CONFIG = RESULTS_DIR / "nginx.conf"
TEMPLATES_DIR = BASE_DIR / ".." / "templates"
HTML_TEMPLATE_PATH = TEMPLATES_DIR / "index.html.j2"
NGINX_TEMPLATE_PATH = TEMPLATES_DIR / "nginx.conf.j2"

PLAYBOOK = BASE_DIR / ".." / "ansible" / "collect_facts.yml"
INVENTORY = BASE_DIR / ".." / "ansible" / "hosts.ini"


def run_playbook():
    env = os.environ.copy()
    env["OUTPUT_DIR"] = str(RESULTS_DIR)
    subprocess.run([
        "ansible-playbook",
        "-i",
        str(INVENTORY),
        str(PLAYBOOK)
    ], check=True, env=env)


def load_results():
    hosts = []
    for path in RESULTS_DIR.glob("facts_*.json"):
        with open(path, "r") as f:
            data = json.load(f)
            hosts.append(data)
    return hosts


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
