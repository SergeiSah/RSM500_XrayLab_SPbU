from functools import wraps


def arguments_type_checker_in_class(func):
    @wraps(func)    # save signature of the function
    def wrapper(self, *args):
        # reduced_args = []
        for arg, arg_type in zip(args, func.__annotations__.items()):
            assert isinstance(arg, arg_type[1]), f"Argument '{arg_type[0]}' must be {arg_type[1]}, not {type(arg)}"
            # reduced_args.append(arg_type(arg))
        return func(self, *args)
    return wrapper


def reduce_datatypes_to_func(func, *args):
    f_param_types = func.__annotations__.values()
    return reduce_datatypes(f_param_types, *args)


def reduce_datatypes(types: list, *args):
    if len(args) == 0:
        return None
    elif len(types) != len(args):
        print('Wrong number of arguments')
        return None

    try:
        return list(map(lambda x, y: x(y), types, args))
    except ValueError:
        print('Invalid value of an argument')
        return None

