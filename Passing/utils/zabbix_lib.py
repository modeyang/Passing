#!/usr/bin/python
# -*- coding:utf-8 -*-
# vim: set number tw=0 shiftwidth=4 tabstop=4 expandtab:
import os
import logging
import time
import collections
from libs.pyzabbix import ZabbixMetric, ZabbixSender, ZabbixAPI
# from pyzabbix import ZabbixMetric, ZabbixSender, ZabbixAPI


Item = collections.namedtuple("Item",
        ["hostid", "itemid", "name", "key", "lastvalue", "lastclock"]
)


class ZabbixHelper(object):
    
    def __init__(self, zabbix_url, user, passwd, sender):
        self.zapi = self.login(zabbix_url, user, passwd)
        self.zabbix_sender = ZabbixSender(sender)

    def login(self, zabbix_url, user, passwd):
        return ZabbixAPI(zabbix_url, user=user, password=passwd)

    def get_host_ids(self, host):
        hosts = self.get_filter_host(host)
        if len(hosts) == 0:
            return None
        return [h['hostid'] for h in hosts]

    def get_hosts(self):
        return self.zapi.host.get(output=['host'])

    def get_host_items(self, host_or_template, fields=["name"]):
        host_ids = self.get_host_ids(host_or_template)
        results = self.zapi.host.get(output=["hostid"], selectItems=fields, hostids=host_ids)
        items = []
        for result in results:
           for r in result["items"]:
                q_item = dict([(key, r[key]) for key in fields ])
                items.append(q_item)
        return items
    
    def get_items_by_host(self, hosts, filters=None):
        hostids = self.get_host_ids(hosts)
        kwargs = {}
        if filters and isinstance(filters, dict):
            kwargs['search'] = filters
        results = self.zapi.item.get(output="extend", hostids=hostids, **kwargs)
        return [Item(ret["hostid"], ret["itemid"], ret["name"], ret["key_"], ret["lastvalue"], ret["lastclock"]) for ret in results]

    def get_filter_host(self, hosts):
        return self.zapi.host.get(output=['host'], filter={'host': hosts})

    def get_host_by_id(self, hostids):
        results = self.zapi.host.get(output="extend", hostids=hostids)
        return dict([(x["hostid"], x["host"]) for x in results])

    def exist_item(self, hostid, key):
        results = self.zapi.item.get(output="extend", hostids=hostid, search={"key_": key})
        return len(results) > 0

    def create_item(self, host, name, key, **kwargs):
        """
        value_type: Possible values: 
            0 - numeric float; 
            1 - character; 
            2 - log; 
            3 - numeric unsigned; 
            4 - text.
        type: Possible values: 
            0 - Zabbix agent; 
            1 - SNMPv1 agent; 
            2 - Zabbix trapper; 
            3 - simple check; 
            4 - SNMPv2 agent; 
            5 - Zabbix internal; 
            6 - SNMPv3 agent; 
            7 - Zabbix agent (active); 
            8 - Zabbix aggregate; 
            9 - web item; 
            10 - external check; 
            11 - database monitor; 
            12 - IPMI agent; 
            13 - SSH agent; 
            14 - TELNET agent; 
            15 - calculated; 
            16 - JMX agent; 
            17 - SNMP trap.
        """
        hostid = self.get_host_ids(host)
        if hostid is None:
            raise Exception("can not found host %s" % host)
        hostid = hostid[0]
        params = {"name": name, "key_": key, "hostid": str(hostid)}
        params['type'] = kwargs.pop('type', 2)
        params['value_type'] = kwargs.pop("value_type", 0)
        params['interfaceid'] = kwargs.pop('interfaceid', "1")
        params['delay'] = kwargs.pop('delay', 30)
        tpl_name = kwargs.pop("template", None)
        if tpl_name is not None:
            tpl_id = self.get_template_id(tpl_name)
            if tpl_id is not None: params["hostid"] = str(tpl_id)
        if self.exist_item(params['hostid'], key):
            return True
        return self.zapi.item.create(**params)

    @classmethod
    def metric(cls, host, metric, value, timestamp=time.time()):
        return ZabbixMetric(host, metric, value, timestamp)

    def send_metrics(self, metrics):
        return self.zabbix_sender.send(metrics)

    def get_template_id(self, tpl_name):
        result = self.zapi.template.get(output="extend", filter={"name": tpl_name})
        if len(result) > 0:
            return result[0]['templateid']
        return None

    def get_template_host_ids(self, tpl_name):
        result = self.zapi.host.get(output="extend", filter={'template': tpl_name})
        if len(result) > 0:
            return [ret['hostid'] for ret in result]
        return []

    def create_discovery_rule(self, host, name, key, **kwargs):
        params = {}
        params["key_"] = key
        params["host"] = host
        if self.zapi.discoveryrule.exists(**params):
            logging.info("host: %s discoveryrule:%s has been created" % (host, key))
            results = self.zapi.discoveryrule.get(filter=params)
            return results[0]["itemid"]
        params.pop("host")
        params["name"] = name
        params["type"] = kwargs.pop("type", 2)
        params["lifetime"] = kwargs.pop("lifetime", 1)
        params['interfaceid'] = kwargs.pop('interfaceid', "1")
        params['delay'] = kwargs.pop('delay', 0)
        hostids = self.get_host_ids(host)
        if hostids is None:
            raise Exception("can not found host %s" % host)
        params["hostid"] = hostids[0]
        results = self.zapi.discoveryrule.create(**params)
        return results["itemids"][0]

    def create_item_prototype(self, ruleid, host, name, key, **kwargs):
        params = {}
        params["key_"] = key
        params["host"] = host
        if self.zapi.itemprototype.exists(**params):
            logging.info("host: %s item:%s has been created" % (host, key))
            return True
        params.pop("host")
        hostids = self.get_host_ids(host)
        if hostids is None:
            raise Exception("can not found host %s" % host)
        if kwargs.get("applications", None):
            params["applications"] = kwargs["applications"]
        params["hostid"] = hostids[0]
        params["ruleid"] = ruleid
        params["value_type"] = kwargs.pop("value_type", 0)
        params["type"] = kwargs.pop("type", 2)
        params['delay'] = kwargs.pop('delay', 0)
        params["name"] = name
        return self.zapi.itemprototype.create(**params)


