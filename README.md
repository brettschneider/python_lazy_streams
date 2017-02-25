python\_lazy\_streams
=====================

Inspired by Java 8's streams, this Python module provides a fluent syntax for
manipulating and querying Python lists.  It's called __lazy__\_streams because
it lazy-evaluates the requests to increase performance and decrease resource
requirements.

Example usage:

    >>> from lazy_streams import stream
    >>> data = range(100)
    >>> s = stream(data)
    >>> print s \
    ...     .reverse() \
    ...     .filter(lambda x: (x+1)%2 == 0) \
    ...     .map(lambda x: x*x) \
    ...     .map(lambda x: "Item %d" % x) \
    ...     .last_or_else('Nothing here')
    Item 1
    >>>

Lazy\_streams is intended to be a small (single-file), light-weight, simple
implementation the depends only the the Python standard library.

Copyright (c) 2017, Steve Brettschneider.

License: MIT (see LICENSE for details)
