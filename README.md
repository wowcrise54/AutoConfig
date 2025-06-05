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

## Setup
Run the provided helper script to automatically install the necessary packages:

```bash
./setup.sh
```

## Usage
Run the helper script which will invoke the playbook and generate a small React
site in the `results` directory:

```bash
python3 collect_and_visualize.py
```

Open `results/index.html` in a browser to view the collected information. The
page will load `data.json` from the same directory and display the facts using
React.
