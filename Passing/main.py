#!/usr/bin/python
# -*- coding:utf-8 -*-
# vim: set number tw=0 shiftwidth=4 tabstop=4 expandtab

import os
import sys
import time
import yaml
import signal
import click
import importlib
 
import config


def handler_close_signal(s, frame):
    print "exit"
    sys.exit(1)


def load_module(module_path, **kwargs):
    package = module_path.split(".", 1)[0]
    module_name = config.module_dict.get(package, None)
    if module_name is None:
        return None

    try:
        m = importlib.import_module(module_path)
        return getattr(m, module_name)(**kwargs)
    except Exception, e:
        print e
    return None


def load_yml_file(file_path):
    with open(file_path) as f:
        return yaml.load(f)


def get_handlers(package, conf):
    conf = conf[package]
    module_path_func = lambda x: "{0}.{1}".format(package, x["name"])
    return filter(lambda x: x is not None, [ load_module(module_path_func(item)) for item in conf ])


@click.command()
@click.option("--worker", "-w", default=1, help="number of filter worker")
@click.argument("yml_file")
def main(worker, yml_file):
    click.echo("filter worker is %s " % worker)
    click.echo(yml_file)
    signal.signal(signal.SIGINT, handler_close_signal)
    signal.signal(signal.SIGTERM, handler_close_signal)
    yaml_config = load_yml_file(yml_file)
    print yaml_config

    input_workers = get_handlers("input", yaml_config)
    if len(input_workers) == 0:
        return

    for m in input_workers:
        for msg in m:
            print msg



if __name__ == "__main__":
    main()
