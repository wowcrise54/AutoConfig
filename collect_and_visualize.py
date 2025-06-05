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
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset='utf-8'>
        <title>System Facts</title>
        <script crossorigin src="https://unpkg.com/react@17/umd/react.production.min.js"></script>
        <script crossorigin src="https://unpkg.com/react-dom@17/umd/react-dom.production.min.js"></script>
        <script crossorigin src="https://unpkg.com/babel-standalone@6/babel.min.js"></script>
        <style>
            body { font-family: Arial, sans-serif; }
            h2 { border-bottom: 1px solid #ccc; }
            ul { list-style-type: none; padding: 0; }
            li { margin: 0.2em 0; }
        </style>
    </head>
    <body>
        <div id="root"></div>
        <script type="text/babel">
        fetch('data.json')
          .then(response => response.json())
          .then(data => {
            function Host({host}) {
                return (
                  <div>
                    <h2>{host.hostname}</h2>
                    <h3>Users</h3>
                    <ul>
                      {host.users.map((u, i) => <li key={i}>{u}</li>)}
                    </ul>
                    <h3>Listening Ports</h3>
                    <ul>
                      {host.ports.map((p, i) => <li key={i}>{p}</li>)}
                    </ul>
                  </div>
                );
            }

            function App() {
                return (
                  <div>
                    <h1>Collected System Facts</h1>
                    {data.map((h, i) => <Host key={i} host={h} />)}
                  </div>
                );
            }

            ReactDOM.render(<App />, document.getElementById('root'));
          });
        </script>
    </body>
    </html>
    """
)


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


if __name__ == "__main__":
    RESULTS_DIR.mkdir(exist_ok=True)
    run_playbook()
    hosts = load_results()
    generate_site(hosts)
