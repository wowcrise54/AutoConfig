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
remotely. If `ansible-playbook` is not available the script will collect facts
from the local machine only so it can be used for quick testing without a full
Ansible setup:

```bash
python3 scripts/collect_and_visualize.py
```

After the script completes, visit `http://localhost:8080` to view the collected
information. The page now loads host information via a small Flask API instead
of reading a static JSON file. The React interface supports searching, sorting
by columns and filtering by CPU load. Data refreshes automatically every
30&nbsp;seconds without reloading the page. The nginx configuration file is
written to `results/nginx.conf`.

Alternatively you can run the API directly using:

```bash
python3 server.py
```

The API listens on port 5000 by default and serves host data from the
`results` directory using a lightweight SQLite database. Be sure to run the
helper script at least once so that the `results` directory is populated.
