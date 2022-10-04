import os

from typing import TypeVar, Callable, Type, Optional

import peewee

T = TypeVar("T")


def required_env(key: str, conversion_func: Callable[[str], T] = str) -> T:
    """
    Retrieves an environment variable which is required for running the application.
    Throws a ValueError if the variable is not found in os.environ (comparison by lowercase)
    :param key: environment variable name
    :param conversion_func: func to convert value into specific type (`str` by default)
    :raises ValueError if `key` is not found in environment (os.environ.keys())
    :return: value for `key` converted by `conversion_func`
    """
    if key.lower() in [_key.lower() for _key in os.environ.keys()]:
        return conversion_func(os.environ.get(key))

    raise ValueError(f"`{key}` not found in environment")


def list_message_for_model(model: Type[peewee.Model], delimiter: str = "\n", empty_message: str = "Nothing here",
                           order_by_field: Optional[peewee.Field] = None) -> str:
    results = model.select()
    if order_by_field:
        results = results.order_by(order_by_field)

    msg = delimiter.join(map(str, results))
    if not results:
        msg = empty_message

    return msg
