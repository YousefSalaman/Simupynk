"""
This module extends the standard library's abc module's functionality by
verifying abstractmethods have been overridden with the same type as in the
ABC. The classes in this module can be used in the same manner as the Python's
abc module.

This should work fine classmethods, staticmethods, properties, or any other
built-in class in the Python repository. For custom classes like classproperty,
you'll have to add a decorator like, for example, abstractclassmethod to make
this functionality work correctly.

The ABCMeta metaclass was used to build the metaclass TypeABCMeta to detect
type consistency at class creation, so it gurantees the user overrides the
interface's method with the correct type. The new metaclass was mixed in with the classproperty metaclass,
CPEnabledMeta, to fuse both features together in case someone wants to use both
at the same time.

The classes on this module are based on the following source:

    [1] Overall structure was based on the abc module:
        https://github.com/python/cpython/blob/master/Lib/abc.py
"""

from abc import ABCMeta
from inspect import isabstract
from Simupynk.Simupynk.utils.cls_prop import CPEnabledMeta, classproperty


def _find_ABC_from_bases(bases):

    for base_cls in bases:
        if isabstract(base_cls):
            return base_cls
    return None


def _verify_type_override(cls, abs_cls):

    for abs_method_name in abs_cls.__abstractmethods__:
        method = cls.__dict__.get(abs_method_name)
        abs_method = abs_cls.__dict__[abs_method_name]
        if method is None:
            _raise_standard_abc_error(cls, abs_cls)
        else:
            _check_type_consistency(method, abs_method, abs_method_name)


def _raise_standard_abc_error(cls, abs_cls):

    non_overridden_methods = [method for method in abs_cls.__abstractmethods__ if cls.__dict__.get(method) is None]
    raise TypeError(f"Can't instantiate abstract class {cls.__name__} "
                    f"with abstract methods {', '.join(non_overridden_methods)}")


def _check_type_consistency(method, abs_method, abs_method_name):

    method_type = type(method)
    abs_method_type = type(abs_method)
    if all(method_type is not cls for cls in abs_method_type.__mro__ if cls is not object):
        possible_types = [cls.__name__ for cls in abs_method_type.__mro__ if cls is not object]
        raise TypeError(f'The method "{abs_method_name}" must be '
                        f'one of the following types: {", ".join(possible_types)}.')


class abstractclassproperty(classproperty):
    """
    A decorator indicating abstract classproperties.

    It's a direct copy of the depracated "abstractproperty" class from the abc
    module. This has to be implemented to make the classproperty class work for
    ABCs. In other words, do not chain classproperty and abstract property
    since that won't yield the desired result.

    For usage of this class, look at the test scripts for this class.
    """

    __isabstractmethod__ = True


class TypeABCMeta(ABCMeta):
    """
    A metaclass to verify ABCs and their direct child classes have the same
    types when overridden. It does this when a new class is created, so it
    prevents the user from using the abstractmethod unless they have overridden
    the abstractmethod with the correct class.
    """

    def __new__(mcls, name, bases, namespace, **kwargs):

        cls = super().__new__(mcls, name, bases, namespace, **kwargs)
        abs_cls = _find_ABC_from_bases(bases)  # The ABC that contains the relevant abstract methods
        if abs_cls is not None:
            _verify_type_override(cls, abs_cls)
        return cls


class TypeABC(metaclass=TypeABCMeta):
    """
    A helper class for the TypeABCMeta metaclass. It enables ABCs that verify
    if its child classes have overridden the abstractmethods with methods that
    have the correct type just by inheriting from this class.
    """

    __slots__ = ()


class CPEnabledTypeABCMeta(CPEnabledMeta, TypeABCMeta):
    """
    A metaclass that mixes the functionality of using classproperties and type
    checking for ABCs.
    """


class CPEnabledTypeABC(metaclass=CPEnabledTypeABCMeta):
    """
    A helper class for CPEnabledTypeABCMeta that enables using classproperties
    and type checking for ABCs just by inhereting from this class directly.
    """

    __slots__ = ()