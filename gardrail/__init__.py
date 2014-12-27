# -*- coding:utf-8 -*-
import sys
import logging
logger = logging.getLogger(__name__)
from functools import partial


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


class Failure(Exception):
    @property
    def errors(self):
        return self.args[0]

    def __repr__(self):
        return "Failure[{!r}]".format(self.errors)

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
    def __init__(self, names, method, msg=None, path=None, strict=False):
        self.names = names
        self.method = method
        self._v_count = counter()
        self.msg = msg
        self.path = path
        self.strict = strict

    def validate_context(self, context):
        params = context.params
        if all(params.get(name) is not None for name in self.names):
            result = self.method(context.scope, *(params[name] for name in self.names))
            context.scope.dispatch(context, self, result)
        else:
            if self.strict:
                ng = context.scope.on_missing(self.names, self.__class__.__name__, self.method)
                context.scope.dispatch(context, self, ng)
            logger.debug("names=%s not found", self.names)


class Dispatch(object):
    def __init__(self, names, method, strict=False):
        self.names = names
        self.dispatch_method = method
        self._v_count = counter()
        self.strict = strict

    def dispatch_validate(self, rail, child, path=[], context=None):
        if not isinstance(path, (list, tuple)):
            path = [path]
        N = len(path)

        original = context.params
        context.params = child
        context.path.extend(path)
        rail.validate_context(context)
        for i in range(N):
            context.path.pop()
        context.params = original

    def validate_context(self, context):
        params = context.params
        if not self.names:
            check_fn = partial(self.dispatch_validate, context=context)
            return self.dispatch_method(context.scope, check_fn, params)
        if all(params.get(name) is not None for name in self.names):
            check_fn = partial(self.dispatch_validate, context=context)
            self.dispatch_method(context.scope, partial(self.dispatch_validate, context=context), params)


class Matched(object):
    def __init__(self, names, method, path=None, msg=None, strict=False):
        self.names = names
        self.method = method
        self.path = path
        self._v_count = counter()
        self.msg = msg
        self.strict = strict

    def validate_context(self, context):
        params = context.params
        if any(params.get(name) is not None for name in self.names):
            result = self.method(context.scope, [params[name] for name in self.names if params.get(name) is not None])
            context.scope.dispatch(context, self, result)
        else:
            if self.strict:
                ng = context.scope.on_missing(self.names, self.__class__.__name__, self.method)
                context.scope.dispatch(context, self, ng)
            logger.debug("names=%s not found", self.names)


class container(object):
    def __init__(self, cls):
        self.cls = cls
        self.names = [cls.__name__]  # for common interface
        self.validators = [v for v in cls.__dict__.values() if is_validator(v)]
        self.validators.sort(key=lambda o: o._v_count)
        self._v_count = counter()

    def validate_context(self, context):
        if self.names[0] not in context.params:
            if getattr(self.cls, "strict", False):
                ng = context.scope.on_missing(self.names, self.__class__.__name__, self.cls)
                context.scope.dispatch(context, self, ng)
            logger.debug("names=%s not found", self.names)
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
        self.cls = cls
        self.names = [cls.__name__]  # for common interface
        self.validators = [v for v in cls.__dict__.values() if is_validator(v)]
        self.validators.sort(key=lambda o: o._v_count)
        self._v_count = counter()

    def validate_context(self, context):
        if self.names[0] not in context.params:
            if getattr(self.cls, "strict", False):
                ng = context.scope.on_missing(self.names, self.__class__.__name__, self.cls)
                context.scope.dispatch(context, self, ng)
            logger.debug("names=%s not found", self.names)
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


class Subrail(object):
    def __init__(self, name, target, strict=False):
        self.names = [name]
        self.Gardrail = target
        self._v_count = counter()
        self.strict = strict

    def validate_context(self, context):
        if self.names[0] not in context.params:
            if self.strict:
                ng = context.scope.on_missing(self.names, self.__class__.__name__, self.Gardrail)
                context.scope.dispatch(context, self, ng)
            logger.debug("names=%s not found", self.names)
            return

        context.path.append(self.names[0])
        original = context.params
        context.params = context.params[self.names[0]]

        for v in self.Gardrail.validators:
            v.validate_context(context)

        context.params = original
        context.path.pop()


class Convert(object):
    def __init__(self, names, method, msg=None, strict=False, path=None):
        self.names = names
        self.method = method
        self._v_count = counter()
        self.msg = msg
        self.strict = strict
        self.path = path

    def validate_context(self, context):
        params = context.params
        if not self.names:
            return self.method(context.scope, params)
        else:
            if all(params.get(name) is not None for name in self.names):
                return self.method(context.scope, params)
            elif self.strict:
                ng = context.scope.on_missing(self.names, self.__class__.__name__, self.method)
                context.scope.dispatch(context, self, ng)


def single(name, msg=None, strict=False):
    return partial(Multi, [name], msg=msg, strict=strict)


def multi(names, path=None, msg=None, strict=False):
    assert isinstance(names, (list, tuple))
    return partial(Multi, names, msg=msg, path=path, strict=strict)


def dispatch(names=None, strict=False):
    return partial(Dispatch, names, strict=strict)


def matched(names, path, msg=None, strict=False):
    assert isinstance(names, (list, tuple))
    return partial(Matched, names, path=path, msg=msg, strict=strict)


def subrail(name, strict=False):
    return partial(Subrail, name, strict=strict)


def convert(names=None, msg=None, strict=False, path=None):
    return partial(Convert, names, path=path, msg=msg, strict=strict)


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
        ancestor_validators = set(v for c in bases for v in getattr(c, "validators", []) if is_validator(v))
        validators = set([v for v in attrs.values() if is_validator(v)])
        validators = list(ancestor_validators | validators)
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
        return super(GardrailMeta, self).__new__(self, name, bases, attrs)


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
        raise Failure(errors)

    def on_missing(self, names, wrapname, fn):
        return NG("fields:{} not found: {}.{}".format(names, wrapname, fn))

Gardrail = GardrailMeta("Gardrail", (_Gardrail, ), {})
