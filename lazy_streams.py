#!/usr/bin/env python
"""
Inspired by Java8's streams, provides a fluent syntax for list manipulation and
querying.  It's called lazy because it lazy-evaluates the stream values for
better performance and memory consumption of large lists.

Example usage:

    >>> from lazy_streams import stream
    >>> data = range(100)
    >>> s = stream(data)
    >>> print s \\
    ...     .reverse() \\
    ...     .filter(lambda x: (x+1)%2 == 0) \\
    ...     .map(lambda x: x*x) \\
    ...     .map(lambda x: "Item %d" % x) \\
    ...     .last_or_else('Nothing here')
    Item 1
    >>>

Copyright (c) 2017, Steve Brettschneider.
License: MIT (see LICENSE for details)
"""

__author__ = 'Steve Brettschneider'
__version__ = '0.1'
__license__ = 'MIT'


class NoStreamItemError(LookupError):
    """Indicates that the requested item does not exist."""


class LazyStream(object):
    """A lazy evaluated stream"""

    def __init__(self, lst):
        self._lst = lst

    def size(self):
        """The resulting number of items in the stream.  Returns an int."""
        return len(self._lst)

    def _calc_item(self, index):
        if index < 0:
            raise NoStreamItemError()
        try:
            return self._lst[index]
        except:
            raise NoStreamItemError()

    def to_list(self):
        """Converts the stream to a python list.  Returns a list."""
        result = []
        index = 0
        while True:
            try:
                result.append(self._calc_item(index))
                index += 1
            except NoStreamItemError:
                break
        return result

    def to_string(self, seperator=', '):
        """Converts the stream to a string.  Returns a str."""
        return seperator.join([str(i) for i in self.to_list()])

    def reduce(self, func):
        """
        Calls python's reduce function using the given [func] and the items
        from the stream.  Returns a single value whose type matches that of
        [func]'s output.
        """
        return reduce(func, self.to_list())

    def max(self, key=None):
        """
        Returns the maximum value in the stream.  Returns a single item from
        the stream.  This method forces processing of every item in the stream.
        """
        return self.sort(key=key).last_or_else()

    def min(self, key=None):
        """
        Returns the minimum value in the stream.  Returns a single item from
        the stream.  This method forces processing of every item in the stream.
        """
        return self.sort(key=key).first_or_else()

    def take(self, num_items):
        """
        Returns a new LazyStream containing only the first [num_items] items.
        """
        result = []
        for index in range(num_items):
            try:
                result.append(self._calc_item(index))
            except NoStreamItemError:
                break
        return LazyStream(result)

    def first_or_else(self, or_else=None):
        """
        Returns the first item in the stream or, if the stream is empty,
        returns [or_else].
        """
        try:
            return self._calc_item(0)
        except NoStreamItemError:
            return or_else

    def last_or_else(self, or_else=None):
        """
        Returns the last item in the stream or, if the stream is empty,
        returns [or_else].
        """
        try:
            return self.reverse()._calc_item(0) # pylint: disable=protected-access
        except NoStreamItemError:
            return or_else

    def for_each(self, func):
        """
        Executes [func] on each item in the stream.  Doesn't return anything.
        """
        for item in self._lst:
            func(item)

    def flatten(self):
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

    def sort(self, key=None, reverse=False):
        """
        Sorts the steam given an optional [key] function.  Returns a new
        LazyStream.  This method forces processing of every item in the steam.
        """
        sorted_lst = sorted(self.to_list(), key=key, reverse=reverse)
        return LazyStream(sorted_lst)

    def map(self, func):
        """
        Replaces each item in the stream with func(item).  Returns a new
        LazyStream.
        """
        return _LazyMapStream(func, self)

    def filter(self, func):
        """
        Filters out items from the stream in which func(item) is False.
        Returns a new LazyStream.
        """
        return _LazyFilterStream(func, self)

    def reverse(self):
        """
        Reverses the order of the items in the stream.  Returns a new
        LazyStream.
        """
        return _LazyReverseStream(self)


class _LazyMapStream(LazyStream):
    """The Map implementation of a LazyStream"""
    def __init__(self, func, parent): # pylint: disable=super-init-not-called
        self._func = func
        self._parent = parent
        self._cache = {}

    def size(self):
        return self._parent.size()

    def _calc_item(self, index):
        if index not in self._cache.keys():
            self._cache[index] = self._func(self._parent._calc_item(index)) # pylint: disable=protected-access
        return self._cache[index]


class _LazyFilterStream(LazyStream):
    """The Filter implementation of a LazyStream"""
    def __init__(self, func, parent): # pylint: disable=super-init-not-called
        self._func = func
        self._parent = parent
        self._cache = {}
        self._parent_index = 0
        self._filter_index = 0
        self._size = -1 # not calculated yet

    def size(self):
        if self._size > -1:
            return self._size
        self._size = 0
        while True:
            try:
                self._calc_item(self._size)
                self._size += 1
            except NoStreamItemError:
                return self._size

    def _calc_item(self, index):
        if index in self._cache.keys():
            return self._cache[index]
        while self._parent_index < self._parent.size():
            item = self._parent._calc_item(self._parent_index) # pylint: disable=protected-access
            self._parent_index += 1
            if self._func(item):
                self._filter_index = index
                self._cache[self._filter_index] = item
                if self._filter_index == index:
                    return item
                else:
                    self._filter_index += 1
        raise NoStreamItemError()


class _LazyReverseStream(LazyStream):
    """The Reverse implemenation of a LazyStream"""
    def __init__(self, parent): # pylint: disable=super-init-not-called
        self._parent = parent

    def size(self):
        return self._parent.size()

    def _calc_item(self, index):
        return self._parent._calc_item(self._parent.size() - index - 1) # pylint: disable=protected-access


class _LazyFlattenStream(LazyStream):
    """The Flatten implementation of a LazyStream"""
    def __init__(self, parent): # pylint: disable=super-init-not-called
        self._parent = parent
        self._size = -1
        self._flattened_lst = None
        self._cache = []

    def size(self):
        return len(self._calc_flattened_list())

    def _calc_item(self, index):
        try:
            return self._calc_flattened_list()[index]
        except IndexError:
            raise NoStreamItemError()

    def _calc_flattened_list(self):
        if self._flattened_lst is None:
            self._flattened_lst = list(_list_flattener(self._parent.to_list()))
        return self._flattened_lst


def _list_flattener(lst):
    """Flattens a nested list"""
    for i in lst:
        if isinstance(i, (list, tuple)):
            for j in _list_flattener(i):
                yield j
        else:
            yield i


def stream(lst):
    """
    The main entry-point for creating a new stream.  Takes a list (lst) of
    items to populate the the new LazyStream.
    """
    if isinstance(lst, xrange): # xranges don't really work yet.
        lst = list(lst)
    return LazyStream(lst)
