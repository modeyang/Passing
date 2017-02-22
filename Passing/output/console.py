#!/usr/bin/python
# -*- coding:utf-8 -*-
# vim: set number tw=0 shiftwidth=4 tabstop=4 expandtab

from .base import Base


class Console(Base):

    def __init__(self, queue, **kwargs):
        self.queue = queue

    def run(self):
        while True:
            msg = self.queue.get()
            print msg


OutStream = Console

