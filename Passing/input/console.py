#!/usr/bin/python
# -*- coding:utf-8 -*-
# vim: set number tw=0 shiftwidth=4 tabstop=4 expandtab

from .base import Base


class Console(Base):

    def __init__(self, **kwargs):
        pass

    def next(self):
        msg = raw_input()
        return msg


InStream = Console

