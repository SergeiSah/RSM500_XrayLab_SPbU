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
        """
        Initialize RSM controller.

        :param port: serial port object
        :return: None
        """
        cls.port = port

    def run_command(self, command: Command, *args: int):
        """
        Run command on the RSM controller.

        :param command: Command object
        :param args: arguments to be passed to the command
        :return: result of the command
        """
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
        """
        Read status byte. The contents of this byte shows which devices of the spectrometer are "busy" at the given
        moment of time - that is, they "transition" from one stable state to another.

        - &h80 - Presence of an error.
        - &h40 - X-ray tube mode is setting.
        - &h20 - The detector is turning on.
        - &h10 - Pulse counters are enabled.
        - &h08 - The controller is busy writing parameters "to disk", no commands are accepted.
        - &h04 - Filter changer or crystal changer is working.
        - &h02 - Sample changer is working.
        - &h01 - The motor is working.

        :return: 1 byte
        """
        return self.run_command(Command('RB', 'B'))

    def device_version(self):
        """
        Reading the version number of the controller program.

        :return: Returns 2 bytes. The high byte is the "high" part of the version number, the low byte is the low one.
        """
        (high, low) = self.run_command(Command('VS', 'BB'))
        return '{}.{}'.format(high, low)

    def device_reset(self):
        """
        Software reset of the controller. All movements are interrupted and the detectors turn off "to zero".

        :return: Error code 1 byte
        """
        return self.run_command(Command('RS', 'B'))

    def device_get_error(self):
        """
        Read error byte.

        :return: Last error code (1 byte). If there are no errors, it returns zero.
        """
        return self.run_command(Command('RE', 'B'))

    def __repr__(self):
        return f'{self.__class__.__name__}, port={self.port}'


class Motor(RSMController):
    motor_id = 4    # 4 is non-existent motor

    def __init__(self, motor_id: int = None):
        if motor_id is not None:
            self.select(motor_id)

    def select(self, motor_id: int):
        """
        Select motor.

        Identifiers:
        - 0 - energy
        - 1 - theta angle of the sample holder
        - 2 - 2theta angle of the second detector
        - 3 - shift of the sample holder along y-axis
        - 4 - remove voltage from a motor

        :param motor_id: motor identifier (0-4)
        :return: Error code (1 byte)
        """
        self.__class__.motor_id = motor_id
        return self.run_command(Command('SM', 'B', 1), self.motor_id)

    def status(self):
        """
        Reading of the motor status.

        - &h80 - presence of an error
        - &h40 - Indicates that the cross flag is overridden (if the bit is NOT SET, the flag is overridden)
        - &h20 - indicates that the longitudinal flag is overridden (if the bit is NOT SET, the flag is overridden)
        - &h10 - ...
        - &h08 - "main" is the upper trailer (not necessary)
        - &h04 - availability of goniometer initialization
        - &h02 - if this bit is NOT SET, the upper limit switch is triggered
        - &h01 - if this bit is NOT SET, the lower limit switch is triggered

        :return: 1 byte
        """
        return self.run_command(Command('RG', 'B'))

    def initialize(self):
        """
        Initialization of the motor - the motor is moved to the main limit switch and its position is set to zero.

        :return: Error code (1 byte)
        """
        return self.run_command(Command('GI', 'B'))

    def get_position(self):
        """
        Reading the position of the motor.

        :return: Current motor position (2 bytes) - signed integer
        """
        return self.run_command(Command('GP', '>h'))

    def set_position(self, position: int):
        """
        Recording the position of the motor. The number nnnnn is written into the motor position counter.
        The initialization flag is reset.

        :param position: Numerical representation of the position to be set
        :return: Error code (1 byte)
        """
        return self.run_command(Command('GW', 'B', 5), position)

    def move(self, direction_id: int, steps: int):
        """
        Move the motor on nnnnn steps in direction d.

        :param direction_id: Direction of motor rotation
        :param steps: Number of steps, no more than 32768
        :return: Error code (1 byte)
        """
        return self.run_command(Command('GM', 'B', 1, 5), direction_id, steps)

    def stop(self):
        """
        Interrupting the movement of the motor. Current position is not reset.

        :return: Error code (1 byte)
        """
        return self.run_command(Command('GB', 'B'))

    def is_moving(self):
        """
        Wait while motor is moving.

        :return: If interrupted - False, else True
        """
        while self.device_status() & 1:
            time.sleep(self.DELAY)
            if keyboard.is_pressed(KEY_FOR_INTERRUPTION):
                self.stop()
                return False
        return True

    def error(self):
        """
        Reading the value of the step counter mismatch during re-initialization. Returns the value of the counter of
        motor steps at the moment of reaching the home position sensor (2 bytes) - a signed integer. If initialization
        was not carried out or it is the first one after switching on, it returns 0.
        For a serviceable motor with an accurate limit switch, this modulo value should not exceed 2.

        :return: The value of the steps counter
        """
        return self.run_command(Command('GE', '>h'))

    def __repr__(self):
        return f'{self.__class__.__name__}({self.motor_id})'


