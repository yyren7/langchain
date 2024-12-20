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
    # try:
    #     FILE_HANDLER = os.getenv("FILE_HANDLER")
    #     if FILE_HANDLER is True or FILE_HANDLER == "True" or FILE_HANDLER == "true" or FILE_HANDLER == "TRUE":
    #         import datetime
    #         _now = datetime.datetime.now()
    #         _date = _now.strftime("%Y%m&d")
    #         try:
    #             script_dirname = os.path.dirname(__file__)
    #         except Exception:
    #             script_dirname = os.getcwd()
    #         finally:
    #             os.makedirs(script_dirname + "/log/", exist_ok=True)
    #             filename = _date + ".log"
    #             fh = logging.FileHandler(
    #                 script_dirname + "/log/" + filename, 'a+')
    #             logger.addHandler(fh)
    # except Exception:
    #     pass

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
