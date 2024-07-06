import logging
import logging.config
import os

from .config import *


class LogHandler:
    __instance = None

    # realisation of singleton pattern
    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(LogHandler, cls).__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self):
        logging.config.fileConfig(os.path.join(ROOT_DIR, SETTINGS_DIR, 'loggers_config.ini'))
        self.logger = logging.getLogger('root')
        # set format for stream handler
        self.logger.handlers[1].setFormatter(StreamFormatter('%(levelname)7s: %(message)s'))

    # def set_level(self, handler_name):
    #     self.logger.setLevel(logging.INFO)


class StreamFormatter(logging.Formatter):
    """Logging colored formatter, adapted from https://stackoverflow.com/a/56944256/3638629"""

    grey = "\x1b[38;20m"
    blue = '\x1b[38;5;39m'
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = '\x1b[0m'

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
