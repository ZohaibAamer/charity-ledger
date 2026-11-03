"""Central logging configuration for the extraction pipeline.

Every module obtains its logger through ``get_logger`` so that the
whole pipeline shares one format and level, configurable via the
LOG_LEVEL environment variable.
"""

import logging
import os
import sys

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_configured = False


def get_logger(name: str) -> logging.Logger:
    """Return a logger wired to the shared pipeline configuration."""
    global _configured
    if not _configured:
        logging.basicConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=_FORMAT,
            stream=sys.stdout,
        )
        _configured = True
    return logging.getLogger(name)
