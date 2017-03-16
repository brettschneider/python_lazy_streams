Python lazy\_streams
====================

Inspired by Java 8's streams, this Python module provides a fluent syntax for
manipulating and querying Python lists.  It's called __lazy__\_streams because
it lazy-evaluates the requests to increase performance and decrease resource
requirements.

Here's a quick example:

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
implementation that depends only the Python standard library.

As you can see from the above example, you can stack multiple manipulations
on top of each other.  The module will optimize the execution to only perform
the operations on the elements of the list that are involved in the eventual
output.

Also, the original list will remain unchanged as the output of each operation
simply returns a delta from the original value.

Operations on a LazyStream can be categories into two groups:  Terminal
operations and Non-terminal operations.  Terminal operations result in a
concrete result (a value, a list, etc.).  Non-terminal operations will return
a new LazyStream.

Terminal operations
-------------------

__to\_list(threads=0)__ - Will convert the stream back to a list. Returns a
_list_.  If _threads_ is 0, to\_list will create the list serially on the
main thread.  If _threads_ is greater than 0, to\_list will be generated
in parallel using the number of threads specified.

    >>> print stream(range(10)).to_list()
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    >>>

__*NOTE:__ using threads is computationally expensive and won't
necessarily speed up your work.  It is intended to be used to speed up
time-consuming map and filter processes (making web service calls for
example).  If your map/filter functions aren't doing anything time-
sensitive, you'll probably get more speed leaving _threads_ at 0.

__to\_string(separator=', ', threads=0)__ - Will convert the list to a string
by joining the elements using the given separator (defaults to ', '). Returns
a _string_.

    >>> print stream(range(10)).to_string()
    '0, 1, 2, 3, 4, 5, 6, 7, 8, 9'
    >>> print stream(range(10)).to_string('-')
    '0-1-2-3-4-5-6-7-8-9'
    >>>

__first\_or\_else(or\_else=None)__ - Will return the first item in the resulting
list.  If the resulting list is empty, returns the value of _or\_else_.
Returns a _value_.

    >>> print stream([5, 6, 7]).first_or_else()
    5
    >>> print stream([]).first_or_else()
    None
    >> print stream([]).first_or_else(-1)
    -1
    >>>

__last\_or\_else(or\_else=None)__ - Will return the last item in the resulting
list.  If the resulting list is empty, returns the value of _or\_else_.
Returns a _value_.

    >>> print stream([5, 6, 7]).first_or_else()
    7
    >>> print stream([]).first_or_else()
    None
    >> print stream([]).first_or_else(-1)
    -1
    >>>

__reduce(func, threads=0)__ - Calls Python's _reduce_ function passing it the
given function and the resulting list of the stream. Returns a _value_.

    >>> print stream(range(5)).reduce(lambda x,y: x-y)
    -10
    >>>

__min(key=None, threads=0)__ - Sorts the list using the given sort key and then
returns the first item in the rsulting list. Returns a _value_.

    >>> print stream(range(3)).min()
    0
    >>> print stream(['Matilda', 'Tom', 'Sally']).min(key=lambda x: len(x))
    'Tom'
    >>>

__max(key=None, threads=0)__ - Sorts the list using the given sort key and then
returns the last item in the resulting list. Returns a _value_.

    >>> print stream(range(3)).max()
    2
    >>> print stream(['Matilda', 'Tom', 'Sally']).max(key=lambda x: len(x))
    'Matilda'
    >>>

__size(threads=0)__ - Returns the number of items in the Streams's resulting
list.

    >>> print stream([5, 6, 7]).size()
    3
    >>>


Non-terminal operations
-----------------------
Non-terminal operations return a new LazyStream as their result.  This allows
you to stack multiple operations up together.

    #!/usr/bin/env python
    from lazy_streams import stream

    names = stream(['Bob', 'Sally', 'Jane', 'Joe', 'Emily', 'Jake', 'John']) \
        .filter(lambda x: len(x) > 3) \
        .sort() \
        .map(lambda x: "First name: %s" % x) \
        .to_string("\n")
    print names

    ... outputs ...

    First name: Emily
    First name: Jake
    First name: Jane
    First name: John
    First name: Sally

__take(num\_items)__ - Will return a new LazyStream that only contains the
first _num_items_ item from the called upon stream.

    >>> print stream([1, 2, 3, 4]).take(2).to_list()
    [1, 2]
    >>>

__flatten()__ - Will flatten a list-of-lists to a flat list.

    >>> print stream([1, [2, 3], 4, [[5, 6], 7]]).flatten().to_list()
    [1, 2, 3, 4, 5, 6, 7]
    >>>

__sort(key=None, reverse=False)__ - Will return a sorted Stream using the given
key.  If _reverse_ is true, will reverse the sort.

    >>> print stream([3, 5, 7, 2, 4, 6]).sort().to_list()
    [2, 3, 4, 5, 6, 7]
    >>> print stream(['AAA', 'AA', 'AAA', 'A']).sort(key=lambda x: len(x), reverse=True).to_list()
    ['AAA', 'AAA', 'AA', 'A']

__map(func)__ - Will call _func_ on each item of the stream's list and return
the result.

    >>> print stream([2, 3, 4]).map(lambda x: x*2).to_list()
    [4, 6, 8]
    >>>

__filter(func)__ - Will call _func_ on each item of the stream's list and only
keep the ones where _func_ reutrns True.

    >>> print stream(['A', 'AAAAA', 'AAA', 'AA']).filter(lambda x: len(x) > 2).to_list()
    ['AAAAA', 'AAA']
    >>>

__reverse()__ - Will simply reverse the order of the items.  This operation does
not perform any sorting.  It simply mirrors the values.

    >>> print stream(['Gus', 'Joe', 'Sally', 'Mike', 'Jane']).reverse().to_list()
    ['Jane', 'Mike', 'Sally', 'Joe', 'Gus']
    >>>


Copyright (c) 2017, Steve Brettschneider.

License: MIT (see LICENSE for details)
