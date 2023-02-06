from functools import wraps
from inspect import signature
from typing import Union

from definitions import *
from error_types import *


def arguments_type_checker_in_class(func):
    @wraps(func)    # save signature of the function
    def wrapper(self, *args):
        assert hasattr(func, '__annotations__'), f'Hey, "programmer", you forgot annotate your function {func}'

        for arg, arg_type in zip(args, func.__annotations__.items()):
            if not isinstance(arg, arg_type[1]):
                raise TypeError(f"Argument '{arg_type[0]}' must be {arg_type[1]}, not {type(arg)}")
        return func(self, *args)
    return wrapper


def convert_datatypes_to_func(func, *args) -> Union[list, None]:
    """
    Convert types of the given arguments to the types indicated in a func annotations. If len(args) !=
    len(f_arguments without defs) - return None. defs - default parameters.

    :param func: some function with annotated parameters
    :param args: arguments, that will be transferred to the function
    :return: list of converted arguments or None
    """
    f_param_types = list(func.__annotations__.values())  # list of types of the func parameters
    defaults = func.__defaults__                         # tuple of the default parameters of the func or None
    defaults = list(defaults) if defaults is not None else []
    len_pos_args = len(f_param_types) - len(defaults)    # length of the positional arguments of the func

    if len(args) == 0 and len(f_param_types) > 0:
        return
    elif len(f_param_types) < len(args) or len(args) < len(f_param_types) - len(defaults):
        print('Wrong number of the arguments.')
        return

    _args = list(args)
    _args.extend(defaults[len(_args) - len_pos_args:])  # add necessary default values
    return convert_datatypes(f_param_types, *_args)


def convert_datatypes(types: list, *args) -> Union[list, None]:
    """
    Convert given types of values to indicated in the list `types`. len(list) must be == len(args)

    :param types: list of types
    :param args: values
    :return: list of converted values, or None
    """
    if len(args) == 0:  # Case of functions without arguments
        return []
    try:    # TODO: raise
        return list(map(lambda x, y: x(y), types, args))
    except ValueError:
        print('Invalid value of an argument')


def validate_and_log(scan_func):
    @wraps(scan_func)
    def wrapper(self, *args, **kwargs):
        f_params = {name: val for name, val in zip(signature(scan_func).parameters, [self, *args])}
        if 'motor' in f_params:
            validate_motor(f_params['motor'], scan_func.__name__)
        if not f_params['step_num'] > 0:
            raise ValueError('Number of steps cannot be less than 0.')
        validate_exposure(f_params['exposure'])
        # TODO: add raise error for step and start/end positions

        f_params.pop('self', None)
        self.log.info(f'Start [{scan_func.__name__}]' +
                      ''.join(' <{}:{}>'.format(name, val) for name, val in f_params.items()))

        was_stopped = scan_func(self, *args, **kwargs)

        status = 'stopped' if was_stopped else 'completed'
        self.log.info(f'[{scan_func.__name__}] has been {status}.')

        if 'motor' in f_params:    # Write absolute position of the motor to the log file
            self.log.info(f'Motor {f_params["motor"]} absolute position: '
                          f'{self.settings.get_motor_apos(f_params["motor"])}')

        return was_stopped
    return wrapper


def validate_motor(motor: int, scan_func_name=None):
    motors = [MOTOR_0, MOTOR_1, MOTOR_2, MOTOR_3]

    if scan_func_name is not None:
        if not motor != MOTOR_0:
            raise MotorException(f'Command [{scan_func_name}] works only with the motors '
                                 f'{MOTOR_1}, {MOTOR_2} and {MOTOR_3}.')
        motors.remove(MOTOR_0)

    if motor not in motors:
        raise MotorException('Invalid number of the motor.')


def validate_exposure(exposure: float):
    if not 1 <= int(exposure * 10) <= 9999:
        raise DetectorException(f'Exposure must be in the range of [0.1, 999], your value is {exposure}.')


def validate_photocathode_voltage(voltage: int):
    if not 0 <= voltage < 2048:
        raise ValueError(f'Voltage on the photocathode must be in the range of [0, 2048)')
