# -*- coding:utf-8 -*-
from gardrail import Gardrail, NG, multi, subrail, dispatch, share, Failure, single


class Balanced(Gardrail):
    @multi(["min", "max"])
    def balanced(self, min, max):
        if min > max:
            return NG("not {} < {}".format(min, max))

    @dispatch()
    def rec(self, check, params):
        if "children" not in params:
            return

        for i, child in enumerate(params["children"]):
            check(self, child, path=["children", i])

# failure level 1
try:
    Balanced()({"min": 100, "max": 10})
except Failure as e:
    print(e.errors)

# failure level 2
try:
    Balanced()({"min": 1, "max": 100, "children": [{"min": 50, "max": 5}]})
except Failure as e:
    print(e.errors)

# failure level 3
try:
    Balanced()({"min": 1, "max": 100, "children": [{"min": 5, "max": 50, "children": [{"min": 25, "max": 10}]}]})
except Failure as e:
    print(e.errors)


"""
Color(name=["red", "blue", "green"])
Color(r=0~255, g=0~255, b=0~255)
"""


class ColorName(Gardrail):
    @single("name", strict=True)
    def name(self, name):
        if name not in ["red", "blue", "green"]:
            return NG("invalid color: {}".format(name))


class ColorTriple(Gardrail):
    @share(single("r", strict=True),
           single("g", strict=True),
           single("b", strict=True))
    def range(self, value):
        if not (0 <= value <= 255):
            return NG("invalid color: {}".format(value))


class Color(Gardrail):
    def __init__(self, mode):
        self.mode = mode

    @dispatch()
    def color(self, check, params):
        if self.mode == "name":
            return check(ColorName(), params)
        else:
            return check(ColorTriple(), params)

print(Color("name")({"name": "red"}))
try:
    Color("name")({"name": "purple"})
except Failure as e:
    print(e.errors)
try:
    Color("name")({"r": 100, "g": 100, "b": 100})
except Failure as e:
    print(e.errors)

print(Color("tri")({"r": 100, "g": 100, "b": 100}))
try:
    Color("tri")({"r": 100, "g": 100, "b": 300})
except Failure as e:
    print(e.errors)
try:
    Color("tri")({"name": "red"})
except Failure as e:
    print(e.errors)
