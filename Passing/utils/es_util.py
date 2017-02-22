# !/usr/bin/env python
# coding=utf-8

# stdlib
import time
import json
import jinja2
import logging
import requests
import datetime
import logging
import bin.config
from elasticsearch import Elasticsearch


class ESHelper(object):
    '''
    es for every single metrics when monitor
    '''
    def __init__(self, es_url, step=60, span=bin.config.QUERY_SPAN):
        self.es_url = es_url
        self.step = step
        self.es_client = Elasticsearch(es_url)
        self.query_span = span

    def _get_es_data(self, url, action="POST", body=None):
        try:
            if action.upper() == "POST":
                resp = requests.post(url, data=json.dumps(body))
            else:
                resp = requests.get(url)

            logging.debug(resp.text)
            resp_json = resp.json()
            if resp_json.get("error", None):
                raise Exception(str(resp_json['error']['root_cause']))
            return resp_json
        except Exception, e:
            logging.exception(e)
        return None

    def _get_es_data_by_sdk(self, indice, body):
        try:
            resp_json = self.es_client.search(index=indice, body=body, pretty=True)
            logging.debug(json.dumps(resp_json))
            return resp_json
        except Exception, e:
            logging.error(indice)
            logging.exception(e)
        return None

    def _load_query_json(self, query_file, **kwargs):
        kend_time = kwargs.get("end_time", None)
        kstart_time = kwargs.get("start_time", None)
        step_counts = kwargs.get("step_counts", 1)
        template = jinja2.Template(open(query_file, 'rb').read())
        if kend_time and kstart_time:
            end_time, start_time = kend_time, kstart_time
        elif kend_time:
            end_time, start_time = kend_time, kend_time - step_counts * self.step
        else:
            end_time = int(time.time()) - self.query_span
            start_time = end_time - self.step * step_counts

        query_kwargs = {}
        if kwargs: query_kwargs.update(kwargs)
        query_kwargs.update({'start_time': start_time * 1000, 'end_time': end_time * 1000})
        query_json = json.loads(template.render(**query_kwargs))
        logging.debug(json.dumps(query_json))
        return query_json, end_time

    def _get_index_name(self, indice, timestamp):
        es_timestamp = timestamp - 8 * 3600
        es_index_date = datetime.date.fromtimestamp(es_timestamp)
        return indice.replace("*", es_index_date.strftime("%Y.%m.%d"))

    def check_metrics(self, indice, query_file, **kwargs):
        self.indice, self.query_file, self.kwargs = indice, query_file, kwargs

    @classmethod
    def get_es_data(cls, es_url, indice, query_json, logger):
        es_client = Elasticsearch(es_url, timeout=bin.config.ES_TIMEOUT)
        try:
            resp_json = es_client.search(index=indice, body=query_json, pretty=True)
            logger.debug(resp_json)
            return resp_json
        except Exception, e:
            logging.exception(e)
        return None

    def check(self):
        query_json, timestamp = self._load_query_json(self.query_file, **self.kwargs)
        logging.debug(json.dumps(query_json))
        index_name = self._get_index_name(self.indice, timestamp)
        resp_client_json = self._get_es_data_by_sdk(index_name, query_json)
        return resp_client_json


