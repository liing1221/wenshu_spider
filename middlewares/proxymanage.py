# -*- coding: utf-8 -*-
# @Time    : 2018/5/16 PM5:36
# @Author  : undefined
# @FileName: test.py
# @Software: PyCharm
import sys, time, random
import requests
import threading
from requests.models import Response
from middlewares.logmanage import LogManager


logger = LogManager(level=30)

class ProxyManager:
    # URL = "http://api.ip.data5u.com/dynamic/get.html?order=2ddcac4f4b8a630bd2b0c051cf236500&sep=3"
    URL = "http://api.ip.data5u.com/dynamic/get.html?order=2ddcac4f4b8a630bd2b0c051cf236500&random=true&sep=3"
    INTERVAL = 55     #10分钟
    EXPIRES_TIME = 0
    PROXY_IP = ''
    PROXY_PORT = ''
    POOL = []         # 代理池
    _instance_lock = threading.Lock()     # 使单列模式支持多线程

    def __new__(cls, *args, **kwargs):
        """
        构造proxyManager的单列模式，并支持多线程调用
        :param args:
        :param kwargs:
        :return:
        """
        if not hasattr(ProxyManager, '_instance'):
            with ProxyManager._instance_lock:
                if not hasattr(ProxyManager, '_instance'):
                    ProxyManager._instance = object.__new__(cls)
                    ProxyManager.INIT = True
        return ProxyManager._instance

    def __init__(self, pool = True):
        """
        初始化过期时间
        :param pool:
        """
        if self.INIT:                     # 单列模式，初始化一次
            self.INIT = False
            self.pool = pool
            if self.pool:
                self.get_pool()
            else:
                self.set_proxy()

    @logger.log_decoratore
    def set_proxy(self):
        """
        proxy获取，记录proxy以及获取时间
        :return:
        """
        retry_time = 5 #重复请求次数
        while True:
            try:
                contents = requests.get(self.URL)
                if contents.status_code == 200:
                    self.PROXY_IP, self.PROXY_PORT = contents.text.strip().split(":")
                    # print(self.PROXY_IP, self.PROXY_PORT)
                    self.EXPIRES_TIME = int(time.time())    # 过期时间
                return
            except Exception as e:
                print(e)
                retry_time -= 1
                if retry_time <= 0:
                    resp = Response()
                    resp.status_code = 200
                    self.EXPIRES_TIME = 0
                    return resp
                time.sleep(0.1)

    @logger.log_decoratore
    def get_proxy(self):
        """
        若__init__的pool参数为True，则从POOL随机获取一个代理；否则自动或区域个代理；
        并都对proxy进行了过期维护
        :return: 返回获取proxy
        """
        # print("Run get_proxy...")
        now_time = int(time.time())
        if not self.pool:   # 没用使用代理池时
            time.sleep(1)
            proxy_expires = self.EXPIRES_TIME     # 过期时间
            if proxy_expires + self.INTERVAL < now_time:   # 过期从新获取
                self.set_proxy()
            return (self.PROXY_IP,self.PROXY_PORT)
        else:  # 使用代理池时
            while True:
                try:
                    proxy = random.choice(self.POOL)   # 过期维护
                    proxy_expires = proxy[2]        # 过期时间
                    if proxy_expires + self.INTERVAL < now_time:  # 移除过期代理
                        self.proxy_remove(proxy)
                    else:
                        return (proxy[0], proxy[1])
                except IndexError as e:
                    self.get_pool()

    def get_pool(self):
        """
        获取一个数量为100的代理池POOL
        :return:
        """
        # print("Run get_pool...")
        while True:
            if len(self.POOL) < 100:
                self.set_proxy()
                proxy = (self.PROXY_IP, self.PROXY_PORT, self.EXPIRES_TIME)
                self.POOL.append(proxy)
                time.sleep(0.1)
            else:
                break

    def proxy_remove(self, proxy):
        """
        从POOL中移除一个代理，并再添加一个
        :param proxy: (ip, port，EXPIRES_TIME)
        :return:
        """
        # print("Run proxy_remove...")
        self.POOL.remove(proxy)
        self.set_proxy()
        proxy = (self.PROXY_IP, self.PROXY_PORT, self.EXPIRES_TIME)
        self.POOL.append(proxy)


if __name__ == "__main__":
    # proxy1 = ProxyManager(pool=True)
    proxy2 = ProxyManager(pool=False)
    # print(id(proxy1), id(proxy2))
    print(proxy2.POOL)
    for i in range(20):
        try:
            ip, prot = proxy2.get_proxy()
            print('IP: {}\nPort: {}\nPROXYPOOL: {}' .format(ip, prot, len(proxy2.POOL)))
        except KeyboardInterrupt:
            sys.exit(0)