if __name__ == "__main__":
    import sys
    import time
    import json
    sys.path.append("..")

    helper = ZabbixHelper("http://192.168.1.193/zabbix", "test", "test", "192.168.1.193")
    # print helper.get_hosts()
    # print helper.get_filter_host("ip-10-1-172-57")
    # print helper.create_item("ip-10-1-172-57", "test_api_4", "test_api_4", **{"delay": 60, "template": "test"})

    # print helper.get_template_host_ids("test")
    # print helper.get_template_id("test")
    # print len(helper.get_host_items(zhost_config.values()))
    # print len(helper.get_host_items(zhost_config.values()))
    # print helper.get_host_items(["SAAS-Odin-UPSTREAM_TIME"], ["itemid", "key_"])
    # print helper.get_host_by_id([10122, 10131])
    # items = [item.key for item in results]
    # print items
    # ruleid = helper.create_discovery_rule("odin-bytes_sent", "odin_discovery_typeName_idc", "odin_discovery_typeName_idc")

    # print ruleid
    # print helper.create_item_prototype(ruleid, "odin-bytes_sent", u"odin-带宽-接口类型-{#TYPENAME}-机房-{#IDC}", "odin_bytes[{#TYPENAME}, {#IDC}]")
    # metrics = []
    now = int(time.time())
    d_data = {
        "data": [{
            "{#ONE}": "1"
        }]
    }
    print json.dumps(d_data)
    print helper.send_metrics([helper.metric("TEST_D", "test_key", json.dumps(d_data, ensure_ascii=False, indent=2), now)])
    d_data = {
        "data": [{
            "{#ONE}": 1,
            "{#TWO}": 2
        }]
    }
    print json.dumps(d_data)
    print helper.send_metrics([helper.metric("TEST_D", "test_key", json.dumps(d_data, ensure_ascii=False, indent=2), now)])

    # metrics.append(helper.metric("SAAS-Odin-QOS", "odin_error_rate[mob.bz.mgtv.com]", 11, now))
    # metrics.append(helper.metric("SAAS-Odin-QOS", "odin_error_rate[mob.bz.mgtv.com]", 12, now))
    # metrics.append(helper.metric("SAAS-Odin-QOS", "odin_error_rate[mob.bz.mgtv.com]", 13, now))
    # helper.send_metrics(metrics)
    # helper.exist_item(10142, "odin_error_rate[mob.bz.mgtv.com]")
