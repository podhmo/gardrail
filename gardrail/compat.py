# -*- coding:utf-8 -*-
import sys

PY3 = sys.version_info[0] == 3


def assert_regex(unittest_self, *args, **kwargs):
    if PY3:
        return unittest_self.assertRegex(*args, **kwargs)
    else:
        return unittest_self.assertRegexpMatches(*args, **kwargs)
