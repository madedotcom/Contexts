import inspect
import os
import re
import types
from collections import namedtuple
from .. import errors


SpecialMethods = namedtuple("SpecialMethods", ['setups', 'actions', 'assertions', 'teardowns'])

establish_re = re.compile(r"(^|_)([Ee]stablish|[Cc]ontext|[Gg]iven)")
because_re = re.compile(r"(^|_)([Bb]ecause|[Ww]hen|[Ss]ince|[Aa]fter)")
should_re = re.compile(r"(^|_)([Ss]hould|[Ii]t|[Mm]ust|[Ww]ill|[Tt]hen)")
cleanup_re = re.compile(r"(^|_)[Cc]leanup")
class_re = re.compile(r"([Ss]pec|[Ww]hen)")


class ClassFinder(object):
    def find_specs_in_modules(self, modules):
        for module in modules:
            for context in self.find_specs_in_module(module):
                yield context

    def find_specs_in_module(self, module):
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if class_re.search(name):
                yield cls()


class MethodFinder(object):
    def __init__(self, spec):
        self.spec = spec

    def find_special_methods(self):
        return SpecialMethods(self.find_setups(),
                              self.find_actions(),
                              self.find_assertions(),
                              self.find_teardowns())

    def find_setups(self):
        return self.find_methods_matching(establish_re, top_down=True, one_per_class=True)

    def find_actions(self):
        return self.find_methods_matching(because_re, one_only=True, one_per_class=True)

    def find_assertions(self):
        return self.find_methods_matching(should_re)

    def find_teardowns(self):
        return self.find_methods_matching(cleanup_re, one_per_class=True)

    def find_methods_matching(self, regex, *, top_down=False, one_only=False, one_per_class=False):
        found = []
        mro = self.spec.__class__.__mro__
        classes = reversed(mro) if top_down else mro
        for cls in classes:
            found.extend(self.find_methods_on_class_matching(cls, regex, one_only or one_per_class))
            if one_only and found:
                break
        return found

    def find_methods_on_class_matching(self, cls, regex, one_per_class):
        found = []
        for name, val in cls.__dict__.items():
            if not regex.search(name):
                continue
            if callable(val):
                method = types.MethodType(val, self.spec)
                found.append(method)
            elif isinstance(val, classmethod):
                method = getattr(cls, name)
                found.append(method)
            elif isinstance(val, staticmethod):
                method = getattr(cls, name)
                found.append(method)

        if one_per_class:
            assert_single_method_of_given_type(cls, found)

        return found


def assert_single_method_of_given_type(cls, found):
    if len(found) > 1:
        msg = "Context {} has multiple methods of the same type:\n".format(cls.__qualname__)
        msg += ", ".join([meth.__func__.__name__ for meth in found])
        raise errors.TooManySpecialMethodsError(msg)