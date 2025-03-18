import logging
import sys

from pythonjsonlogger import jsonlogger


def get_logger(name=__name__, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    logHandler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d"
    )
    logHandler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(logHandler)
    logger.propagate = False

    return logger
