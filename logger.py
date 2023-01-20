import logging
import logging.config

from definitions import *


class LogHandler:
    def __init__(self):
        logging.config.fileConfig(f'{ROOT_DIR}/config/loggers_config.ini')
        self.logger = logging.getLogger('root')

    def set_level(self, handler_name):
        pass
