from math import floor
import re
from datetime import timedelta

regex = re.compile(
    r"((?P<days>\d+?)d)?((?P<hours>\d+?)h)?((?P<minutes>\d+?)min)?((?P<seconds>\d+?)s)?((?P<miliseconds>\d+?)ms)?"
)


def str_to_timedelta(delta_str: str) -> timedelta:
    parts = regex.match(delta_str)

    if not parts:
        raise ValueError(f"Invalid timedelta string: {delta_str}")

    parts = parts.groupdict()

    time_params = {}

    for name, param in parts.items():
        if param:
            time_params[name] = int(param)

    return timedelta(**time_params)


def timedelta_to_str(delta: timedelta) -> str:
    result = ""

    if delta.days > 0:
        result += f"{delta.days}d"

    hours = delta.seconds // 3600
    if hours > 0:
        result += f"{hours}h"

    minutes = delta.seconds // 60 % 60
    if minutes > 0:
        result += f"{minutes}min"

    seconds = floor(delta.seconds) % 60
    if seconds > 0:
        result += f"{seconds}s"

    miliseconds = delta.microseconds // 1000
    if miliseconds > 0:
        result += f"{miliseconds}ms"

    return result
