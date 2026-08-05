"""Registro y métricas para operaciones de respaldo y restauración."""

import logging

logger = logging.getLogger("openlp_vault")


def setup_logging(level=logging.INFO):
    handler = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.setLevel(level)
