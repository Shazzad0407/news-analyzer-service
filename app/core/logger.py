from loguru import logger

from app.core.config import settings


class LoggerInstance:

    def __new__(cls):
        """
        LoggerInstance is an object of loguru module.
        It is Used to trace and store various logging information of the API's
        """

        log_format = "{time} | <level>{level}</level> | {message} | {file} | {line} | {function} | {exception}"

        logger.add(
            sink="logs/logfile.log",
            colorize=True,
            format=log_format,
            level=settings.FILE_LOG_LEVEL,
            compression='zip',
            rotation='10 MB',
            encoding='utf-8',
            retention='5 days'
        )

        return logger


logger = LoggerInstance()  # noqa
