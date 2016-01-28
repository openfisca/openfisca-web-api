# -*- coding: utf-8 -*-


import collections


def sodict(**kwargs):
    """Create a sorted OrderedDict."""
    return collections.OrderedDict(sorted(kwargs.iteritems()))
