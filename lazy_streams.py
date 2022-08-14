#!/usr/bin/env python
"""
Inspired by Java8's streams, provides a fluent syntax for list manipulation and
querying.  It's called lazy because it lazy-evaluates the stream values for
better performance and memory consumption of large lists.

Example usage:

    >>> from lazy_streams import stream
    >>> data = range(100)
    >>> s = stream(data)
    >>> print(s \\
    ...     .reverse() \\
    ...     .filter(lambda x: (x+1)%2 == 0) \\
    ...     .map(lambda x: x*x) \\
    ...     .map(lambda x: "Item %d" % x) \\
    ...     .last_or_else('Nothing here'))
    Item 1
    >>>

Copyright (c) 2017, Steve Brettschneider.
License: MIT (see LICENSE for details)
"""

__author__ = "Steve Brettschneider"

from typing import Iterator, Optional, Callable, List, Any, Union, Tuple
from enum import IntEnum
from functools import reduce
from abc import ABC, abstractmethod
from promise_keeper import PromiseKeeper, Promise


class LazyStream(ABC):
    """A lazy evaluated stream"""

    def __init__(self):
        self._original_size = 0

    @abstractmethod
    def size(self, threads: int = 0):  # pylint: disable=no-self-use, unused-argument
        """The resulting number of items in the stream.  Returns an int."""
        return 0

    def __len__(self) -> int:
        """
        usage with len, but thread number cannot be specified.
        """
        return self.size()

    def _materialize_item(self, index):  # pylint: disable=unused-argument,no-self-use
        return _MaterializationResult(_MaterializationResultState.NO_ITEM)

    def to_list(self, threads: int = 0) -> List[Any]:
        """
        Converts the stream to a python list.  If threads is greater than 0,
        this method will use a PromiseKeeper to parallelize the work.  If
        threads is 0, it will just do the work serially on the main thread.
        Beware, threading is computationally expensive.  It should really
        only be used here if the filter and/or map functions in the pipeline
        are time-bound (like making a web service call for example).

        Returns a list.
        """
        if threads > 0:
            return self._to_list_parallel(threads)
        else:
            return self._to_list_serial()

    def _to_list_serial(self) -> List[Any]:
        results = []
        index = 0
        while True:
            result = self._materialize_item(index)
            if result.status() == _MaterializationResultState.ITEM:
                results.append(result.item())
            elif result.status() == _MaterializationResultState.NO_ITEM:
                break
            index += 1
        return results

    def _to_list_parallel(self, thread_count: int) -> List[Any]:
        def promises_contains_no_item(promises: List[Promise]) -> bool:
            """Checks to see if the promises have any NO_ITEM statuses"""
            for i in range(len(promises) - 1, -1, -1):
                result = promises[i].get_result()
                if result is None:
                    continue
                if result.status() == _MaterializationResultState.NO_ITEM:
                    return True
                if result.status() == _MaterializationResultState.ITEM:
                    return False
            return False

        promises = []
        index = 0
        p_keeper = PromiseKeeper(thread_count, auto_stop=False)
        while True:
            promises.append(p_keeper.submit(self._materialize_item, (index,)))
            if promises_contains_no_item(promises):
                break
            index += 1
        p_keeper.stop()
        return_val = []
        for promise in promises:
            result = promise.get_result()
            if result != None and result.status() not in [
                _MaterializationResultState.NO_ITEM,
                _MaterializationResultState.FILTERED_OUT,
            ]:
                return_val.append(result.item())
        return return_val

    def to_string(self, separator: str = ", ", threads: int = 0) -> str:
        """Converts the stream to a string.  Returns a str."""
        return separator.join([str(i) for i in self.to_list(threads)])

    def reduce(self, func: Callable, threads: int = 0):
        """
        Calls python's reduce function using the given [func] and the items
        from the stream.  Returns a single value whose type matches that of
        [func]'s output.
        """
        return reduce(func, self.to_list(threads))

    def max(
        self, key: Optional[Callable] = None, threads: int = 0
    ) -> Optional["_LazyListStream"]:
        """
        Returns the maximum value in the stream.  Returns a single item from
        the stream.  This method forces processing of every item in the stream.
        """
        return self.sort(key=key, threads=threads).last_or_else()

    def min(
        self, key: Optional[Callable] = None, threads: int = 0
    ) -> Optional["_LazyListStream"]:
        """
        Returns the minimum value in the stream.  Returns a single item from
        the stream.  This method forces processing of every item in the stream.
        """
        return self.sort(key=key, threads=threads).first_or_else()

    def take(self, num_items: int) -> "_LazyListStream":
        """
        Returns a new LazyStream containing only the first [num_items] items.
        """
        results: List[Any] = []
        index = 0
        while len(results) < num_items:
            result = self._materialize_item(index)
            if result.status() == _MaterializationResultState.ITEM:
                results.append(result.item())
            elif result.status() == _MaterializationResultState.NO_ITEM:
                break
            index += 1
        return _LazyListStream(results)

    def first_or_else(
        self, or_else: Optional[Any] = None
    ) -> Optional["_LazyListStream"]:
        """
        Returns the first item in the stream or, if the stream is empty,
        returns [or_else].
        """
        index = 0
        while True:
            result = self._materialize_item(index)
            if result.status() == _MaterializationResultState.ITEM:
                return result.item()
            elif result.status() == _MaterializationResultState.NO_ITEM:
                return or_else
            index += 1

    def last_or_else(
        self, or_else: Optional[Any] = None
    ) -> Optional["_LazyListStream"]:
        """
        Returns the last item in the stream or, if the stream is empty,
        returns [or_else].
        """
        index = 0
        reverse = self.reverse()
        while True:
            result = reverse._materialize_item(
                index
            )  # pylint: disable=protected-access
            if result.status() == _MaterializationResultState.ITEM:
                return result.item()
            elif result.status() == _MaterializationResultState.NO_ITEM:
                return or_else
            index += 1

    def for_each(self, func: Callable) -> None:
        """
        Executes [func] on each item in the stream.  Doesn't return anything.
        """
        index = 0
        while True:
            result = self._materialize_item(index)
            if result.status() == _MaterializationResultState.ITEM:
                func(result.item())
            elif result.status() == _MaterializationResultState.NO_ITEM:
                break
            index += 1

    def flatten(self) -> "_LazyFlattenStream":
        """
        If items in the stream are tuples or lists, flattens them so that
        the resulting stream contains a list of non-tuple, non-list items

        [[1, 2], 3, [4, 5, [6, 7]]]

        becomes

        [1, 2, 3, 4, 5, 6, 7]

        Returns a new LazyStream.  This method forces processing of every item
        in the stream.
        """
        return _LazyFlattenStream(self)

    def sort(
        self, key: Callable = None, reverse: bool = False, threads: int = 0
    ) -> "_LazyListStream":
        """
        Sorts the steam given an optional [key] function.  Returns a new
        LazyStream.  This method forces processing of every item in the steam.
        """
        sorted_lst = sorted(self.to_list(threads), key=key, reverse=reverse)
        return _LazyListStream(sorted_lst)

    def map(self, func: Callable) -> "_LazyMapStream":
        """
        Replaces each item in the stream with func(item).  Returns a new
        LazyStream.
        """
        return _LazyMapStream(func, self)

    def filter(self, func: Callable) -> "_LazyFilterStream":
        """
        Filters out items from the stream in which func(item) is False.
        Returns a new LazyStream.
        """
        return _LazyFilterStream(func, self)

    def reverse(self) -> "_LazyReverseStream":
        """
        Reverses the order of the items in the stream.  Returns a new
        LazyStream.
        """
        return _LazyReverseStream(self)


