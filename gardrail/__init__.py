# -*- coding:utf-8 -*-
import sys
import logging
logger = logging.getLogger(__name__)
from functools import partial
from collections import namedtuple


# 本当はnamedtupleみたいなものがほしい
class Context(object):
    def __init__(self, ob, scope, status, params, errors, path):
        self.ob = ob
        self.scope = scope
        self.status = status
        self.params = params
        self.errors = errors
        self.path = path

    __slots__ = ("ob", "scope", "status", "params", "errors", "path")


Failure = namedtuple("Failure", "errors")

OK = None


class NG(object):
    def __bool__(self):
        return False

    def __init__(self, msg, path=None):
        self.msg = msg
        self.path = path


class Interrupt(NG):
    pass


def is_validator(v):
    return hasattr(v, "_v_count")


class Counter(object):
    def __init__(self):
        self.i = 0

    def __call__(self):
        self.i += 1
        return self.i

counter = Counter()


class Multi(object):
    def __init__(self, names, method, msg=None, path=None):
        self.names = names
        self.method = method
        self._v_count = counter()
        self.msg = msg
        self.path = path

    def validate_context(self, context):
        params = context.params
        if all(params.get(name) is not None for name in self.names):
            result = self.method(context.scope, *(params[name] for name in self.names))
            context.scope.dispatch(context, self, result)
        else:
            logger.debug("names=%s is not found", self.names)


class Matched(object):
    def __init__(self, names, method, msg=None):
        self.names = names
        self.method = method
        self._v_count = counter()
        self.msg = msg

    def validate_context(self, context):
        params = context.params
        if any(params.get(name) is not None for name in self.names):
            result = self.method(context.scope, [(name, params[name]) for name in self.names if params.get(name) is not None])
            context.scope.dispatch(context, self, result)
        else:
            logger.debug("names=%s is not found", self.names)


class container(object):
    def __init__(self, cls):
        self.names = [cls.__name__]  # for common interface
        self.validators = [v for v in cls.__dict__.values() if is_validator(v)]
        self.validators.sort(key=lambda o: o._v_count)
        self._v_count = counter()

    def validate_context(self, context):
        if self.names[0] not in context.params:
            logger.debug("names=%s is not found", self.names)
            return

        context.path.append(self.names[0])
        original = context.params
        context.params = context.params[self.names[0]]
        for v in self.validators:
            v.validate_context(context)
        context.params = original
        context.path.pop()


class collection(object):
    def __init__(self, cls):
        self.names = [cls.__name__]  # for common interface
        self.validators = [v for v in cls.__dict__.values() if is_validator(v)]
        self.validators.sort(key=lambda o: o._v_count)
        self._v_count = counter()

    def validate_context(self, context):
        if self.names[0] not in context.params:
            logger.debug("names=%s is not found", self.names)
            return

        context.path.append(self.names[0])
        original = context.params
        for i, child in enumerate(context.params[self.names[0]]):
            context.path.append(i)
            context.params = child
            for v in self.validators:
                v.validate_context(context)
            context.path.pop()
        context.params = original
        context.path.pop()


class Rail(object):
    def __init__(self, name, target):
        self.names = [name]
        self.Gardrail = Gardrail
        self._v_count = counter()

    def validate_context(self, context):
        if self.names[0] not in context.params:
            logger.debug("names=%s is not found", self.names)
            return

        context.path.append(self.names[0])
        original = context.params
        context.params = context.params[self.names[0]]
        for v in self.Gardrail.validators:
            v.validate_context(context)
        context.params = original
        context.path.pop()


class Convert(object):
    def __init__(self, names, method, msg=None):
        self.names = names
        self.method = method
        self._v_count = counter()
        self.msg = msg

    def validate_context(self, context):
        params = context.params
        if not self.names:
            return self.method(context.scope, params)
        else:
            if all(params.get(name) is not None for name in self.names):
                return self.method(context.scope, params)


def single(name, msg=None):
    return partial(Multi, [name], msg=msg)


def multi(names, msg=None, path=None):
    assert isinstance(names, (list, tuple))
    return partial(Multi, names, msg=msg, path=path)


def matched(names, msg=None):
    assert isinstance(names, (list, tuple))
    return partial(Matched, names, msg=msg)


def rail(name):
    return partial(Rail, name)


def convert(names=None, msg=None):
    return partial(Convert, names, msg=msg)


def share(*factories):
    cls_env = sys._getframe(1).f_locals

    def wrapper(method):
        validations = []
        for f in factories:
            name = "{}{}".format(method.__name__, counter())
            v = f(method)
            cls_env[name] = v
            validations.append(v)
        return validations
    return wrapper


class _Status(object):
    def __init__(self, status):
        self.status = status

    def __call__(self, status):
        self.status = status

    def __bool__(self):
        return self.status
    __nonzero__ = __bool__


class GardrailMeta(type):
    def __new__(self, name, bases, attrs):
        validators = [v for v in attrs.values() if is_validator(v)]
        validators.sort(key=lambda o: o._v_count)
        attrs["validators"] = validators

        def __call__(self, ob):
            status = _Status(True)
            params, errors = self.configure(ob)
            if errors:
                return self.on_failure(ob, params, errors)

            context = Context(ob=ob, scope=self, status=status, params=params, errors=errors, path=[])
            self.validate_context(context)

            if status:
                return self.on_success(ob, params)
            else:
                return self.on_failure(ob, params, errors)

        attrs["__call__"] = __call__
        attrs["validate"] = __call__
        return super().__new__(self, name, bases, attrs)


class _Gardrail(object):
    def validate_context(self, context):
        for v in self.validators:
            v.validate_context(context)

    def configure(self, params):
        return params, {}

    def dispatch(self, context, validator, result):
        if result is OK:
            return

        if hasattr(result, "msg"):  # NG
            context.status(False)
            self.add_error(context.path, validator, result, context.errors)
            if isinstance(result, Interrupt):
                self.on_failure(context.ob, context.params, context.errors)

    def add_error(self, path, validator, ng, errors):
        current = getattr(ng, "path", None)
        if current is None:
            current = getattr(validator, "path", None) or [validator.names[0]]

        if not isinstance(current, (tuple, list)):
            current = [current]

        if path:
            path = path + current
        else:
            path = current

        target = errors
        for p in path[:-1]:
            try:
                target = target[p]
            except KeyError:
                target[p] = {}
                target = target[p]
        try:
            target[path[-1]].append(ng.msg)
        except KeyError:
            target[path[-1]] = []
            target[path[-1]].append(ng.msg)

    def on_success(self, _, params):
        return params

    def on_failure(self, _, params, errors):
        return Failure(errors=errors)


Gardrail = GardrailMeta("Gardrail", (_Gardrail, ), {})
