from functools import wraps
from inspect import signature
from typing import Union

from definitions import *


def arguments_type_checker_in_class(func):
    @wraps(func)    # save signature of the function
    def wrapper(self, *args):
        # reduced_args = []
        for arg, arg_type in zip(args, func.__annotations__.items()):
            assert isinstance(arg, arg_type[1]), f"Argument '{arg_type[0]}' must be {arg_type[1]}, not {type(arg)}"
            # reduced_args.append(arg_type(arg))
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
        print('Wrong number of the arguments')
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
    try:
        return list(map(lambda x, y: x(y), types, args))
    except ValueError:
        print('Invalid value of an argument')
        return


def scan_check_params_and_log(scan_func):
    @wraps(scan_func)
    def wrapper(self, *args, **kwargs):
        f_params = {name: val for name, val in zip(signature(scan_func).parameters, [self, *args])}
        try:
            if 'motor' in f_params:
                assert f_params['motor'] != MOTOR_0, f'Command works only for the motors {MOTOR_1}, ' \
                                                     f'{MOTOR_2} and {MOTOR_3}.'
                assert f_params['motor'] in [MOTOR_1, MOTOR_2, MOTOR_3], 'Invalid number of the motor.'
            assert f_params['step_num'] > 0, 'Number of steps cannot be less than 0'
            assert 1 <= int(f_params['exposure'] * 10) <= 9999, f'Invalid exposure {f_params["exposure"]}, ' \
                                                                f'must be in the range of [0.1, 999]'
            # TODO: add assert for step and start/end positions
        except AssertionError as msg:
            print(msg)
            return -1

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

