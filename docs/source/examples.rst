Examples
========

Simple example showing how to query the API for the list of hosts using
``curl`` with an authentication token:

.. code-block:: bash

   API_TOKEN=secret
   curl -H "Authorization: Bearer $API_TOKEN" \
        http://localhost:5000/api/hosts
