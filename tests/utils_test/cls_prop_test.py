from pyrunner.utils.cls_prop import classproperty, CPEnabled, CPEnabledMeta
import pytest


class Foo(CPEnabled):  # testing CPEnabled
    _bar = 0

    @classproperty
    @classmethod
    def bar(cls):
        """
        Test class property
        """
        return cls._bar

    @bar.setter
    def bar(cls, value):
        cls._bar = value

    @bar.getter
    def bar(cls):
        return 1

    @bar.deleter
    @classmethod
    def bar(cls):
        print("Deleting...")
        del cls._bar


class FooMeta(metaclass=CPEnabledMeta):  # testing CPEnabledMeta
    _bar = 0

    @classproperty
    @classmethod
    def bar(cls):
        """
        Test class property
        """
        return cls._bar

    @bar.setter
    def bar(cls, value):
        cls._bar = value

    @bar.getter
    def bar(cls):
        return 1

    @bar.deleter
    @classmethod
    def bar(cls):
        print("Deleting...")
        del cls._bar

def test_getter():
    object = Foo()
    assert object.bar == 1, "The value of the cls should be 1."

    object = FooMeta()
    assert object.bar == 1, "The value of the cls should be 1."

def test_setter():
    object = Foo()
    object.bar = 1
    assert object.bar == 1, "The expected result is 1"

    Foo.bar = 2
    assert Foo.bar, 1 == "The expected result is 1"

    object = FooMeta()
    object.bar = 1
    assert object.bar == 1, "The expected result is 1"
    Foo.bar = 2
    assert Foo.bar == 1, "The expected result is 1"

def test_del():
    # testing switch value error
    with pytest.raises(AttributeError):
        object = Foo()
        del object.bar
        print(Foo._bar)  # It's suppose to give an error since the property is deleted by the deleter
        print(Foo.bar)  # This will also yield an error

        object = FooMeta()
        del object.bar
        print(Foo._bar)  # It's suppose to give an error since the property is deleted by the deleter
        print(Foo.bar)  # This will also yield an error
