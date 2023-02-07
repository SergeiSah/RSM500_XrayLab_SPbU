import configparser

from config.definitions import *


class Settings:
    path_to_settings_ini = os.path.join(ROOT_DIR, r'config\settings.ini')

    def __init__(self):
        self.__config = configparser.ConfigParser()
        self.__config.read(self.path_to_settings_ini)

    @property
    def port(self):
        return self.__config['DEFAULT']['port']

    @port.setter
    def port(self, value: str):
        self.__config['DEFAULT']['port'] = value
        self.write_changes_to_settings()

    @property
    def baudrate(self):
        return self.__config['DEFAULT']['baudrate']

    @baudrate.setter
    def baudrate(self, value):
        self.__config['DEFAULT']['baudrate'] = value
        self.write_changes_to_settings()

    @property
    def path_for_files_save(self):
        return self.__config['PATHS']['path_for_files_save']

    @path_for_files_save.setter
    def path_for_files_save(self, path: str):
        self.__config['PATHS']['path_for_files_save'] = path
        self.write_changes_to_settings()

    # absolute positions of the motors 1, 2, 3
    @property
    def apos_motor_1(self):
        return self.__config['ABS_MOTOR_POSITIONS']['motor_1']

    @apos_motor_1.setter
    def apos_motor_1(self, value):
        self.__config['ABS_MOTOR_POSITIONS']['motor_1'] = value
        self.write_changes_to_settings()

    @property
    def apos_motor_2(self):
        return self.__config['ABS_MOTOR_POSITIONS']['motor_2']

    @apos_motor_2.setter
    def apos_motor_2(self, value):
        self.__config['ABS_MOTOR_POSITIONS']['motor_2'] = value
        self.write_changes_to_settings()

    @property
    def apos_motor_3(self):
        return self.__config['ABS_MOTOR_POSITIONS']['motor_3']

    @apos_motor_3.setter
    def apos_motor_3(self, value):
        self.__config['ABS_MOTOR_POSITIONS']['motor_3'] = value
        self.write_changes_to_settings()

    def write_changes_to_settings(self):
        with open(self.path_to_settings_ini, 'w') as configfile:
            self.__config.write(configfile)

    def change_motor_apos(self, motor_num: int, value: int):
        if motor_num == MOTOR_1:
            self.apos_motor_1 = str(int(self.apos_motor_1) + value)
        elif motor_num == MOTOR_2:
            self.apos_motor_2 = str(int(self.apos_motor_2) + value)
        elif motor_num == MOTOR_3:
            self.apos_motor_2 = str(int(self.apos_motor_3) + value)
        return 0

    def get_motor_apos(self, motor_num: int) -> str:
        return {
            MOTOR_1: self.apos_motor_1,
            MOTOR_2: self.apos_motor_2,
            MOTOR_3: self.apos_motor_3
        }[motor_num]
