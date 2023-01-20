import time
from handlers import reduce_datatypes, reduce_datatypes_to_func
from scans import Scan
from bucket import Bucket
from inspect import signature
from convertor import *
from definitions import *
from logger import LogHandler


class CommandRunner:
    phrases = {
        'en_scan': ['Input exposure in seconds: ',
                    'Input number of steps: ',
                    'Input step value in rev of the reel: ',
                    'Input start rev of the reel: '],
        'move': ['Input motor number: ',
                 'Input step: '],
        'setV': [f'Input voltage for the photocathode of the detector {i+1}: ' for i in range(2)],
        'setT': [f'Input the {th} threshold: ' for th in ['lower', 'upper']]
    }

    def __init__(self, rsm: Bucket):
        self.__lh = LogHandler()
        self.log = self.__lh.logger

        self.rsm = rsm
        self.scan = Scan(self.rsm)

        self.modes = {
            'en_scan': self.run_en_scan,
            'move': self.run_motor_move,
            'setV': self.set_voltage,
            'setT': self.set_threshold,
            'getV': self.get_voltage,
            'getT': self.get_thresholds,
        }

    def run_command(self, mode, *args):
        try:
            command = self.modes[mode]
            # reduce arguments to datatypes of the desired function
            _args = reduce_datatypes_to_func(command, *args)

            # if there are no arguments or their number is invalid, input with hints
            if _args is None:
                _args = []
                for phrase, param_type in zip(self.phrases[mode], command.__annotations__.values()):
                    _args.append(param_type(input(phrase)))

            command(*_args)
        except KeyError:
            print(f'Command {mode} does not exist.')
        except ValueError:
            print('Invalid value of the argument')

    def run_en_scan(self, exposure: int, step_num: int, step: float, start: float):
        # # reduce datatypes of the entered arguments
        # _args = reduce_datatypes_to_func(self.scan.en_scan, *args)
        #
        # # if there are no arguments, or their number is incorrect
        # if _args is None:
        #     # TODO: Determine, why 1 sec exposure doesn't work
        #     exposure = int(input('Input exposure in seconds: '))
        #     step_num = int(input('Input number of steps: '))
        #     step = float(input('Input step value in rev of the reel: '))
        #     start = float(input('Input start rev of the reel: '))
        #     _args = (exposure, step_num, step, start)

        self.log.info(f'Start en_scan {exposure} {step_num} {step} {start}')
        was_stopped = self.scan.en_scan(exposure, step_num, step, start)
        if not was_stopped:
            self.log.info(f'en_scan has been completed. Motor {MOTOR_0} position: {self.rsm.motor_get_position()}')
            return 0

        self.log.info(f'en_scan has been stopped. Motor {MOTOR_0} position: {self.rsm.motor_get_position()}')
        return -1

    def run_motor_move(self, motor: int, steps: float):
        # # if there are no arguments, or their number is incorrect
        # _args = reduce_datatypes([int, float], *args)
        #
        # if _args is None:
        #     motor = int(input('Input motor number: '))
        #     steps = float(input('Input step: '))
        #     _args = (motor, steps)

        # determine value of direction for the command
        if steps < 0:
            direction = DIRECTION['negative'][motor]
        elif steps > 0:
            direction = DIRECTION['positive'][motor]
        else:
            print('Step cannot be 0.')
            return -1

        self.rsm.motor_select(motor)
        step = to_step(motor, abs(steps))

        self.log.info(f'Start motor {motor} moving')

        # bypass the restriction for step value for MOTOR_0
        if motor == MOTOR_0 and step >= 32768:

            repetitions = step // 32767
            residual = step % 32767
            is_arrived = True

            for i in range(repetitions):
                self.rsm.motor_move(direction, 32767)
                is_arrived = self.rsm.motor_moving()
                if not is_arrived:
                    break

            # if moving was not interrupted
            if is_arrived:
                self.rsm.motor_move(direction, residual)
                is_arrived = self.rsm.motor_moving()

        else:
            self.rsm.motor_move(direction, step)
            is_arrived = self.rsm.motor_moving()

        if is_arrived:
            self.log.info(f'The motor {motor} has arrived, position: {self.rsm.motor_get_position()}')
        else:
            self.log.info(f'The motor {motor} has been stopped, position: {self.rsm.motor_get_position()}')

        self.rsm.motor_select(4)
        return 0

    def set_voltage(self, detector_1_v: int, detector_2_v: int):
        self.rsm.photocathode_set_voltage(COUNTER_1, detector_1_v)
        self.rsm.photocathode_set_voltage(COUNTER_2, detector_2_v)
        self.log.info(f'Voltage on the photocathode of the detector 1: {self.rsm.photocathode_get_voltage(COUNTER_1)}')
        self.log.info(f'Voltage on the photocathode of the detector 2: {self.rsm.photocathode_get_voltage(COUNTER_2)}')
        return 0

    def get_voltage(self):
        print(f'Detector 1 photocathode voltage: {self.rsm.photocathode_get_voltage(COUNTER_1)}')
        print(f'Detector 2 photocathode voltage: {self.rsm.photocathode_get_voltage(COUNTER_2)}')

    def set_threshold(self, low_th: int, up_th: int):
        if low_th >= up_th:
            self.log.error('The lower threshold cannot be higher than the upper threshold')
            return -1

        for id_level, value in zip([LOWER_THRESHOLD, UPPER_THRESHOLD], [low_th, up_th]):
            self.rsm.threshold_set(COUNTER_1, id_level, value)
            self.rsm.threshold_set(COUNTER_2, id_level, value)

        self.log.info(f'Detector 1 thresholds: {self.rsm.threshold_get(COUNTER_1, LOWER_THRESHOLD)} '
                      f'{self.rsm.threshold_get(COUNTER_1, UPPER_THRESHOLD)}')
        self.log.info(f'Detector 2 thresholds: {self.rsm.threshold_get(COUNTER_2, LOWER_THRESHOLD)} '
                      f'{self.rsm.threshold_get(COUNTER_2, UPPER_THRESHOLD)}')
        return 0

    def get_thresholds(self):
        for i, cnt in enumerate([COUNTER_1, COUNTER_2]):
            print(f'Thresholds of the detector {i+1}: ', end='')
            for th in [LOWER_THRESHOLD, UPPER_THRESHOLD]:
                print(f'{self.rsm.threshold_get(cnt, th)}', end=' ')
            print()
