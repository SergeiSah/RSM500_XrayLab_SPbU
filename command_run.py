from bucket import Bucket
from convertor import *
from definitions import *
from handlers import convert_datatypes_to_func
from logger import LogHandler
from scans import Scan
from settings import Settings


class CommandRunner:
    # phrases that will appear if only the mode name without parameters was inputted
    input_phrases = {
        'escan': ['Input exposure in seconds: ',
                  'Input number of steps: ',
                  'Input step value in rev of the reel: ',
                  'Input start rev of the reel: '],
        'move': ['Input motor number: ',
                 'Input step: '],
        'setV': [f'Input voltage for the photocathode of the detector {i + 1}: ' for i in range(2)],
        'setT': ['Input detector number: ',
                 *[f'Input the {th} threshold: ' for th in ['lower', 'upper']]],
        'set2T': [f'Input the {th} threshold: ' for th in ['lower', 'upper']],
        'setAPos': ['Input motor number: '],
        **dict.fromkeys(['mscan', 'getV', 'getT', 'getAPos'], [])   # commands without phrases
    }

    def __init__(self, rsm: Bucket):
        self.__lh = LogHandler()
        self.log = self.__lh.logger

        self.rsm = rsm
        self.settings = Settings()
        self.scan = Scan(self.rsm, self.settings)

        self.modes = {
            'escan': self.run_en_scan,
            'mscan': self.run_manual_scan,
            'move': self.run_motor_move,
            'setV': self.set_voltage,
            'setT': self.set_threshold,
            'set2T': self.set_two_threshold,
            'setAPos': self.set_absolute_position_zero,
            'getV': self.get_voltage,
            'getT': self.get_thresholds,
            'getAPos': self.get_motor_absolute_position,
            **dict.fromkeys(['info', 'help'], self.info)
        }

    def run_command(self, mode, *args):
        """
        The function determines, whether the specified mode exists in the available modes, check accordance of argument
        datatypes to that of specified in the function annotation. If argument datatypes of invalid, or number of the
        arguments incorrect, input values successively with popup hint. In the end it runs a function that corresponds
        to the mode.

        :param mode: name of the mode, specified in the `modes` dictionary
        :param args: arguments passed to the function of the mode
        :return: None
        """
        try:
            command = self.modes[mode]

            # output information about function
            if len(args) > 0:
                if 'param' in args[0]:
                    print(f'Parameters of the [{mode}]:', *self._func_param_names(command))
                    return 0
                elif 'doc' == args[0]:
                    print(command.__doc__)
                    return 0

            # reduce arguments to datatypes of the desired function
            _args = convert_datatypes_to_func(command, *args)

            # if there are no arguments or their number is invalid, input with hints
            if _args is None:
                _args = []
                for phrase, param_type in zip(self.input_phrases[mode], command.__annotations__.values()):
                    _args.append(param_type(input(phrase)))

            command(*_args)
            return 0
        except KeyError:
            print(f'Command {mode} does not exist.')
            return -1
        except ValueError:
            print('Invalid value of the argument')
            return -1

    def run_en_scan(self, exposure: float, step_num: int, step: float, start: float):
        """
        Run an energy scan with the given parameters.

        :param exposure: exposure time of the detectors
        :param step_num: number of steps
        :param step: value of one step in revs of the reel
        :param start: value in revs of the reel from which the scan starts
        :return: 0 or -1
        """
        try:
            assert 1 <= int(exposure * 10) <= 9999, f'Invalid exposure {exposure}, must be in the range of [0.1, 999]'
            assert step_num > 0, 'Number of steps cannot be less than 0'
            # TODO: determine assertions for step and start
            # assert step > 1 / 75000
            # assert <= start <=
        except AssertionError as msg:
            print(msg)
            return -1

        self.log.info(f'Start [escan] {exposure} {step_num} {step} {start}')
        was_stopped = self.scan.one_motor_scan('escan', MOTOR_0, exposure, step_num, step, start)
        if not was_stopped:
            self.log.info(f'[escan] has been completed.')
            return 0

        self.log.info(f'[escan] has been stopped.')
        return -1

    def run_motor_move(self, motor: int, step: float):
        # TODO: complete the doc after determination of dependence of motor steps on distance for motor_3
        """
        Move the specified motor by the given steps relative to the position where the motor is currently located.
        Steps for motor_0 are in the revs of the reel, for motor_1 and motor_2 in grads.

        :param motor: number of the motor
        :param step: value of the step to move motor
        :return: 0 or -1
        """
        # FIXME: define limits for relative step on the basis of absolut motor positions
        try:
            assert motor in [MOTOR_0, MOTOR_1, MOTOR_2, MOTOR_3], 'Wrong number of the motor'
        except AssertionError as msg:
            print(msg)
            return -1

        # determine value of direction for the command motor_move of the Bucket class
        if step < 0:
            direction = DIRECTION['negative'][motor]
        elif step > 0:
            direction = DIRECTION['positive'][motor]
        else:
            print('Step cannot be 0.')
            return -1

        self.rsm.motor_select(motor)
        m_step = to_motor_steps(motor, abs(step))

        position = self.settings.get_motor_apos(motor) if motor != MOTOR_0 else self.rsm.motor_get_position()
        self.log.info(f'Start motor {motor} moving from position {position}')

        # bypass the restriction for step value for MOTOR_0
        if motor == MOTOR_0 and m_step >= 32768:

            repetitions = m_step // 32767
            residual = m_step % 32767
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
            self.rsm.motor_move(direction, m_step)
            is_arrived = self.rsm.motor_moving()
            if motor != MOTOR_0:
                self.settings.change_motor_apos(motor, to_motor_steps(motor, step))

        status = 'arrived' if is_arrived else 'been stopped'
        position = self.settings.get_motor_apos(motor) if motor != MOTOR_0 else self.rsm.motor_get_position()
        self.log.info(f'The motor {motor} has {status}, position: {position}')

        self.rsm.motor_select(4)
        return 0

    def set_voltage(self, detector_1_v: int, detector_2_v: int):
        """
        Set voltage on the photocathodes of the detectors.

        :param detector_1_v: voltage on photocathode of the first detector
        :param detector_2_v: voltage on photocathode of the second detector
        :return: 0 or -1
        """
        try:
            for voltage in [detector_1_v, detector_2_v]:
                assert 0 <= voltage < 2048, f'Invalid value {voltage}. Voltage must be in the range of [0, 2048)'
        except AssertionError as msg:
            print(msg)
            return -1

        self.rsm.photocathode_set_voltage(COUNTER_1, detector_1_v)
        self.rsm.photocathode_set_voltage(COUNTER_2, detector_2_v)
        self.log.info(f'Voltage on the photocathodes: {self.rsm.photocathode_get_voltage(COUNTER_1)}V (1), '
                      f'{self.rsm.photocathode_get_voltage(COUNTER_2)}V (2)')
        return 0

    def get_voltage(self):
        """
        Output voltage on the photocathodes to console.

        :return: None
        """
        print(f'Voltage on the photocathodes: {self.rsm.photocathode_get_voltage(COUNTER_1)}V (1), '
              f'{self.rsm.photocathode_get_voltage(COUNTER_2)}V (2)')

    def set_threshold(self, detector_num: int, low_threshold: int, up_threshold: int):
        """
        Set lower and upper thresholds for the given detector.

        :param detector_num: number of the detector (1 or 2)
        :param low_threshold: lower threshold in mV
        :param up_threshold: upper threshold in mV
        :return: 0 or -1
        """
        try:
            detector_num = {1: COUNTER_1, 2: COUNTER_2}[detector_num]
            assert 0 <= low_threshold < 4096 or 0 <= low_threshold < 4096, 'Thresholds must be in the range [0, 4096)'
            assert low_threshold < up_threshold, 'The lower threshold cannot be greater than or equal to the upper one'
        except KeyError:
            print('Invalid number of the detector. Must be 1 or 2.')
            return -1
        except AssertionError as msg:
            print(msg)
            return -1

        for id_level, value in zip([LOWER_THRESHOLD, UPPER_THRESHOLD], [low_threshold, up_threshold]):
            self.rsm.threshold_set(detector_num, id_level, value)

        self.log.info(f'Detector {detector_num} thresholds: {self.rsm.threshold_get(detector_num, LOWER_THRESHOLD)} mV,'
                      f' {self.rsm.threshold_get(detector_num, UPPER_THRESHOLD)} mV')
        return 0

    def set_two_threshold(self, low_threshold: int, up_threshold: int):
        """
        Set the same thresholds for the both detectors.

        :param low_threshold: lower threshold in mV
        :param up_threshold: upper threshold in mV
        :return: 0 or -1
        """
        for detector_num in [1, 2]:
            flag = self.set_threshold(detector_num, low_threshold, up_threshold)
            if flag != 0:
                return -1
        return 0

    def get_thresholds(self):
        """
        Output thresholds of the detectors to console.

        :return: None
        """
        for i, cnt in enumerate([COUNTER_1, COUNTER_2]):
            print(f'Thresholds of the detector {i + 1}: ', end='')
            for th in [LOWER_THRESHOLD, UPPER_THRESHOLD]:
                print(f'{self.rsm.threshold_get(cnt, th)}', end=' ')
            print()

    def set_absolute_position_zero(self, motor_num: int):
        """
        Set absolute position of the motor to zero.

        :param motor_num: motor number
        :return: 0 or -1
        """
        current_position = self.settings.get_motor_apos(motor_num)
        self.settings.change_motor_apos(motor_num, -current_position)
        self.log.info(f'Absolute position of the motor {motor_num} was set to 0.')
        return 0

    def get_motor_absolute_position(self):
        """
        Output absolute positions of the motors.

        :return: None
        """

        print('Absolute positions of the motors:')
        for motor_num in [MOTOR_1, MOTOR_2, MOTOR_3]:
            print(f'Motor {motor_num}: {self.settings.get_motor_apos(motor_num)}')

    def run_manual_scan(self, exposure: float = 1., time_steps_on_plot: int = 30):
        """
        Continuously displays CPS values on a plot over time.

        :param exposure: exposure time of the detectors
        :param time_steps_on_plot: number of time steps on a plot
        :return: 0 or -1
        """

        try:
            assert 1 <= int(exposure * 10) <= 9999, f'Invalid exposure {exposure}, must be in the range of [0.1, 999]'
            assert time_steps_on_plot > 1, 'Number of steps on a plot cannot be less than 1'
        except AssertionError as msg:
            print(msg)
            return -1

        self.scan.manual_scan(exposure, time_steps_on_plot)
        return 0

    def info(self):
        print('\t==== List of commands with parameters ====')
        for mode, function in self.modes.items():
            print(f'\t[{mode}]\t', *self._func_param_names(function))

        print('\n\t==========================================\n'
              '\tCommands can be inputted in two ways:\n'
              '\t1. mode param_1 param_2 ...\n'
              '\t2. mode\n'
              '\tIf only mode was inputted, instructions will appear\n')

        print('\t============== Main settings =============\n'
              '\tport: name of the port that connected to the RSM\'s bucket\n'
              '\tbaudrate: connection speed in bps\n'
              '\tDM_files_path: absolute path to the directory with datafiles\n')

    @staticmethod
    def _func_param_names(func):
        """
        Return list of names of the function parameters

        :param func: function
        :return: list of param names
        """
        params = func.__code__.co_varnames[1:func.__code__.co_argcount]
        return list(map(lambda x: '{' + x + '}', params))
