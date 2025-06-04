#!/usr/bin/env python3
import json
import os
import subprocess
from pathlib import Path
from jinja2 import Template

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"

PLAYBOOK = BASE_DIR / "ansible" / "collect_facts.yml"
INVENTORY = BASE_DIR / "ansible" / "hosts.ini"


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


HTML_TEMPLATE = Template(
    """
    <html>
    <head>
        <meta charset='utf-8'>
        <title>System Facts</title>
        <style>
            body { font-family: Arial, sans-serif; }
            h2 { border-bottom: 1px solid #ccc; }
            ul { list-style-type: none; padding: 0; }
            li { margin: 0.2em 0; }
        </style>
    </head>
    <body>
    <h1>Collected System Facts</h1>
    {% for host in hosts %}
        <h2>{{ host.hostname }}</h2>
        <h3>Users</h3>
        <ul>
        {% for user in host.users %}
            <li>{{ user }}</li>
        {% endfor %}
        </ul>
        <h3>Listening Ports</h3>
        <ul>
        {% for port in host.ports %}
            <li>{{ port }}</li>
        {% endfor %}
        </ul>
    {% endfor %}
    </body>
    </html>
    """
)


def generate_html(hosts):
    html = HTML_TEMPLATE.render(hosts=hosts)
    output_file = RESULTS_DIR / "index.html"
    with open(output_file, "w") as f:
        f.write(html)
    print(f"Report written to {output_file}")


if __name__ == "__main__":
    RESULTS_DIR.mkdir(exist_ok=True)
    run_playbook()
    hosts = load_results()
    generate_html(hosts)
