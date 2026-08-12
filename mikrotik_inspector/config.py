import logging
import os
import sys

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigdict


class _LevelFilter(logging.Filter):
    def __init__(self, *, allow_over: int | None = None, allow_only: int | None = None):
        super().__init__()
        self.allow_over = allow_over
        self.allow_only = allow_only

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - trivial
        if self.allow_only is not None:
            return record.levelno == self.allow_only
        if self.allow_over is not None:
            return record.levelno >= self.allow_over
        return False


def configure_logging(debug: bool = False) -> logging.Logger:
    """Configure root logging so that:
    - `INFO` level records are written only to stdout
    - `DEBUG` (and all non-INFO levels, e.g. WARNING/ERROR) go to stderr
    This prevents duplication and keeps `INFO` output "plain" on stdout.
    """
    root = logging.getLogger("mikrotik_inspector")
    root.setLevel(logging.DEBUG if debug else logging.INFO)

    # Remove existing handlers to avoid duplicate logging
    for h in root.handlers:
        root.removeHandler(h)

    # stdout handler: only allow INFO level messages
    default_fmt = logging.Formatter("%(message)s")
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.addFilter(_LevelFilter(allow_over=logging.INFO))
    stdout_handler.setFormatter(default_fmt)
    root.addHandler(stdout_handler)

    if debug:
        # stderr handler: allow everything EXCEPT INFO (which goes to stdout)
        debug_fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        debug_handler = logging.StreamHandler(sys.stderr)
        debug_handler.setLevel(logging.DEBUG)

        def onlyDebug(record: logging.LogRecord) -> bool:
            return record.levelno == logging.DEBUG

        # Filter to exclude INFO level - it goes to stdout
        debug_handler.addFilter(onlyDebug)
        debug_handler.setFormatter(debug_fmt)
        root.addHandler(debug_handler)
    return root


class Settings(BaseSettings):
    hostname: str | None = Field(None)
    user: str | None = Field(os.getenv("USER"))

    model_config = SettingsConfigdict(env_prefix="MIKROTIK_")
