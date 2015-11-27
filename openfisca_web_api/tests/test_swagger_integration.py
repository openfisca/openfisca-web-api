# -*- coding: utf-8 -*-


from nose.tools import assert_greater

from ..controllers.swagger import (
    build_paths,
    )
from . import common


def setup_module(module):
    common.get_or_load_app()


def smoke_test_build_paths():
    assert_greater(build_paths(), 100)
