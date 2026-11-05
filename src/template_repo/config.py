"""Settings, read from environment variables and from ``.env`` if present."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Settings of the application.

    Attributes
    ----------
    log_level : str
        Level of the root logger, e.g. ``"INFO"`` or ``"DEBUG"``.
    """

    log_level: str = "INFO"


def load_settings() -> Settings:
    """Read the settings from the environment, after loading ``.env`` if present.

    Variables already set in the environment take precedence over ``.env``.

    Returns
    -------
    Settings
        The settings, with the default value for each variable that is not set.
    """
    load_dotenv()
    return Settings(log_level=os.environ.get("LOG_LEVEL", Settings.log_level))