class _LazyListStream(LazyStream):
    """A stream based off an actual list"""

    def __init__(self, lst: Union[List, Tuple]) -> None:
        super().__init__()
        if not isinstance(lst, (list, tuple)):
            raise ValueError("Argument must be a list or tuple")
        self._lst = lst
        self._original_size = len(lst)

    def _materialize_item(self, index: int) -> "_MaterializationResult":
        if index < 0:
            return _MaterializationResult(_MaterializationResultState.NO_ITEM)
        try:
            return _MaterializationResult(
                _MaterializationResultState.ITEM, self._lst[index]
            )
        except IndexError:
            return _MaterializationResult(_MaterializationResultState.NO_ITEM)

    def size(self, threads: int = 0) -> int:
        return len(self._lst)


class _LazyMapStream(LazyStream):
    """The Map implementation of a LazyStream"""

    def __init__(self, func: Callable, parent: "LazyStream") -> None:
        super().__init__()
        self._func = func
        self._parent = parent
        self._original_size = parent._original_size

    def size(self, threads=0):
        return self._parent.size(threads)

    def _materialize_item(self, index: int) -> "_MaterializationResult":
        result = self._parent._materialize_item(
            index
        )  # pylint: disable=protected-access
        if result.status() == _MaterializationResultState.ITEM:
            return _MaterializationResult(
                _MaterializationResultState.ITEM, self._func(result.item())
            )
        else:
            return result


