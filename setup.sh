#!/usr/bin/env bash
set -e

# Simple environment setup script for local testing
# Installs Ansible and required packages using apt if they are not already present

if ! command -v ansible >/dev/null; then
    sudo apt-get update
    sudo apt-get install -y ansible
fi

if ! command -v ss >/dev/null; then
    sudo apt-get install -y iproute2
fi

# Install nginx for serving the results
if ! command -v nginx >/dev/null; then
    sudo apt-get install -y nginx
fi

# Install pip and the Jinja2 package used by the helper script
if ! command -v pip3 >/dev/null; then
    sudo apt-get install -y python3-pip
fi

if ! python3 -c 'import jinja2' 2>/dev/null; then
    pip3 install --break-system-packages Jinja2
fi

# Install python3 if missing (usually preinstalled)
if ! command -v python3 >/dev/null; then
    sudo apt-get install -y python3
fi

# Provide message about running the main script
echo "Environment configured. You can now run: python3 collect_and_visualize.py"

