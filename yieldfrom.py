"""Backporting of the ``yield from`` semantic from Python 3.x.

If you want to nest generators in Python 3.x, you can use the ``yield from``
keywords. This allows you to automatically iterate over sub-generators and
transparently pass exceptions and return values from the top level caller
to the lowest generator.

.. code-block:: python

    def subgen():
        yield 2
        yield 3
        
    def gen():
        yield 1
        yield from subgen()  # Python 3.x only
        yield 4
        
    def main():
        for i in gen():
            print i,
            
    >>> main()
    ... 1 2 3 4
    
This functionality is not available in Python 2.x, and we emulate it using the
:py:func:`yieldfrom` decorator and the helper :py:class:`From` class:

.. code-block:: python

    from yieldfrom import yieldfrom, From

    def subgen():
        yield 2
        yield 3
        
    @yieldfrom
    def gen():
        yield 1
        yield From(subgen())
        yield 4
        
    def main():
        for i in gen():
            print i,
            
    >>> main()
    ... 1 2 3 4
    
Advanced usage allows returning a value from the subgenerator using 
:py:exc:`StopIteration`. Using :py:func:`Return` does this conveniently:

.. code-block:: python

    from yieldfrom import yieldfrom, From, Return
    
    def subgen():
        yield 2
        yield 3
        Return(100)  # Raises `StopIteration(100)`
        
    @yieldfrom
    def gen():
        yield 1
        ret = (yield From(subgen()))
        yield 4
        yield ret
        
    def main():
        for i in gen():
            print i,
            
    >>> main()
    ... 1 2 3 4 100

Subgenerators can be nested on multiple levels, each one requiring additional
decoration by :py:func:`yieldfrom`:

.. code-block:: python

    def subsubgen():
        yield 2
        
    @yieldfrom
    def subgen():
        yield From(subsubgen())
        yield 3
        
    @yieldfrom
    def gen():
        yield 1
        yield From(subgen())
        yield 4
        
    def main():
        for i in gen():
            print i,
            
    >>> main()
    ... 1 2 3 4
    
Exceptions thrown into the top-level generator can be handled in relevant
subgenerators:

.. code-block:: python

    def subsubgen():
        try:
            yield 2
        except ValueError:
            yield 200
            
    @yieldfrom
    def subgen():
        yield From(subsubgen())
        yield 3
        
    @yieldfrom
    def gen():
        yield 1
        yield From(subgen())
        yield 4
        
    def main():
        try:
            g = gen()
            while True:
                i = g.next()
                if i == 2:
                    i = g.throw(ValueError())
            print i,
        except StopIteration:
            pass
            
    >>> main()
    ... 1 200 3 4
    
Note that if you use ``yield From()`` on a simple iterable (``list``, 
``tuple``, etc) then the individual members of the iterator will be yielded on
each iteration (perhaps in that case you need the usual ``yield``).

.. code-block:: python

    @yieldfrom
    def gen():
        yield From([1, 2, 3])
        yield [1, 2, 3]
        
    def main():
        for i in gen():
            print i
            
    >>> main()
    ... 1
    ... 2
    ... 3
    ... [1, 2, 3]
        
Passing non-iterable objects to :py:class:`From` will result in an empty
generator that does nothing.
    
.. code-block:: python

    @yieldfrom
    def gen():
        yield From(None)
        yield 1
        
    def main():
        for i in gen():
            print i
            
    >>> main()
    ... 1
    
This module is an adaptation of the following Python recipe:
http://code.activestate.com/recipes/576727
Modifications include bug fixes in exception handling, naming, documentation,
handling of empty generators, etc.

"""

__version__ = '1.0.3'
__all__ = ('yieldfrom', 'From', 'Return')


import sys
import functools


def Return(return_value):
    """Return a value from a generator by raising ``StopIteration``."""
    raise StopIteration(return_value)


class From(object):
    """Helper class to wrap subiterators.
    
    If the expression wrapped is not iterable, holds an empty generator.
    
    """

    def __init__(self, iterable_expression):
        try:
            self.iterator = iter(iterable_expression)
        except TypeError:
            self.iterator = iter([])


def get_stop_iteration_value(e_stop):
    return e_stop.args[0] if e_stop.args else None


