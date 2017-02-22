#!/usr/bin/python
# -*- coding:utf-8 -*-
# vim: set number tw=0 shiftwidth=4 tabstop=4 expandtab:
import logging
import time
import datetime
import arrow
from libs.dateutil import parser


class TimeConvertor(object):
    
    @staticmethod 
    def convert2datetime(time_str, format=None, fuzzy=True):
        """
        convert time string to datetime, if format sure, use strptime, 
        otherwise parse time string fuzzily. 
        params:
            time_str  log time string
            formats   list of time formats, such as UNIX, ISO8601 or %Y-%m-%d %H:%M:%S  
            fuzzy     fuzzy search, default True    
        """
        try:
            if format:
                if format.lower() == "iso8601":
                    return arrow.get(time_str)
                return datetime.datetime.strptime(time_str, format)
            return parser.parse(time_str, fuzzy=fuzzy)
        except Exception, e:
            logging.error(time_str)
            logging.exception(e)
        return datetime.datetime.now()

    @staticmethod
    def convert2timestamp(time_str, format=None):
        dt = TimeConvertor.convert2datetime(time_str, format)
        return int(time.mktime(dt.timetuple()))

    @staticmethod
    def format_timestamp(timestamp):
        return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
