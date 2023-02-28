import time

import keyboard
import serial

from definitions import KEY_FOR_INTERRUPTION
from rsm500.command import Command


class RSMController:
    DELAY = 0.01

    port = None

    @classmethod
    def set_port(cls, port: serial.Serial):
        cls.port = port

    def run_command(self, command: Command, *args: int):
        out_cmd = command.format(*args)

        if self.port is None:
            raise ValueError('RSM500: port is not set')

        self.port.write(out_cmd.encode())
        response = self.__class__.port.read(size=command.response_length)
        result = command.parse(response)
        if len(result) == 1:
            return result[0]
        return result

    def device_status(self):
        return self.run_command(Command('RB', 'B'))

    def device_version(self):
        (high, low) = self.run_command(Command('VS', 'BB'))
        return '{}.{}'.format(high, low)

    def device_reset(self):
        return self.run_command(Command('RS', 'B'))

    def device_get_error(self):
        return self.run_command(Command('RE', 'B'))

    def __repr__(self):
        return f'{self.__class__.__name__}({self.port})'


class Motor(RSMController):
    motor_id = 4    # 4 is non-existent motor

    # def __init__(self, motor_id: int = None):
    #     if motor_id is not None:
    #         self.select(motor_id)

    @classmethod
    def select(cls, motor_id: int):
        cls.motor_id = motor_id
        return super().run_command(Command('SM', 'B', 1), cls.motor_id)

    def status(self):
        return self.run_command(Command('RG', 'B'))

    def initialize(self):
        return self.run_command(Command('GI', 'B'))

    def get_position(self):
        return self.run_command(Command('GP', '>h'))

    def set_position(self, position: int):
        return self.run_command(Command('GW', 'B', 5), position)

    def move(self, direction_id: int, steps: int):
        return self.run_command(Command('GM', 'B', 1, 5), direction_id, steps)

    def stop(self):
        return self.run_command(Command('GB', 'B'))

    def is_moving(self):
        while self.device_status() & 1:
            time.sleep(self.DELAY)
            if keyboard.is_pressed(KEY_FOR_INTERRUPTION):
                self.stop()
                return False
        return True

    def error(self):
        return self.run_command(Command('GE', '>h'))

    def __repr__(self):
        return f'{self.__class__.__name__}({self.motor_id})'


class Detector(RSMController):
    MAX_DETECTORS = 6

    def __init__(self, detector_id: int):
        self.detector_id = detector_id

    def set_threshold(self, threshold_id: int, value: int):
        return self.run_command(Command('TS', 'B', 1, 1, 4), self.detector_id, threshold_id, value)

    def get_threshold(self, threshold_id: int):
        return self.run_command(Command('TG', '>H', 1, 1), self.detector_id, threshold_id)

    def set_exposure(self, value: int):
        return self.run_command(Command('ES', 'B', 4), value)

    def start_count(self):
        return self.run_command(Command('CS', 'B'))

    def stop_count(self):
        return self.run_command(Command('CB', 'B'))

    def is_counting(self):
        while self.get_remaining_exposure() > 0:
            time.sleep(self.DELAY)
            if keyboard.is_pressed(KEY_FOR_INTERRUPTION):
                self.stop_count()
                return False
        return True

    def read_detector_count(self):
        return self.run_command(Command('CG', '>I', 1), self.detector_id)

    def get_remaining_exposure(self):
        return self.run_command(Command('EG', '>H'))

    def set_voltage_on_photocathode(self, voltage: int):
        return self.run_command(Command('DS', 'B', 1, 4), self.detector_id, voltage)

    def get_voltage_on_photocathode(self):
        return self.run_command(Command('DG', '>H', 1), self.detector_id)

    def enable_photocathode(self, is_enabled: bool):
        en_val = 1 if is_enabled else 0
        return self.run_command(Command('DM', 'B', 1, 1), self.detector_id, en_val)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.detector_id})'
