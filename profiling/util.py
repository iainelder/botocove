from typing import Callable, Iterable, Tuple, TypeVar
from itertools import filterfalse, tee


T = TypeVar("T")

def partition(
    pred: Callable[[T], bool], iterable: Iterable[T]
) -> Tuple[Iterable[T], Iterable[T]]:
    "Use a predicate to partition entries into false entries and true entries."
    # partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9
    t1, t2 = tee(iterable)
    return filterfalse(pred, t1), filter(pred, t2)
