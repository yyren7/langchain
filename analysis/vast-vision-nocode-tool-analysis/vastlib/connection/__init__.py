import logging
import os
import dotenv


def get_module_logger(modname, *, level=None):
    logger = logging.getLogger(modname)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        'Time:%(asctime)s, %(name)s, Level:%(levelname)s, Func:%(funcName)s, Line:%(lineno)s, %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    dotenv.load_dotenv(override=True)
    if level is None:
        LOGGER_LEVEL = os.getenv('LOGGER_LEVEL')
    elif level in ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]:
        LOGGER_LEVEL = level
    else:
        LOGGER_LEVEL = "INFO"

    if (LOGGER_LEVEL == 'CRITICAL'):
        logger.setLevel(logging.CRITICAL)
    elif (LOGGER_LEVEL == 'ERROR'):
        logger.setLevel(logging.ERROR)
    elif (LOGGER_LEVEL == 'WARNING'):
        logger.setLevel(logging.WARNING)
    elif (LOGGER_LEVEL == 'INFO'):
        logger.setLevel(logging.INFO)
    elif (LOGGER_LEVEL == 'DEBUG'):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.NOTSET)
    return logger
