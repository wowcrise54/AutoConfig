#!/usr/bin/env bash
# Collect host data and launch the application using docker-compose
set -e

python3 -m autoconfig.collect_and_visualize \
  --output-dir results \
  --inventory ansible/hosts.ini \
  --skip-nginx

# build and start the compose stack
exec docker-compose up --build
