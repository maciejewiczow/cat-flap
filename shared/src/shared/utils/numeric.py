from typing import Any


def interpolate(n, range_from: tuple[Any, Any], range_to: tuple[Any, Any]):
    start1, stop1 = range_from
    start2, stop2 = range_to
    return ((n - start1) / (stop1 - start1)) * (stop2 - start2) + start2
