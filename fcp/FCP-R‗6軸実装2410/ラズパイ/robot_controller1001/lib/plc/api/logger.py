import os
import logging
import dotenv


def get_module_logger(modname):
    logger = logging.getLogger(modname)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s-%(name)s-%(levelname)s-%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    dotenv.load_dotenv(override=True)
    LOGGER_LEVEL = os.getenv('LOGGER_LEVEL')
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
