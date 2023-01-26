from functools import wraps
from typing import Union


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