class Detector(RSMController):
    MAX_DETECTORS = 6

    def __init__(self, detector_id: int):
        self.detector_id = detector_id

    def set_threshold(self, threshold_id: int, value: int):
        """
        Set one detector threshold.

        :param threshold_id: Threshold identifier (0 - bottom, 1 - up)
        :param value: Threshold value
        :return: Error code (1 byte)
        """
        return self.run_command(Command('TS', 'B', 1, 1, 4), self.detector_id, threshold_id, value)

    def get_threshold(self, threshold_id: int):
        """
        Get one detector threshold.

        :param threshold_id: Threshold (0 - bottom, 1 - up)
        :return: Error code (1 byte)
        """
        return self.run_command(Command('TG', '>H', 1, 1), self.detector_id, threshold_id)

    def set_exposure(self, value: int):
        """
        Set exposure for counting pulses in all the detectors.

        :param value: Exposure value in tenths of a second (0 - 9999). If zero exposure is set, the counters
        immediately (without the ''counter_start' command) are switched on to the continuous operation mode
        :return: Error code (1 byte)
        """
        return self.run_command(Command('ES', 'B', 4), value)

    def start_count(self):
        """
        Starting a count. Turns on all counters for the specified exposure time ('exposure_set' command).

        :return: Error code (1 byte)
        """
        return self.run_command(Command('CS', 'B'))

    def stop_count(self):
        """
        Count interruption. Stops all counters. The contents of the counters are not reset.

        :return: Error code (1 byte)
        """
        return self.run_command(Command('CB', 'B'))

    def is_counting(self):
        """
        Wait while counter is working during set exposure time.

        :return: If interrupted - False, else True
        """
        while self.get_remaining_exposure() > 0:
            time.sleep(self.DELAY)
            if keyboard.is_pressed(KEY_FOR_INTERRUPTION):
                self.stop_count()
                return False
        return True

    def read_detector_count(self):
        """
        Reading the result of the count (a set of pulses) in the specified channel.

        :return: 4 bytes, unsigned integer
        """
        return self.run_command(Command('CG', '>I', 1), self.detector_id)

    def get_remaining_exposure(self):
        """
        Reading the current exposure. When the counters are running continuously, the command returns the "hardware"
        time (in milliseconds) that has elapsed since the start of the counters. With the counters running normally,
        the command still returns the remaining exposure in tenths of a second.

        :return: 2 bytes - the value of the "remaining" exposure in tenths of a second.
        """
        return self.run_command(Command('EG', '>H'))

    def set_voltage_on_photocathode(self, voltage: int):
        """
        Set the desired voltage on the photocathode of the detector.

        :param voltage: Voltage on the photocathode of the detector
        :return: Error code (1 byte)
        """
        return self.run_command(Command('DS', 'B', 1, 4), self.detector_id, voltage)

    def get_voltage_on_photocathode(self):
        """
        Read the current voltage on the photocathode of the detector.

        :return: Photocathode voltage (2 bytes, unsigned integer)
        """
        return self.run_command(Command('DG', '>H', 1), self.detector_id)

    def enable_photocathode(self, is_enabled: bool):
        """
        Enable or disable the photocathode for the specified detector. If 'disable', the detector will turn off, that
        is, the standby voltage will be set on it from the parameters #Dn.IV. If 'enable', the voltage set in the last
        command (#Dn.IV) will be set on the detector. If no 'photocathode_set_voltage' command has been received since
        the device was turned on or the 'device_reset' command was issued, the operating voltage from the device
        parameters (#Dn. WV).

        :param is_enabled: True or False
        :return: Error code (1 byte)
        """
        en_val = 1 if is_enabled else 0
        return self.run_command(Command('DM', 'B', 1, 1), self.detector_id, en_val)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.detector_id})'
