from functools import wraps


def arguments_type_checker_in_class(func):
    @wraps(func)
    def wrapper(self, *args):
        for arg, arg_type in zip(args, func.__annotations__.items()):
            assert isinstance(arg, arg_type[1]), f"Argument '{arg_type[0]}' must be {arg_type[1]}, not {type(arg)}"
        return func(self, *args)
    # wrapper.__annotations__ = func.__annotations__
    return wrapper