def close_safely(gen):
    """Close generator, ignore if has no ``close`` attribute."""
    try:
        _close = gen.close
    except AttributeError:
        pass
    else:
        _close()


def yieldfrom(generator_func):
    """Decorate a function to enable ``yield From(generator)``.
    
    Implements PEP380 (``yield from``) in Python 2.x.
    
    """
    @functools.wraps(generator_func)
    def wrapper(*args, **kwargs):
        # gen in the function body that is decorated by `yieldfrom`. (it is
        # a generator, too).
        gen = generator_func(*args, **kwargs)

        try:
            # First poll of `gen`.
            item = gen.next()

            # OUTER loop: iterate over all the values yielded by `gen`.
            while True:
                # ------------------------------------------------------------
                # Handling normal `yield`
                # ------------------------------------------------------------
                if not isinstance(item, From):
                    try:
                        sent = (yield item)
                    except Exception:
                        # Caller did `throw`. We push the exception back into
                        # `gen` and get the next item.
                        item = gen.throw(*sys.exc_info())
                    else:
                        # No exception was thrown, push the return value into
                        # `gen` and get the next item.
                        item = gen.send(sent)

                # ------------------------------------------------------------
                # Handling `yield From()`
                # ------------------------------------------------------------
                else:
                    subgen = item.iterator
                    try:
                        # First poll of `subgen`.
                        subitem = subgen.next()
                    except StopIteration as e_stop:
                        # `subgen` exhausted on first poll. Extract return
                        # value passed by `StopIteration`, push it into `gen`
                        # and get the next item.
                        item = gen.send(get_stop_iteration_value(e_stop))
                    else:
                        # INNER loop: iterate on values yielded by
                        # subgenerator.
                        while True:
                            try:
                                # Yield what the subgenerator did.
                                sent = (yield subitem)
                            except GeneratorExit:
                                # Higher level caller called `close()`.
                                # Close the subgenerator if possible.
                                close_safely(subgen)
                                raise
                            except BaseException:
                                # Higher level caller called `throw()`.
                                try:
                                    _throw = subgen.throw
                                except AttributeError:
                                    # `subgen` doesn't have a `throw()` method.
                                    # We consider it exhausted, so we push the
                                    # exception into `gen` instead, and get
                                    # the next item.
                                    item = gen.throw(*sys.exc_info())
                                    break  # Restart OUTER loop.
                                else:
                                    try:
                                        # Push the exception into `subgen` and
                                        # get the next subitem.
                                        subitem = _throw(*sys.exc_info())
                                    except StopIteration as e_stop:
                                        # `subgen` is exhausted. Retrieve its
                                        # return value, push it into `gen` and
                                        # get the next item.
                                        item = gen.send(
                                            get_stop_iteration_value(e_stop))
                                        break  # Restart OUTER loop.
                                    except BaseException:
                                        # `subgen` did not handle the thrown
                                        # exception (or raised a different
                                        # one). We give `gen` a chance to
                                        # handle the raised exception.
                                        item = gen.throw(*sys.exc_info())
                                        # Restart the OUTER loop because
                                        # `subgen` raised an exception and
                                        # `gen` caught it.
                                        break
                                    else:
                                        continue  # Restart INNER loop
                            else:
                                try:
                                    # Re-poll `subgen`
                                    # It would be possible to just call
                                    # `send()` even when `sent` is None,
                                    # however, for non-generator iterables this
                                    # won't work.
                                    if sent:
                                        subitem = subgen.send(sent)
                                    else:
                                        subitem = subgen.next()
                                except StopIteration as e_stop:
                                    # `subgen` is exhausted. Retrieve its
                                    # return value, push it into `gen` and
                                    # get the next item.
                                    item = gen.send(
                                        get_stop_iteration_value(e_stop))
                                    break  # Restart OUTER loop.
                                except BaseException:
                                    # `subgen` raised an exception.
                                    # We give `gen` a chance to
                                    # handle the raised exception.
                                    item = gen.throw(*sys.exc_info())
                                    # Restart the OUTER loop because
                                    # `subgen` raised an exception and
                                    # `gen` caught it.
                                    break
                                else:
                                    continue  # Restart INNER loop

        finally:
            # `gen` raised an exception or caller called `close()` or generator
            # was garbage collected.
            # Close the generator if possible.
            close_safely(gen)

    return wrapper
