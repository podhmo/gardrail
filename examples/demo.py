# -*- coding:utf-8 -*-

D = {"x": 10, "y": 20, "z": -30}


class Point:
    x = 10
    y = 20
    z = -30

from gardrail import (
    multi,
    Gardrail,
    NG,
    matched,
    single,
    share,
    container,
    subrail,
    collection,
    convert
)


class PointGardrail(Gardrail):
    @matched(["x", "y", "z"], path="__all__")
    def positive(self, values):
        for value in values:
            if value < 0:
                return NG("negative")

    @multi(["x", "y"], path="x")
    def equals(self, x, y):
        if x != y:
            return NG("oops")


class PairGardrail(Gardrail):
    left = subrail("left")(PointGardrail)
    right = subrail("right")(PointGardrail)


def positive(self, values):
    for value in values:
        if value < 0:
            return NG("negative")


def equals(self, x, y):
    if x != y:
        return NG("oops")


class Pair2Gardrail(Gardrail):
    @container
    class left:
        positive = matched(["x", "y", "z"], path="__all__")(positive)
        equals = multi(["x", "y"], path="x")(equals)

    @container
    class right:
        positive = matched(["x", "y", "z"], path="__all__")(positive)
        equals = multi(["x", "y"], path="x")(equals)


class PointListGardrail(Gardrail):
    @collection
    class points:
        positive = matched(["x", "y", "z"], path="__all__")(positive)
        equals = multi(["x", "y"], path="x")(equals)


print(PointGardrail()({"x": 10, "y": 10}))
print(PointGardrail()(D))
print(PairGardrail()({"left": D, "right": D}))
print(Pair2Gardrail()({"left": D, "right": D}))
print(PointListGardrail()({"points": [D, D, D]}))


class ABCDEFG(Gardrail):
    def __init__(self, value):
        self.value = value

    @container
    class a:
        @container
        class b:
            @container
            class c:
                @container
                class d:
                    @container
                    class e:
                        @single("f")
                        def f(self, g):
                            if g == self.value:
                                return NG("abcdefg")

print(ABCDEFG("g")({"a": {"b": {"c": {"d": {"e": {"f": "g"}}}}}}))


class Mode(Gardrail):
    @convert(["a_code", "b_code", "mode"])
    def code(self, params):
        params["code"] = params["{}_code".format(params["mode"])]

print(Mode()({"a_code": "aaaaa", "b_code": "b", "mode": "a"}))


# class Dispatch(Gardrail):
#     @dispatch({"a": foo, "b": foo})
#     def dispatch(self, cont, v):
#         return cont["a"](v)

