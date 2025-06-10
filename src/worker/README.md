# Worker Service

This worker listens for simulation messages and runs scenario plugins.

## Development

Create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the worker in development mode:

```bash
export WORKER_BROKER_URL="amqp://guest:guest@localhost:5672/"
python -m worker.cmd.main
```

The service exposes a health check on `http://localhost:8081/health`.
