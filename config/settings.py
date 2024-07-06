import configparser

from .definitions import *


class Settings:
    path_to_settings_ini = os.path.join(ROOT_DIR, r'config\settings.ini')

    def __init__(self):
        self._config = configparser.ConfigParser()
        self._config.read(self.path_to_settings_ini)

    @property
    def port(self):
        return self._config['CONTROLLER_CONNECTION']['port']

    @port.setter
    def port(self, value: str):
        self._config['CONTROLLER_CONNECTION']['port'] = value
        self.save_changes()

    @property
    def baudrate(self):
        return self._config['CONTROLLER_CONNECTION']['baudrate']

    @baudrate.setter
    def baudrate(self, value: int):
        self._config['CONTROLLER_CONNECTION']['baudrate'] = str(value)
        self.save_changes()

    @property
    def path_to_datafiles(self):
        return self._config['PATHS']['path_to_datafiles']

    @path_to_datafiles.setter
    def path_to_datafiles(self, path: str):
        self._config['PATHS']['path_to_datafiles'] = path
        self.save_changes()

    def get_abs_motor_position(self, motor_num: int) -> int:
        return int(self._config['ABSOLUTE_MOTOR_POSITION'][f'motor_{motor_num}'])

    def set_abs_motor_position(self, motor_num: int, value: int) -> None:
        self._config['ABSOLUTE_MOTOR_POSITION'][f'motor_{motor_num}'] = \
            str(int(self._config['ABSOLUTE_MOTOR_POSITION'][f'motor_{motor_num}']) + value)
        self.save_changes()

    def get_limits(self, motor_num: int) -> tuple:
        return tuple(map(int, self._config['LIMITS'][f'motor_{motor_num}'].split(' ')))

    def save_changes(self):
        with open(self.path_to_settings_ini, 'w') as configfile:
            self._config.write(configfile)