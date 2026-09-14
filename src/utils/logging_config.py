import os
import sys

from loguru import logger


def setup_logging():
    """Configure un logging double canal :

    - stderr : format lisible par l'humain pour l'exploitation ;
    - audit.log : lignes JSON structurées uniquement (journal d'audit A.6),
      via le sink dédié déclaré dans :mod:`src.security.audit`.
    """
    logger.remove()
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | {message}",
        level=level,
        colorize=True,
    )
    return logger