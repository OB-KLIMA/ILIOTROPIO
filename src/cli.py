"""Command-line interface: entry point of the ``template-repo`` command."""

import logging

from template_repo.config import load_settings


logger = logging.getLogger(__name__)


def main() -> None:
    """Set up logging and log a greeting. Entry point of the ``template-repo`` command."""
    settings = load_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger.info("Hello from template-repo!")
