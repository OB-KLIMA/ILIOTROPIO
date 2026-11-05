"""Command-line interface: entry point of the ``iliotropio`` command."""

import logging

from iliotropio.config import load_settings


logger = logging.getLogger(__name__)


def main() -> None:
    """Set up logging and log a greeting. Entry point of the ``iliotropio`` command."""
    settings = load_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger.info("Hello from iliotropio!")
