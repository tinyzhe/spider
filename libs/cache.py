# coding=utf-8
__author__ = "xiangzhe"

import redis
from conf import config

class Cache:

    handle = None

    def __init__(cls):
        if cls.handle == None:
            cls.handle = redis.Redis(config.CACHES['host'], port=config.CACHES['port'], db=config.CACHES['dbname'], password=config.CACHES['auth'], socket_timeout=3)

    def get(cls, key):
        return cls.handle.get(key)

    def set(cls, key, vlaue, extime = 0):
        cls.handle.set(key, vlaue, extime)

    def hgetall(cls, key):
        return cls.handle.hgetall(key)