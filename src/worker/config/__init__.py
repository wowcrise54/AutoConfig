from dataclasses import dataclass
import os


def get_env(name: str, default: str | None = None) -> str:
    return os.environ.get(name, default) or ""


@dataclass
class Settings:
    broker_url: str = get_env("WORKER_BROKER_URL", "amqp://guest:guest@localhost:5672/")
    health_port: int = int(get_env("WORKER_HEALTH_PORT", "8081"))


settings = Settings()
