"""
OpsMesh Worker — entry point.

Start with:
    cd apps/api
    source .venv/bin/activate
    python -m src.opsmesh.worker.run

Or for development with auto-reload on code changes:
    rq worker opsmesh --url redis://localhost:6379/0
"""

import logging
import sys

from redis import Redis
from rq import Worker

from src.opsmesh.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("opsmesh.worker")


def main():
    redis_conn = Redis.from_url(settings.redis_url)

    try:
        redis_conn.ping()
        logger.info("Connected to Redis at %s", settings.redis_url)
    except Exception as e:
        logger.error("Cannot connect to Redis: %s", e)
        sys.exit(1)

    queues = ["opsmesh-critical", "opsmesh-high", "opsmesh-default"]
    logger.info("Starting worker on queues: %s", queues)

    worker = Worker(
        queues=queues,
        connection=redis_conn,
        name="opsmesh-worker-1",
    )
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
