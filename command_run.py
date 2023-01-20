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
                 'Input step: ']
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
            self.modes[mode](*args)
        except KeyError:
            self.log.error(f'Command {mode} does not exist.')
            time.sleep(0.1)

    def run_en_scan(self, *args):
        # reduce datatypes of the entered arguments
        _args = reduce_datatypes_to_func(self.scan.en_scan, *args)

        # if there are no arguments, or their number is incorrect
        if _args is None:
            # TODO: Determine, why 1 sec exposure doesn't work
            exposure = int(input('Input exposure in seconds: '))
            step_num = int(input('Input number of steps: '))
            step = float(input('Input step value in rev of the reel: '))
            start = float(input('Input start rev of the reel: '))
            _args = (exposure, step_num, step, start)

        self.log.info('Start en_scan {0} {1} {2} {3}'.format(*_args))
        was_stopped = self.scan.en_scan(*_args)
        if not was_stopped:
            self.log.info(f'en_scan has been completed. Motor {MOTOR_0} position: {self.rsm.motor_get_position()}')
            return 0

        self.log.info(f'en_scan has been stopped. Motor {MOTOR_0} position: {self.rsm.motor_get_position()}')
        return -1

    def run_motor_move(self, *args):
        # if there are no arguments, or their number is incorrect
        _args = reduce_datatypes([int, float], *args)

        if _args is None:
            motor = int(input('Input motor number: '))
            steps = float(input('Input step: '))
            _args = (motor, steps)

        # determine value of direction for the command
        if _args[1] < 0:
            direction = DIRECTION['negative'][_args[0]]
        elif _args[1] > 0:
            direction = DIRECTION['positive'][_args[0]]
        else:
            print('Step cannot be 0.')
            return -1

        self.rsm.motor_select(_args[0])
        step = to_step(_args[0], abs(_args[1]))

        self.log.info(f'Start motor {_args[0]} moving')

        # bypass the restriction for step value for MOTOR_0
        if _args[0] == MOTOR_0 and step >= 32768:

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
            self.log.info(f'The motor {_args[0]} has arrived, position: {self.rsm.motor_get_position()}')
        else:
            self.log.info(f'The motor {_args[0]} has been stopped, position: {self.rsm.motor_get_position()}')

        self.rsm.motor_select(4)
        return 0

    def set_voltage(self, *args):
        if not args or len(args) != 2:
            detector_1_v = int(input('Input voltage for the photocathode of the detector 1: '))
            detector_2_v = int(input('Input voltage for the photocathode of the detector 2: '))
            args = (detector_1_v, detector_2_v)

        self.rsm.photocathode_set_voltage(COUNTER_1, args[0])
        self.rsm.photocathode_set_voltage(COUNTER_2, args[1])

        self.log.info(f'Voltage on the photocathode of the detector 1: {self.rsm.photocathode_get_voltage(COUNTER_1)}')
        self.log.info(f'Voltage on the photocathode of the detector 2: {self.rsm.photocathode_get_voltage(COUNTER_2)}')
        return 0

    def get_voltage(self):
        print(f'Detector 1 photocathode voltage: {self.rsm.photocathode_get_voltage(COUNTER_1)}')
        print(f'Detector 2 photocathode voltage: {self.rsm.photocathode_get_voltage(COUNTER_2)}')

    def set_threshold(self, *args):
        if not args or len(args) != 2:
            low_th = int(input('Input the lower threshold: '))
            top_th = int(input('Input the upper threshold: '))
            args = (low_th, top_th)

        if args[0] >= args[1]:
            self.log.error('The lower threshold cannot be higher than the upper threshold')
            return -1

        for id_level, value in zip([LOWER_THRESHOLD, UPPER_THRESHOLD], args):
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
