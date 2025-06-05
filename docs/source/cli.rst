Command Line Interface
======================

The project provides two entry points: ``collect_and_visualize`` and ``server``.

Run the helper script to collect system facts and generate a small report:

.. code-block:: bash

   python3 -m autoconfig.collect_and_visualize \
     --output-dir results \
     --inventory ansible/hosts.ini \
     --port 8080

Additional options:

``--hosts``
    Comma separated list of hosts to process in parallel. If Ansible is not
    available the script will collect facts over SSH.

``--skip-nginx``
    Collect data only and do not launch nginx.

Run the Flask API directly using ``server``:

.. code-block:: bash

   python3 -m autoconfig.server --port 8000 --results-dir results

Environment variables:

``LOG_LEVEL``
    Adjust verbosity of both commands.

``API_TOKEN``
    Token required for accessing protected API endpoints.
