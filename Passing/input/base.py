#!/usr/bin/python
# -*- coding:utf-8 -*-
# vim: set number tw=0 shiftwidth=4 tabstop=4 expandtab

from collections import Iterator


class Base(Iterator):

    def __init__(self, **kwargs):
        pass

    def metrics(self):
        pass

    def next(self):
        raise NotImplemented("next need implement")

