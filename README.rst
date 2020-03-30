===================
Python lazy-streams
===================

Inspired by Java 8's streams, this Python module provides a fluent syntax for
manipulating and querying Python lists.  It's called lazy-streams because
it *lazy* evaluates the requests to increase performance and decrease resource
requirements. Because of the lazy evaluation, lazy-streams can work on really
large data sets with relatively small delays.

Here's a quick example:

::

    >>> from lazy_streams import stream
    >>> s = stream(range(5000000)) \
    ...    .filter(lambda x: str(x)[0] == '3') \
    ...    .map(lambda x: -x) \
    ...    .map(lambda x: "Item: %s" % x) \
    ...    .take(75) \
    ...    .reverse()
    >>> print(s.first_or_else())
    Item: -363
    >>> print(s.take(5).to_list())
    ['Item: -363', 'Item: -362', 'Item: -361', 'Item: -360', 'Item: -359']
    >>> print(s.take(3).to_string())
    Item: -363, Item: -362, Item: -361


Lazy-streams is intended to be a small (single-file), light-weight, simple
implementation that relies on a mimimal set of dependencies.

As you can see from the above example, you can stack multiple manipulations
on top of each other.  The module will optimize the execution to only perform
the operations on the elements of the list that are involved in the eventual
output.

Also, the original list will remain unchanged as the output of each operation
simply returns a delta from the original value.

Documentation and more examples are available
`docs <https://github.com/brettschneider/python_lazy_streams/blob/master/README.md>`_.

