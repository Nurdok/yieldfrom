"""Unit tests for ``yield From()``."""

import pytest
from yieldfrom import yieldfrom, From, Return


def test_basic_operation():
    """Test basic ``yield From()`` operation."""

    def subgen():
        yield 2
        yield 3

    @yieldfrom
    def gen():
        yield 1
        yield From(subgen())
        yield 4

    assert list(gen()) == [1, 2, 3, 4]


def test_return_value():
    """Test subgenerator return value."""

    def subgen():
        yield 2
        yield 3
        Return(100)

    @yieldfrom
    def gen():
        yield 1
        ret = (yield From(subgen()))
        yield 4
        yield ret

    assert list(gen()) == [1, 2, 3, 4, 100]


def test_nesting():
    """Test subgenerator nesting."""

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

    assert list(gen()) == [1, 2, 3, 4]


def test_throwing():
    """Test throwing exceptions into subgenerator and its handling."""

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

    ret = []
    try:
        gen_obj = gen()
        while True:
            i = gen_obj.next()
            if i == 2:
                i = gen_obj.throw(ValueError())
            ret.append(i)
    except StopIteration:
        pass

    assert ret == [1, 200, 3, 4]


def test_iterable():
    """Test regular iterable in ``yield From``."""

    @yieldfrom
    def gen():
        yield From([1, 2 ,3])
        yield [4, 5, 6]

    assert list(gen()) == [1, 2, 3, [4, 5, 6]]


def test_non_iterable():
    """Test non iterable passed to ``yield From``."""

    @yieldfrom
    def gen():
        yield 1
        yield From(ValueError)
        yield From(None)
        yield 2

    assert list(gen()) == [1, 2]


def test_throwing_handling():
    """Test throwing exceptions into subgenerator and handling in main."""

    def subgen():
        yield 1
        yield 2

    @yieldfrom
    def gen():
        try:
            yield From(subgen())
        except ValueError:
            yield 3

    ret = []
    try:
        gen_obj = gen()
        while True:
            i = gen_obj.next()
            if i == 1:
                i = gen_obj.throw(ValueError())
            ret.append(i)
    except StopIteration:
        pass

    assert ret == [3]


def test_exception_flow():
    """Test raising and catching exceptions between generators."""

    def subgen():
        yield 1
        raise ValueError()
        yield 100

    @yieldfrom
    def gen():
        try:
            yield From(subgen())
        except ValueError:
            yield 2
        yield 3

    assert list(gen()) == [1, 2, 3]


def test_non_generator_wrapping():
    """Test wrapping a non-generator function with ``yieldfrom``."""

    @yieldfrom
    def non_gen():
        return 42

    @yieldfrom
    def gen():
        yield From(non_gen())

    with pytest.raises(AttributeError) as excinfo:
        list(gen())

    assert 'next' in str(excinfo.value)
