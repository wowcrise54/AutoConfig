#!/usr/bin/env python3
import json
import os
import subprocess
from pathlib import Path
from jinja2 import Template

NGINX_PORT = 8080

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
NGINX_CONFIG = RESULTS_DIR / "nginx.conf"

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
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ccc; padding: 0.5em; text-align: left; }
            th { background: #f0f0f0; }
            ul { list-style-type: none; padding: 0; margin: 0; }
            li { margin: 0.2em 0; }
        </style>
    </head>
    <body>
        <div id="root"></div>
        <script type="text/babel">
        fetch('data.json')
          .then(response => response.json())
          .then(data => {
            function HostRow({host}) {
                return (
                  <tr>
                    <td>{host.hostname}</td>
                    <td>
                      <ul>
                        {host.users.map((u, i) => <li key={i}>{u}</li>)}
                      </ul>
                    </td>
                    <td>
                      <ul>
                        {host.ports.map((p, i) => <li key={i}>{p}</li>)}
                      </ul>
                    </td>
                  </tr>
                );
            }

            function App() {
                return (
                  <div>
                    <h1>Collected System Facts</h1>
                    <table>
                      <thead>
                        <tr>
                          <th>Host</th>
                          <th>Users</th>
                          <th>Listening Ports</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.map((h, i) => <HostRow key={i} host={h} />)}
                      </tbody>
                    </table>
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

NGINX_TEMPLATE = Template(
    """
events {}
http {
    server {
        listen {{ port }};
        server_name _;
        root {{ root }};
        location / {
            try_files $uri $uri/ =404;
        }
    }
}
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
