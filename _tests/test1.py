from luxmedhunter.utils.logger_custom import default_logger as logger

try:
    x = 5/0
except Exception as er:
    logger.exception(er)
