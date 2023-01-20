from command import Command
from handlers import arguments_type_checker_in_class
import time
import keyboard
from config.definitions import KEY_FOR_INTERRUPTION
import logging
import serial


class Bucket(object):
    MAX_COUNTERS = 6

    def __init__(self, port: serial.Serial):
        """

        :param port: serial port object
        """
        logging.debug('RSM500: init with port %s', port.name)
        self.port = port

    @arguments_type_checker_in_class
    def run_command(self, command: Command, *args: int):
        out_cmd = command.format(*args)
        self.port.write(out_cmd.encode())
        response = self.port.read(size=command.response_length)
        result = command.parse(response)
        if len(result) == 1:
            return result[0]
        return result

    @arguments_type_checker_in_class
    def motor_move(self, direction: int, steps: int):
        """
        Move the motor on nnnnn steps in direction d.

        :param direction: Direction of motor rotation
        :param steps: Number of steps, no more than 32768
        :return: Error code (1 byte)
        """
        assert direction in [0, 1]
        assert 0 <= steps < 32768

        error = self.run_command(Command('GM', 'B', 1, 5), direction, steps)
        return error

    @arguments_type_checker_in_class
    def motor_select(self, motor_id: int):
        return self.run_command(Command('SM', 'B', 1), motor_id) 
        
    def motor_status(self):
        """
        Reading of the motor status.
        &h80 - presence of an error
        &h40 - Indicates that the cross flag is overridden (if the bit is NOT SET, the flag is overridden)
        &h20 - indicates that the longitudinal flag is overridden (if the bit is NOT SET, the flag is overridden)
        &h10 - ...
        &h08 - "main" is the upper trailer (not necessary)
        &h04 - availability of goniometer initialization
        &h02 - if this bit is NOT SET, the upper limit switch is triggered
        &h01 - if this bit is NOT SET, the lower limit switch is triggered

        :return: 1 byte
        """
        return self.run_command(Command('RG', 'B'))

    def motor_initialize(self):
        """
        Initialization of the motor - the motor is moved to the main limit switch and its position is set to zero.

        :return: Error code (1 byte)
        """
        return self.run_command(Command('GI', 'B'))

    def motor_get_position(self):
        """
        Reading the position of the motor.

        :return: Current motor position (2 bytes) - signed integer
        """
        return self.run_command(Command('GP', '>h'))

    @arguments_type_checker_in_class
    def motor_set_position(self, position: int):
        """
        Recording the position of the motor. The number nnnnn is written into the motor position counter.
        The initialization flag is reset.

        :param position: Numerical representation of the position to be set
        :return: Error code (1 byte)
        """
        assert 0 <= position < 32768

        return self.run_command(Command('GW', 'B', 5), position)

    def motor_stop(self):
        """
        Interrupting the movement of the motor. Current position is not reset.

        :return: Error code (1 byte)
        """
        return self.run_command(Command('GB', 'B'))

    def motor_moving(self):
        """
        Wait while motor is moving.

        :return: If interrupted - False, else True
        """
        while self.device_status() & 1:
            time.sleep(0.1)
            if keyboard.is_pressed(KEY_FOR_INTERRUPTION):
                self.motor_stop()
                return False
        return True

    def motor_error(self):
        """
        Reading the value of the step counter mismatch during re-initialization. Returns the value of the counter of
        motor steps at the moment of reaching the home position sensor (2 bytes) - a signed integer. If initialization
        was not carried out or it is the first one after switching on, it returns 0.
        For a serviceable motor with an accurate limit switch, this modulo value should not exceed 2.

        :return: The value of the steps counter
        """
        return self.run_command(Command('GE', '>h'))

    @arguments_type_checker_in_class
    def threshold_set(self, counter_id: int, threshold_id: int, value: int):
        """
        Setting one detector threshold.

        :param counter_id: Number of the detector.
        :param threshold_id: Threshold identifier (0 - bottom, 1 - up)
        :param value: Threshold value
        :return: Error code (1 byte)
        """
        assert 0 <= counter_id < Bucket.MAX_COUNTERS
        assert threshold_id in [0, 1]
        assert 0 <= value < 4096

        return self.run_command(Command('TS', 'B', 1, 1, 4), counter_id, threshold_id, value)

    @arguments_type_checker_in_class
    def threshold_get(self, counter_id: int, threshold_id: int):
        """
        Getting one detector threshold.

        :param counter_id: Number of the detector.
        :param threshold_id: Threshold (0 - bottom, 1 - up)
        :return: Error code (1 byte)
        """
        assert 0 <= counter_id < Bucket.MAX_COUNTERS
        assert threshold_id in [0, 1]

        return self.run_command(Command('TG', '>H', 1, 1), counter_id, threshold_id)

    @arguments_type_checker_in_class
    def exposure_set(self, value: int):
        """
        Exposure setting for counting pulses in all the detectors.

        :param value: Exposure value in tenths of a second (0 - 9999). If zero exposure is set, the counters
        immediately (without the ''counter_start' command) are switched on to the continuous operation mode
        :return: Error code (1 byte)
        """
        assert 0 <= value <= 9999

        return self.run_command(Command('ES', 'B', 4), value)

    def counter_start(self):
        """
        Starting a count. Turns on all counters for the specified exposure time ('exposure_set' command).

        :return: Error code (1 byte)
        """
        return self.run_command(Command('CS', 'B'))

    def counter_stop(self):
        """
        Count interruption. Stops all counters. The contents of the counters are not reset.

        :return: Error code (1 byte)
        """
        return self.run_command(Command('CB', 'B'))

    @arguments_type_checker_in_class
    def counter_get(self, counter_id: int):
        """
        Reading the result of the count (a set of pulses) in the specified channel.

        :param counter_id: Number of the detector
        :return: 4 bytes, unsigned integer
        """
        assert 0 <= counter_id < Bucket.MAX_COUNTERS

        return self.run_command(Command('CG', '>I', 1), counter_id)

    def exposure_get_remaining(self):
        """
        Reading the current exposure. When the counters are running continuously, the command returns the "hardware"
        time (in milliseconds) that has elapsed since the start of the counters. With the counters running normally,
        the command still returns the remaining exposure in tenths of a second.

        :return: 2 bytes - the value of the "remaining" exposure in tenths of a second.
        """
        return self.run_command(Command('EG', '>H'))

    def counter_working(self):
        """
        Wait while counter is working during set exposure time.

        :return: If interrupted - False, else True
        """
        while self.exposure_get_remaining() > 0:
            time.sleep(0.1)
            if keyboard.is_pressed(KEY_FOR_INTERRUPTION):
                self.counter_stop()
                return False
        return True

    @arguments_type_checker_in_class
    def photocathode_set_voltage(self, counter_id: int, voltage: int):
        """
        Setting the desired voltage on the photocathode of the given detector.

        :param counter_id: Number of the detector
        :param voltage: Voltage on the detector
        :return: Error code (1 byte)
        """
        assert 0 <= counter_id < Bucket.MAX_COUNTERS
        assert 0 <= voltage < 2048

        return self.run_command(Command('DS', 'B', 1, 4), counter_id, voltage)

    @arguments_type_checker_in_class
    def photocathode_get_voltage(self, counter_id: int):
        """
        Reading the current voltage on the photocathode of the given detector.

        :param counter_id: Number of the detector
        :return: Photocathode voltage (2 bytes, unsigned integer)
        """
        assert 0 <= counter_id < Bucket.MAX_COUNTERS

        return self.run_command(Command('DG', '>H', 1), counter_id)

    @arguments_type_checker_in_class
    def photocathode_enable(self, counter_id: int, enabled: bool):
        """
        Enable or disable the photocathode for the specified detector. If 'disable', the detector will turn off, that
        is, the standby voltage will be set on it from the parameters #Dn.IV. If 'enable', the voltage set in the last
        command (#Dn.IV) will be set on the detector. If no 'photocathode_set_voltage' command has been received since
        the device was turned on or the 'device_reset' command was issued, the operating voltage from the device
        parameters (#Dn. WV).

        :param counter_id: Number of the detector.
        :param enabled: True or False
        :return: Error code (1 byte)
        """
        assert 0 <= counter_id < Bucket.MAX_COUNTERS

        en_val = 0
        if enabled:
            en_val = 1
        return self.run_command(Command('DM', 'B', 1, 1), counter_id, en_val)

    def device_status(self):
        """
        Read status byte. The contents of this byte shows which devices of the spectrometer are "busy" at the given
        moment of time - that is, they "transition" from one stable state to another.
        &h80 - Presence of an error.
        &h40 - X-ray tube mode is setting.
        &h20 - The detector is turning on.
        &h10 - Pulse counters are enabled.
        &h08 - The controller is busy writing parameters "to disk" until the write is completed, no commands (except
        for reading the status) are accepted.
        &h04 - Filter changer or crystal changer is working.
        &h02 - Sample changer is working.
        &h01 - The motor is working.

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

