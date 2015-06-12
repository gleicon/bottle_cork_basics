# coding: utf-8

import ConfigParser
import os
import sys
from collections import defaultdict, namedtuple

def parse_config(config_file):
    conf = defaultdict(lambda x: None)
    config = ConfigParser.RawConfigParser(allow_no_value=True)
    config.read(config_file)

    for s in config.sections():
        for foo in config.items(s):
            item, value = foo
            k = "%s_%s" % (s, item)
            conf[k]=value

    return namedtuple("WebAppConfig", conf)(**conf)

if __name__ =="__main__":
    _cfile = sys.argv[1]
    c = parse_config(_cfile)
    print c
