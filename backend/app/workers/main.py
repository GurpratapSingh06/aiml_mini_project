"""
VEDANTA — Background Worker Entry Point
Starts RQ workers listening on all defined queues.
"""

from __future__ import annotations

import signal
import sys

from app.core.config import settings
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def main():
    """Start the VEDANTA background worker."""
    try:
        import redis
        from rq import Worker, Queue
        from rq.timeouts import JobTimeoutException
    except ImportError:
        logger.error("rq and redis packages required. Install: pip install rq redis")
        sys.exit(1)

    logger.info(
        "VEDANTA Worker starting",
        queues=settings.worker_queues_list,
        redis_url=settings.redis_url,
    )

    try:
        conn = redis.from_url(settings.redis_url)
        conn.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error("Cannot connect to Redis", error=str(e))
        sys.exit(1)

    queues = [Queue(name, connection=conn) for name in settings.worker_queues_list]

    worker = Worker(queues, connection=conn, name="vedanta-worker")

    # Graceful shutdown on SIGTERM
    def _shutdown(signum, frame):
        logger.info("Shutdown signal received — stopping worker gracefully")
        worker.stop()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    logger.info("Worker ready, listening for jobs...")
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
