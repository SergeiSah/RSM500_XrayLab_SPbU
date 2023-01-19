import configparser
import os
from config.definitions import ROOT_DIR


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

    def write_changes_to_settings(self):
        with open(self.path_to_settings_ini, 'w') as configfile:
            self.__config.write(configfile)


if __name__ == '__main__':
    s = Settings()
    print(s.path_to_settings_ini)
