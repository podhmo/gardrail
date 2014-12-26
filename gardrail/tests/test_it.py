# -*- coding:utf-8 -*-
import unittest
from evilunit import test_target
from gardrail import Gardrail
from gardrail.compat import assert_regex

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

    def test_success__if_paramaters_are_missing(self):
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

    def test_failure__if_strict_True__missing(self):
        from gardrail import Failure
        params = {}
        target = self._makeOne()
        target.difference_is_small.strict = True
        with self.assertRaises(Failure) as e:
            target(params)
        assert_regex(self, e.exception.errors["x"][0], "fields:\['x', 'y'\] not found")


@test_target("gardrail:matched")
class MatchedTests(unittest.TestCase):
    def _makeOne(self):
        from gardrail import NG

        class G(Gardrail):
            deco = self._getTarget()

            @deco(["x", "y"], path="__all__")
            def is_positive(self, values):
                if not all(e > 0 for e in values):
                    return NG("oops")
        return G()

    def test_success(self):
        params = {"x": 10, "y": 10}
        target = self._makeOne()
        result = target(params)
        self.assertEqual(result, params)

    def test_success__if_paramaters_are_missing(self):
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

    def test_failure__if_strict_True__missing(self):
        from gardrail import Failure
        params = {}
        target = self._makeOne()
        target.is_positive.strict = True
        with self.assertRaises(Failure) as e:
            target(params)
        assert_regex(self, e.exception.errors["__all__"][0], "fields:\['x', 'y'\] not found")


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

    def test_success__if_paramaters_are_missing(self):
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

    def test_failure__if_strict_True__missing(self):
        from gardrail import Failure
        params = {}
        target = self._makeOne()
        target.left.strict = True
        with self.assertRaises(Failure) as e:
            target(params)
        assert_regex(self, e.exception.errors["left"][0], "fields:\['left'\] not found")


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

    def test_success__if_paramaters_are_missing(self):
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

    def test_failure__if_strict_True__missing(self):
        from gardrail import Failure
        params = {}
        target = self._makeOne()
        target.left.cls.strict = True
        with self.assertRaises(Failure) as e:
            target(params)
        assert_regex(self, e.exception.errors["left"][0], "fields:\['left'\] not found")


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

    def test_success__if_paramaters_are_missing(self):
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

    def test_failure__if_strict_True__missing(self):
        from gardrail import Failure
        params = {}
        target = self._makeOne()
        target.points.cls.strict = True
        with self.assertRaises(Failure) as e:
            target(params)
        assert_regex(self, e.exception.errors["points"][0], "fields:\['points'\] not found")


@test_target("gardrail:convert")
class ConvertTests(unittest.TestCase):
    def _makeOne(self):
        class G(Gardrail):
            deco = self._getTarget()

            @deco(["x", "y"], path="total")
            def total(self, params):
                params["total"] = params["x"] + params["y"]
        return G()

    def test_success(self):
        params = {"x": 10, "y": 200}
        target = self._makeOne()
        result = target(params)
        self.assertEqual(result, {"x": 10, "y": 200, "total": 210})

    def test_failure__if_strict_True__missing(self):
        from gardrail import Failure
        params = {}
        target = self._makeOne()
        target.total.strict = True
        with self.assertRaises(Failure) as e:
            target(params)
        assert_regex(self, e.exception.errors["total"][0], "fields:\['x', 'y'\] not found")
