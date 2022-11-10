import inspect
import os
from datetime import datetime

from typing import TypeVar, Callable, List, Optional

from .logger import create_logger

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


def parse_date(date_string: str, date_formats: List[str] = None, default_year: int = 2023) -> Optional[datetime]:
    log = create_logger(inspect.currentframe().f_code.co_name)

    date = None
    if date_formats is None:
        date_formats = ["%d.%m", "%d.%m.%Y"]

    for date_format in date_formats:
        log.debug(f"try formatting ({date}) with {date_format}")

        try:
            date = datetime.strptime(date_string, date_format)
        except ValueError:
            log.error(f"couldn't parse date ({date}) with {date_format}", exc_info=True)
            pass

    if date:
        log.debug("successfully parsed date")
        if date.year == 1900:
            log.debug(f"year of parsed datetime object is 1900 -> set to default year ({default_year})")
            date = date.replace(year=default_year)
    else:
        log.error(f"couldn't parse date ({date} with any of ({date_formats})")

    return date
