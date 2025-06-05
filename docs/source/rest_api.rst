REST API
========

The Flask application exposes a small JSON API.

``/api/hosts``
    Return host information. Supports optional query parameters ``search``,
    ``sort`` and ``order``. Requires an ``Authorization`` header containing the
    ``API_TOKEN`` value.

``/api/reload``
    POST endpoint that reloads data from ``results/data.json`` into the
    database. Also protected by ``API_TOKEN``.
