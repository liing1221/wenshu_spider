# -*- coding: utf-8 -*-
"""
    @Project     : malacardspider
    @File        : redismange.py
    @Create_Date : 2019-01-14 16:13
    @Update_Date : 2019-01-14 16:13
    @Author      : liing
    @Email       : liing1221@163.com
    @Software    : PyCharm
    @Description : redis管理类 (redis进行专利去重；以及任务队列)
"""
import os
import json
import redis
from hashlib import md5
from middlewares.settings import REDIS_HOST, REDIS_PORT, PROJECT


class RedisManager:
    """
    创建redis管理对象。存储patentid到redis集合，进行专利过滤；同时存储待处理的专利文件路径到redis队列，等待处理。处理后的路径存入已处理队列
    """
    HOST = REDIS_HOST
    REDIS_PORT = REDIS_PORT
    PROJECT = PROJECT

    def __init__(self):
        """
        初始化redis管理器的数据库链接
        """
        self.timeout = 600
        try:
            self.r = redis.Redis(host=self.HOST, port=self.REDIS_PORT, decode_responses=True)
        except Exception as e:
            print('Redis数据库链接出错:{}'.format(e))

    def make_key(self, key):
        """
        格式化返回redis存储的key
        :param key: 字符串
        :return:
        """
        redis_key = '{}:{}'.format(self.PROJECT, key)
        return redis_key

    @classmethod
    def get_md5(cls, data):
        """
        传入数据，进行MD5摘要算法处理
        :param data: 要进行摘要算法处理的数据
        :return: 数据摘要
        """
        data = data.encode('utf-8')
        m = md5()
        m.update(data)
        md5_digest = m.hexdigest()
        return md5_digest

    def add_filter(self, key, filter_data):
        """
        记录patentid到redis集合中，并进行集合去重
        :return: item
        """
        try:
            filter_key = self.make_key(key=key)
            result = self.r.sadd(filter_key, filter_data)         # redis集合去重
            return result
        except Exception as e:
            print('Redis过滤{}出错!\n{}'.format(filter_data, e))

    def put_queue(self, key, data):
        """
        根据传入的key值，把data入队
        :param key:
        :param data:
        :return:
        """
        if isinstance(data, dict):
            item = json.dumps(data)
        else:
            item = data
        data_key = self.make_key(key)
        self.r.rpush(data_key, item)
        print("数据id:{} 入队！".format(data['id']))

    def get_queue(self, key):
        """
        根据key值，获取队列的数据
        :param key:
        :return:
        """
        data_key = self.make_key(key)
        row = self.r.blpop(data_key, timeout=self.timeout)    # 从对列头部获取页面，队列为空则阻塞,超时10分钟
        if isinstance(row, tuple):
            data = json.loads(row[1])
            return data
        if not row:
            return None


if __name__ == "__main__":
    redismanager = RedisManager()