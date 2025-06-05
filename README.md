# AutoConfig

This project demonstrates how to collect system facts from hosts using Ansible
and render the results in a small React application. The playbook gathers the
list of system users and listening network ports, then saves the collected data
as JSON. A Python helper script runs the playbook and generates a React based
web page that displays the results.

## Requirements
- Python 3
- Ansible
- Jinja2 (installed automatically with Ansible)
- nginx (optional, installed automatically by `setup.sh`)

## Setup
Run the provided helper script to automatically install the necessary packages:

```bash
./setup.sh
```

## Usage
Run the helper script which will invoke the playbook, generate a small React
site in the `results` directory and launch a local nginx server to serve it
remotely:

```bash
python3 collect_and_visualize.py
```

After the script completes, visit `http://localhost:8080` to view the collected
information. The page will load `data.json` from the same directory and display
the facts in a neat table rendered by React.
The nginx configuration file is written to `results/nginx.conf`.
