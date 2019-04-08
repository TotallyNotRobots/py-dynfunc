__version__ = (0, 0, 1)

__all__ = (
    'ParameterError',
    'call_with_args',
    'populate_args',
)

from inspect import Parameter, signature


class ParameterError(Exception):
    def __init__(self, name, valid_args):
        super().__init__(
            "'{}' is not a valid parameter, valid parameters are: {}".format(
                name, valid_args
            )
        )
        self.name = name
        self.valid_args = valid_args


def _get_arg_value(param, data_map):
    """
    :type param: _inspect.Parameter
    :type data_map: dict
    """
    try:
        return data_map[param.name]
    except KeyError as e:
        if param.default is param.empty:
            raise ParameterError(e.args[0], list(data_map.keys())) from e

        return param.default


def populate_args(func, data_map):
    args = []
    kwargs = {}
    _args_add = args.append
    _kwargs_add = kwargs.__setitem__

    sig = signature(func)
    for key, param in sig.parameters.items():  # type: str, Parameter
        if param.kind is param.KEYWORD_ONLY:
            _kwargs_add(key, _get_arg_value(param, data_map))
        elif param.kind is param.POSITIONAL_ONLY:  # pragma: no cover
            _args_add(_get_arg_value(param, data_map))
        elif param.kind is param.POSITIONAL_OR_KEYWORD:
            _kwargs_add(key, _get_arg_value(param, data_map))
        elif param.kind is param.VAR_KEYWORD:
            raise TypeError("Unable to populate VAR_KEYWORD parameter '{}'".format(key))
        elif param.kind is param.VAR_POSITIONAL:
            raise TypeError("Unable to populate VAR_POSITIONAL parameter '{}'".format(key))
        else:  # pragma: no cover
            raise TypeError("Unknown parameter type {!r}".format(param.kind))

    return args, kwargs


def call_with_args(func, arg_data):
    """Allows calling a function dynamically based on its signature,
    allowing for cleaner callback or handler functions.

    This uses inspect.signature() to determine the name for each argument
    and uses that name as a key for `arg_data`.

    >>> def a(n):
    ...    return n**2
    >>> call_with_args(a, {'n': 5, 's': 4, 'tm': 3})
    25

    >>> def func(*, param):
    ...     return param
    >>> call_with_args(func, {'param': 'foo'})
    'foo'

    >>> call_with_args(func, {'other': 'foo'})
    Traceback (most recent call last):
        [...]
    dynfunc.ParameterError: 'param' is not a valid parameter, valid parameters are: ['other']

    >>> call_with_args(lambda *args: args, {'args': [1]})
    Traceback (most recent call last):
        [...]
    TypeError: Unable to populate VAR_POSITIONAL parameter 'args'

    >>> call_with_args(lambda **args: args, {'args': [1]})
    Traceback (most recent call last):
        [...]
    TypeError: Unable to populate VAR_KEYWORD parameter 'args'

    >>> call_with_args(lambda a, b=1, c=2: (a, b, c), {'a': 1, 'b': 3})
    (1, 3, 2)

    :param func: A callable to pass `arg_data` to
    :param arg_data: A `Mapping` of arg data for `func`,
        provided dynamically to the function through signature inspection
    :return: The result of calling `func` with the values derived from `arg_data`
    """
    args, kwargs = populate_args(func, arg_data)
    return func(*args, **kwargs)
