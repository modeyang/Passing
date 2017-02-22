# !/usr/bin/env python
# coding=utf-8

from kafka import KafkaConsumer, KafkaProducer
from kafka import KafkaClient, SimpleProducer
import time


class KafkaSender(object):

    def __init__(self, servers, **kwargs):
        self.sender = KafkaProducer(bootstrap_servers=servers, **kwargs)

    def send_msg(self, topic, buf):
        return self.sender.send(topic, buf)


class PKafkaSender(object):

    def __init__(self, servers, **kwargs):
        client = KafkaClient(servers)
        self.sender = SimpleProducer(client)

    def send_msg(self, topic, buf):
        return self.sender.send_messages(topic, buf)


class KafkaSender_v2(object):

    def __init__(self, servers, topic, **kwargs):
        self.sender = KafkaProducer(bootstrap_servers=servers, **kwargs)
        self.topic = topic

    def send_metrics(self, metric):
        return self.sender.send(self.topic, metric)


class KafkaReader(object):
    
    def __init__(self, servers, group_id, topic, **kwargs):
        shoud_connect = kwargs.pop("shoud_connect", True)
        kwargs.update({"bootstrap_servers": servers, "group_id": group_id})
        self.kwargs = kwargs
        self.topic = topic
        self._is_connected = False
        if shoud_connect : self.connect()

    def connect(self):
        self.consumer = KafkaConsumer(**self.kwargs)
        self.consumer.subscribe([self.topic])
        self._is_connected = True

    @property
    def is_connected(self):
        return self._is_connected

    def metrics(self, raw=False):
        return self.consumer.metrics(raw)

    def yield_msg(self):
        for msg in self.consumer:
            yield msg.value

    def __iter__(self):
        return self

    def next(self):
        return self.consumer.next()

    def close(self):
        if self._is_connected:
            self.consumer.close()

