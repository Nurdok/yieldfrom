A backport of the `yield from` semantic from Python 3.x to Python 2.7

If you want to nest generators in Python 3.x, you can use the ``yield from``
keywords. This allows you to automatically iterate over sub-generators and
transparently pass exceptions and return values from the top level caller
to the lowest generator.

```.py
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
```
    
This functionality is not available in Python 2.x, and we emulate it using the
`yieldfrom` decorator and the helper `From` class:

```.py
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
```
    
Advanced usage allows returning a value from the subgenerator using 
`StopIteration`. Using `Return` does this conveniently:

```.py
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
```

Subgenerators can be nested on multiple levels, each one requiring additional
decoration by `yieldfrom`:

```.py
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
```
    
Exceptions thrown into the top-level generator can be handled in relevant
subgenerators:

```.py
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
```
    
Note that if you use `yield From()` on a simple iterable (`list`, 
`tuple`, etc) then the individual members of the iterator will be yielded on
each iteration (perhaps in that case you need the usual `yield`).

```.py
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
```
        
Passing non-iterable objects to `From` will result in an empty
generator that does nothing.
    
```.py
@yieldfrom
def gen():
    yield From(None)
    yield 1

def main():
    for i in gen():
        print i

>>> main()
... 1
```
    
This module is an adaptation of the following Python recipe:
http://code.activestate.com/recipes/576727  
Modifications include bug fixes in exception handling, naming, documentation,
handling of empty generators, etc.