class _LazyFilterStream(LazyStream):
    """The Filter implementation of a LazyStream"""

    def __init__(self, func: Callable, parent: "LazyStream") -> None:
        super().__init__()
        self._func = func
        self._parent = parent
        self._size = -1  # not calculated yet
        self._original_size = parent._original_size

    def size(self, threads: int = 0) -> int:
        if self._size == -1:
            self._size = len(self.to_list(threads))
        return self._size

    def _materialize_item(self, index: int) -> "_MaterializationResult":
        result = self._parent._materialize_item(
            index
        )  # pylint: disable=protected-access
        if result.status() == _MaterializationResultState.ITEM:
            included = self._func(result.item())
            if included:
                return result
            else:
                return _MaterializationResult(_MaterializationResultState.FILTERED_OUT)
        else:
            return result


class _LazyReverseStream(LazyStream):
    """The Reverse implemenation of a LazyStream"""

    def __init__(self, parent: "LazyStream"):
        super().__init__()
        self._parent = parent
        self._original_size = parent._original_size

    def size(self, threads: int = 0):
        return self._parent.size(threads)

    def _materialize_item(self, index: int) -> "_MaterializationResult":
        return self._parent._materialize_item(
            self._original_size - index - 1
        )  # pylint: disable=protected-access


class _LazyFlattenStream(LazyStream):
    """The Flatten implementation of a LazyStream"""

    def __init__(self, parent: "LazyStream"):
        super().__init__()
        self._parent = parent
        self._size = -1
        self._flattened_lst = None
        self._cache: List[Any] = []
        self._original_size = parent._original_size

    def size(self, threads: int = 0) -> int:
        return len(self._calc_flattened_list(threads))

    def _materialize_item(self, index: int) -> "_MaterializationResult":
        try:
            return _MaterializationResult(
                _MaterializationResultState.ITEM, self._calc_flattened_list()[index]
            )
        except IndexError:
            return _MaterializationResult(_MaterializationResultState.NO_ITEM)

    def _calc_flattened_list(self, threads: int = 0) -> List[Any]:
        if self._flattened_lst is None:
            self._flattened_lst = list(  # type: ignore
                _list_flattener(self._parent.to_list(threads))
            )
        return self._flattened_lst  # type: ignore


def _list_flattener(lst: Union[List[Any], Tuple[Any, ...]]) -> Iterator[Any]:
    """Flattens a nested list"""
    for i in lst:
        if isinstance(i, (list, tuple)):
            for j in _list_flattener(i):
                yield j
        else:
            yield i


class _MaterializationResultState(IntEnum):
    ITEM = 0
    FILTERED_OUT = 1
    NO_ITEM = 2


class _MaterializationResult:
    """Describes what happened when an item was materialized"""

    def __init__(self, status, item=None):
        self._status = status
        self._item = item

    def status(self):
        """Returns the status"""
        return self._status

    def item(self):
        """Returns the materialized value"""
        return self._item


def stream(lst) -> "_LazyListStream":
    """
    The main entry-point for creating a new stream.  Takes a list (lst) of
    items to populate the the new LazyStream.
    """
    if isinstance(lst, range):
        lst = list(lst)
    return _LazyListStream(lst)
