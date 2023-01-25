from bucket import Bucket
from convertor import *
from definitions import *
from handlers import convert_datatypes_to_func, check_exposure
from logger import LogHandler
from scans import Scan


class CommandRunner:
    phrases = {
        'escan': ['Input exposure in seconds: ',
                  'Input number of steps: ',
                  'Input step value in rev of the reel: ',
                  'Input start rev of the reel: '],
        'mscan': [],
        'move': ['Input motor number: ',
                 'Input step: '],
        'setV': [f'Input voltage for the photocathode of the detector {i + 1}: ' for i in range(2)],
        'setT': [f'Input the {th} threshold: ' for th in ['lower', 'upper']]
    }

    def __init__(self, rsm: Bucket):
        self.__lh = LogHandler()
        self.log = self.__lh.logger

        self.rsm = rsm
        self.scan = Scan(self.rsm)

        self.modes = {
            'escan': self.run_en_scan,
            'mscan': self.run_manual_scan,
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
            _args = convert_datatypes_to_func(command, *args)

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

    def run_en_scan(self, exposure: float, step_num: int, step: float, start: float):
        if not check_exposure(exposure):
            return -1

        self.log.info(f'Start escan {exposure} {step_num} {step} {start}')
        was_stopped = self.scan.energy_scan(exposure, step_num, step, start)
        if not was_stopped:
            self.log.info(f'escan has been completed. Motor {MOTOR_0} position: {self.rsm.motor_get_position()}')
            return 0

        self.log.info(f'escan has been stopped. Motor {MOTOR_0} position: {self.rsm.motor_get_position()}')
        return -1

    def run_motor_move(self, motor: int, steps: float):
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

        self.log.info(f'Start motor {motor} moving from position {self.rsm.motor_get_position()}')

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
            print(f'Thresholds of the detector {i + 1}: ', end='')
            for th in [LOWER_THRESHOLD, UPPER_THRESHOLD]:
                print(f'{self.rsm.threshold_get(cnt, th)}', end=' ')
            print()

    def run_manual_scan(self, exposure: float = 1., time_steps_on_plot: int = 30):
        if not check_exposure(exposure):
            return -1
        self.scan.manual_scan(exposure, time_steps_on_plot)
