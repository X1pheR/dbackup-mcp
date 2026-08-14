from __future__ import annotations

import asyncio

from .api import DBackupClient
from .config import Settings
from .server import run_stdio
from .service import DBackupService

__version__ = "0.1.0"


def main() -> None:
    settings = Settings.from_env()
    asyncio.run(run_stdio(settings, DBackupService(DBackupClient(settings))))
