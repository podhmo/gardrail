# -*- coding:utf-8 -*-
import unittest
from evilunit import test_target
from gardrail import Gardrail


@test_target("gardrail:multi")
class MultiTests(unittest.TestCase):
    def _makeOne(self):
        from gardrail import NG

        class G(Gardrail):
            deco = self._getTarget()

            @deco(["x", "y"])
            def difference_is_small(self, x, y):
                if (x - y) * (x - y) > 10:
                    return NG("oops")
        return G()

    def test_success(self):
        params = {"x": 10, "y": 10}
        target = self._makeOne()
        result = target(params)
        self.assertEqual(result, params)

    def test_success__if_paramaters_is_not_matched(self):
        params = {}
        target = self._makeOne()
        result = target(params)
        self.assertEqual(result, params)

    def test_failure(self):
        from gardrail import Failure
        params = {"x": 10, "y": 20}
        target = self._makeOne()
        with self.assertRaises(Failure) as e:
            target(params)
        self.assertEqual(e.exception.errors, {"x": ["oops"]})


@test_target("gardrail:matched")
class MatchedTests(unittest.TestCase):
    def _makeOne(self):
        from gardrail import NG

        class G(Gardrail):
            deco = self._getTarget()

            @deco(["x", "y"], path="__all__")
            def difference_is_small(self, values):
                if not all(e > 0 for e in values):
                    return NG("oops")
        return G()

    def test_success(self):
        params = {"x": 10, "y": 10}
        target = self._makeOne()
        result = target(params)
        self.assertEqual(result, params)

    def test_success__if_paramaters_is_not_matched(self):
        params = {}
        target = self._makeOne()
        result = target(params)
        self.assertEqual(result, params)

    def test_failure(self):
        from gardrail import Failure
        params = {"x": 10, "y": -20}
        target = self._makeOne()
        with self.assertRaises(Failure) as e:
            target(params)
        self.assertEqual(e.exception.errors, {"__all__": ["oops"]})


@test_target("gardrail:subrail")
class SubrailTests(unittest.TestCase):
    def _makeOne(self):
        from gardrail import multi, NG

        class PositivePoint(Gardrail):
            @multi(["x", "y"])
            def positive(self, x, y):
                if not (x > 0 and y > 0):
                    return NG("oops")

        class G(Gardrail):
            deco = self._getTarget()
            left = deco("left")(PositivePoint)
            right = deco("right")(PositivePoint)
        return G()

    def test_success(self):
        params = {"left": {"x": 10, "y": 10},
                  "right": {"x": 10, "y": 10}}
        target = self._makeOne()
        result = target(params)
        self.assertEqual(result, params)

    def test_success__if_paramaters_is_not_matched(self):
        params = {}
        target = self._makeOne()
        result = target(params)
        self.assertEqual(result, params)

    def test_failure(self):
        from gardrail import Failure
        params = {"left": {"x": 10, "y": 10},
                  "right": {"x": -10, "y": 10}}
        target = self._makeOne()
        with self.assertRaises(Failure) as e:
            target(params)
        self.assertEqual(e.exception.errors, {"right": {"x": ["oops"]}})


@test_target("gardrail:container")
class ContainerTests(unittest.TestCase):
    def _makeOne(self):
        from gardrail import multi, NG

        class G(Gardrail):
            deco = self._getTarget()

            @deco
            class left:
                @multi(["x", "y"])
                def positive(self, x, y):
                    if not (x > 0 and y > 0):
                        return NG("oops")

            @deco
            class right:
                @multi(["x", "y"])
                def positive(self, x, y):
                    if not (x > 0 and y > 0):
                        return NG("oops")
        return G()

    def test_success(self):
        params = {"left": {"x": 10, "y": 10},
                  "right": {"x": 10, "y": 10}}
        target = self._makeOne()
        result = target(params)
        self.assertEqual(result, params)

    def test_success__if_paramaters_is_not_matched(self):
        params = {}
        target = self._makeOne()
        result = target(params)
        self.assertEqual(result, params)

    def test_failure(self):
        from gardrail import Failure
        params = {"left": {"x": 10, "y": 10},
                  "right": {"x": -10, "y": 10}}
        target = self._makeOne()
        with self.assertRaises(Failure) as e:
            target(params)
        self.assertEqual(e.exception.errors, {"right": {"x": ["oops"]}})


@test_target("gardrail:collection")
class CollectionTests(unittest.TestCase):
    def _makeOne(self):
        from gardrail import multi, NG

        class G(Gardrail):
            deco = self._getTarget()

            @deco
            class points:
                @multi(["x", "y"])
                def positive(self, x, y):
                    if not (x > 0 and y > 0):
                        return NG("oops")
        return G()

    def test_success(self):
        params = {"points": [{"x": 10, "y": 10}, {"x": 10, "y": 10}]}
        target = self._makeOne()
        result = target(params)
        self.assertEqual(result, params)

    def test_success__if_paramaters_is_not_matched(self):
        params = {}
        target = self._makeOne()
        result = target(params)
        self.assertEqual(result, params)

    def test_failure(self):
        from gardrail import Failure
        params = {"points": [{"x": 10, "y": 10}, {"x": 10, "y": -10}]}
        target = self._makeOne()
        with self.assertRaises(Failure) as e:
            target(params)
        self.assertEqual(e.exception.errors, {'points': {1: {'x': ['oops']}}})


@test_target("gardrail:convert")
class ConvertTests(unittest.TestCase):
    def _makeOne(self):
        class G(Gardrail):
            deco = self._getTarget()

            @deco(["x", "y"])
            def total(self, params):
                params["total"] = params["x"] + params["y"]
        return G()

    def test_success(self):
        params = {"x": 10, "y": 200}
        target = self._makeOne()
        result = target(params)
        self.assertEqual(result, {"x": 10, "y": 200, "total": 210})
