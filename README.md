# AutoConfig

This project demonstrates how to collect system facts from hosts using Ansible
and render the results in a small React application. The playbook gathers the
list of system users, listening network ports and several basic metrics such as
CPU load, memory usage and disk space. The collected data is saved as JSON. A
Python helper script located in the `scripts/` directory runs the playbook and
generates a web page using templates stored in `templates/`.

## Requirements
- Python 3
- Ansible
- Jinja2 (installed automatically with Ansible)
- nginx (optional, installed automatically by `setup.sh`)
- See `requirements.txt` for the full Python dependencies

## Setup
Run the provided helper script to automatically install the necessary packages
and Python requirements:

```bash
./setup.sh
pip3 install -r requirements.txt
```

## Usage
Run the helper script which will invoke the playbook, generate a small React
site in the `results` directory and launch a local nginx server to serve it
remotely:

```bash
python3 scripts/collect_and_visualize.py
```

After the script completes, visit `http://localhost:8080` to view the collected
information. The page will load `data.json` from the same directory and display
the facts using React. The interface is styled with the Bootstrap framework for
a clean tabular layout.
The nginx configuration file is written to `results/nginx.conf`.
