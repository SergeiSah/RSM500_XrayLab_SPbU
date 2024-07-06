from convertor import to_motor_steps, to_step_units
from handlers import *
from logger import LogHandler
from rsm500.rsm_controller import Motor, Detector
from scans import Scan


class CommandRunner:

    def __init__(self, settings: Settings):
        self.__lh = LogHandler()
        self.log = self.__lh.logger

        self.motor = Motor()
        self.detector_1 = Detector(COUNTER[1])
        self.detector_2 = Detector(COUNTER[2])

        # self.rsm = rsm
        self.settings = settings
        self.scan = Scan(self.settings)

        self.modes = {
            self.escan.__name__: self.escan,
            self.ascan.__name__: self.ascan,
            self.a2scan.__name__: self.a2scan,
            self.mscan.__name__: self.mscan,
            self.move.__name__: self.move,
            self.amove.__name__: self.amove,
            self.setV.__name__: self.setV,
            self.setT.__name__: self.setT,
            self.set2T.__name__: self.set2T,
            self.setAPos.__name__: self.setAPos,
            self.getV.__name__: self.getV,
            self.getT.__name__: self.getT,
            self.getAPos.__name__: self.getAPos,
            **dict.fromkeys(['info', 'help'], self.info)
        }

        # phrases that will appear if only the mode name without parameters was inputted
        self.input_phrases = {
            self.escan.__name__: ['Input start rev of the reel: ',
                                  'Input number of steps: ',
                                  'Input step value in rev of the reel: ',
                                  'Input exposure in seconds: '],
            self.ascan.__name__: ['Input motor number: ',
                                  'Input start position: ',
                                  'Input number of steps: ',
                                  'Input value of each step: ',
                                  'input exposure in seconds: '],
            self.move.__name__: ['Input motor number: ', 'Input step: '],
            self.amove.__name__: ['Input motor number: ', 'Input position to move: '],
            self.setV.__name__: [f'Input voltage for the photocathode of the detector {i + 1}: ' for i
                                 in
                                 range(2)], 'setT': ['Input detector number: ',
                                                     *[f'Input the {th} threshold: ' for th in
                                                       ['lower', 'upper']]],
            self.set2T.__name__: [f'Input the {th} threshold: ' for th in ['lower', 'upper']],
            self.setAPos.__name__: ['Input motor number: '],
            **dict.fromkeys([
                self.mscan.__name__,
                self.getV.__name__,
                self.getT.__name__,
                self.getAPos.__name__
            ], [])
        }

        self.input_phrases[self.a2scan.__name__] = self.input_phrases[self.ascan.__name__][1:]

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
            if mode not in self.modes:
                raise KeyError(f'Command {mode} does not exist.')

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

        except KeyError as message:
            print(f'Invalid key value:', message)
        except ValueError as message:
            print('Invalid value:', message)
        except TypeError as message:
            print('Invalid datatype of the value:', message)
        except MotorException as message:
            print('MotorException:', message)
        except DetectorException as message:
            print('DetectorException:', message)
        except PlotException as message:
            print('PlotException:', message)

    @validate_and_log
    def escan(self, start: float, step_num: int, step: float, exposure: float):
        """
        Run an energy scan with the given parameters.

        :param exposure: exposure time of the detectors
        :param step_num: number of steps
        :param step: value of one step in revs of the reel
        :param start: value in revs of the reel from which the scan starts
        :return: None
        """
        step, = validate_values(MOTOR_0, [step], self.log)
        self.scan.motor_scan('escan', MOTOR_0, start, step_num, step, exposure)

    @validate_and_log
    def ascan(self, motor: int, start_position: float, step_num: int, step: float, exposure: float):
        """
        Run scanning by the given motor from the specified absolute position.

        :param motor: number of the motor
        :param start_position: specifies position, to which motor will move before scanning
        :param step_num: number of steps
        :param step: value of each step
        :param exposure: time exposure of the detectors
        :return: None
        """
        start_position, step = validate_values(motor, [start_position, step], self.log)
        self.amove(motor, start_position)  # move to start position
        self.scan.motor_scan('ascan', motor, start_position, step_num, step, exposure)

    @validate_and_log
    def a2scan(self, start_position: float, step_num: int, step: float, exposure: float):
        """
        Run theta - 2theta scanning from the specified absolute theta position.

        :param start_position: start theta angle
        :param step_num: number of steps in the scan
        :param step: value for each step
        :param exposure: time exposure of the detectors
        :return: None
        """
        # move motors to start positions
        start_position, step = validate_values(MOTOR_1, [start_position, step], self.log)
        self.amove(MOTOR_1, start_position)
        self.amove(MOTOR_2, 2 * start_position)
        self.scan.motor_scan('a2scan', MOTOR_1, start_position, step_num, step, exposure, motor2_id=MOTOR_2)

    def mscan(self, exposure: float = 1., time_steps_on_plot: int = 30):
        """
        Continuously displays CPS values on a plot over time.

        :param exposure: exposure time of the detectors
        :param time_steps_on_plot: number of time steps on a plot
        :return: None
        """

        validate_exposure(exposure)
        if not time_steps_on_plot > 1:
            raise PlotException('Number of steps on a plot cannot be less than 1.')

        self.scan.manual_scan(exposure, time_steps_on_plot)

    def move(self, motor_id: int, step: float):
        # TODO: complete the doc after determination of dependence of motor steps on distance for motor_3
        """
        Move the specified motor by the given steps relative to the position where the motor is currently located.
        Steps for motor_0 are in the revs of the reel, for motor_1 and motor_2 in grads.

        :param motor_id: number of the motor
        :param step: value of the step to move motor
        :return: None
        """
        # FIXME: define limits for relative step on the basis of absolut motor positions
        validate_motor(motor_id)
        step = validate_values(motor_id, [step], self.log)[0]

        # determine value of direction for the command motor_move of the Bucket class
        if step < 0:
            direction = DIRECTION['negative'][motor_id]
        elif step > 0:
            direction = DIRECTION['positive'][motor_id]
        else:
            return

        self.motor.select(motor_id)
        m_step = to_motor_steps(motor_id, abs(step))

        start_pos_in_controller = self.motor.get_position()
        start_abs_position = self.settings.get_abs_motor_position(motor_id) if motor_id != MOTOR_0 \
            else start_pos_in_controller
        self.log.info(f'Start motor {motor_id} [move] from position {start_abs_position} '
                      f'({start_pos_in_controller} in controller)')

        # bypass the restriction for step value for MOTOR_0
        if motor_id == MOTOR_0 and m_step >= 32768:

            repetitions = m_step // 32767
            residual = m_step % 32767
            is_arrived = True

            for i in range(repetitions):
                self.motor.move(direction, 32767)
                is_arrived = self.motor.is_moving()
                if not is_arrived:
                    break

            # if moving was not interrupted
            if is_arrived:
                self.motor.move(direction, residual)
                is_arrived = self.motor.is_moving()

        else:
            self.motor.move(direction, m_step)
            is_arrived = self.motor.is_moving()
            if motor_id != MOTOR_0:
                self.settings.set_abs_motor_position(motor_id, to_motor_steps(motor_id, step))

        status = 'arrived' if is_arrived else 'been stopped'
        end_position_in_controller = self.motor.get_position()
        end_abs_position = self.settings.get_abs_motor_position(motor_id) if motor_id != MOTOR_0 \
            else end_position_in_controller
        self.log.info(f'The motor {motor_id} has {status}, position: {end_abs_position} '
                      f'({end_position_in_controller} in controller)')
        self.log.info(f'Difference: {end_abs_position - start_abs_position} '
                      f'({end_position_in_controller - start_pos_in_controller} in controller)')

        self.motor.select(4)

    def amove(self, motor: int, position: float):
        """
        Move the motor to the specified position.

        :param motor: motor number
        :param position: desired position
        :return: None
        """
        # TODO: define limits for relative step on the basis of absolut motor positions
        validate_motor(motor, scan_func_name=self.amove.__name__)

        current_apos = to_step_units(motor, self.settings.get_abs_motor_position(motor))
        step = position - current_apos

        return self.move(motor, step)

    def setV(self, detector_1_v: int, detector_2_v: int):
        """
        Set voltage on the photocathodes of the detectors.

        :param detector_1_v: voltage on photocathode of the first detector
        :param detector_2_v: voltage on photocathode of the second detector
        :return: 0 or -1
        """

        for voltage in [detector_1_v, detector_2_v]:
            validate_photocathode_voltage(voltage)

        self.detector_1.set_voltage_on_photocathode(detector_1_v)
        self.detector_2.set_voltage_on_photocathode(detector_2_v)

        self.log.info(f'Voltage on the photocathodes: {self.detector_1.get_voltage_on_photocathode()}V (1), '
                      f'{self.detector_2.get_voltage_on_photocathode()}V (2)')

    def getV(self):
        """
        Output voltage on the photocathodes to console.

        :return: None
        """
        print(f'Voltage on the photocathodes: {self.detector_1.get_voltage_on_photocathode()}V (1), '
              f'{self.detector_2.get_voltage_on_photocathode()}V (2)')

    def setT(self, detector_num: int, low_threshold: int, up_threshold: int):
        """
        Set lower and upper thresholds for the given detector.

        :param detector_num: number of the detector (1 or 2)
        :param low_threshold: lower threshold in mV
        :param up_threshold: upper threshold in mV
        :return: None
        """

        if detector_num not in COUNTER:
            raise DetectorException('invalid number of the detector.')
        if not 0 <= low_threshold < 4096 or not 0 <= up_threshold < 4096:
            raise DetectorException('Thresholds must be in the range [0, 4096).')
        if not low_threshold < up_threshold:
            raise DetectorException('The lower threshold cannot be greater than or equal to the upper one.')

        detector = self.detector_1 if detector_num == 1 else self.detector_2

        for id_level, value in zip([LOWER_THRESHOLD, UPPER_THRESHOLD], [low_threshold, up_threshold]):
            detector.set_threshold(id_level, value)

        self.log.info(f'Detector {detector_num} thresholds: {detector.get_threshold(LOWER_THRESHOLD)} mV,'
                      f' {detector.get_threshold(UPPER_THRESHOLD)} mV')

    def set2T(self, low_threshold: int, up_threshold: int):
        """
        Set the same thresholds for the both detectors.

        :param low_threshold: lower threshold in mV
        :param up_threshold: upper threshold in mV
        :return: None
        """
        for detector_num in COUNTER:
            self.setT(detector_num, low_threshold, up_threshold)

    def getT(self):
        """
        Output thresholds of the detectors to console.

        :return: None
        """
        for i, detector in enumerate([self.detector_1, self.detector_2]):
            print(f'Thresholds for the detector {i}: {detector.get_threshold(LOWER_THRESHOLD)} mV, '
                  f'{detector.get_threshold(UPPER_THRESHOLD)} mV')

    def setAPos(self, motor_num: int):
        """
        Set absolute position of the motor to zero.

        :param motor_num: motor number
        :return: None
        """
        current_position = self.settings.get_abs_motor_position(motor_num)
        self.settings.set_abs_motor_position(motor_num, -current_position)
        self.log.info(f'Absolute position of the motor {motor_num} was set to 0.')

    def getAPos(self):
        """
        Output absolute positions of the motors.

        :return: None
        """

        print('Absolute positions of the motors:')
        for motor_num in [MOTOR_1, MOTOR_2, MOTOR_3]:
            apos_in_motor_steps = self.settings.get_abs_motor_position(motor_num)
            apos_in_units = to_step_units(motor_num, apos_in_motor_steps)
            print(f'Motor {motor_num}:   {apos_in_units:.2f} {self.scan.x_scale[motor_num].split(" ")[1]:<5} '
                  f'({apos_in_motor_steps})')

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
        return list(map(lambda x: f'<{x}>', params))

    # TODO: delete all returns in CommandRunner methods
    # TODO: replace assert and try on raise. Catch errors on the level of the command_run
    # TODO: think about mocks for bucket
