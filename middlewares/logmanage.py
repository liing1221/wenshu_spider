# -*- coding: utf-8 -*-
"""
    @Project     : demo
    @File        : logmanager.py
    @Create_Date : 2019-01-09 13:57
    @Update_Date : 2019-01-09 13:57
    @Author      : liing
    @Email       : liing1221@163.com
    @Software    : PyCharm
"""
import os
import logging
import threading
import traceback
from functools import wraps
from middlewares.settings import PROJECT


class LogManager:
    """
    自定义日志记录模块：实现日志的当前logs文件夹下的存储以及格式化保存，以及文件与screen输出的控制
    """
    DATEFMT = "[%Y-%m-%d %H:%M:%S]"
    FORMAT = "%(asctime)s %(thread)d %(message)s"
    LEVEL = logging.DEBUG
    FILENAME = ''
    PROJECT = PROJECT
    _instance_lock = threading.Lock()     # 使单列模式支持多线程

    def __new__(cls, *args, **kwargs):
        """
        构造CookieManager的单列模式，并支持多线程调用
        :param args:
        :param kwargs:
        :return:
        """
        if not hasattr(cls, '_instance'):
            with cls._instance_lock:
                if not hasattr(cls, '_instance'):
                    cls._instance = object.__new__(cls)
                    cls._INIT = True
        return cls._instance

    def __init__(self, level=None, datefmt=None, format=None):
        """
        初始化日志格式与存储路径
        """
        if self._INIT:
            self._INIT = False
            self.log_dirs = os.path.join(os.path.dirname(__file__), 'logs')
            if not os.path.exists(self.log_dirs):
                os.makedirs(self.log_dirs)
            self.FILENAME = '{}.log'.format(self.PROJECT)   # 初始化日志文件名称
            if datefmt:
                self.DATEFMT = datefmt                      # 初始化时间格式
            if format:
                self.FORMAT = format                        # 初始化日志格式
            if level:
                self.LEVEL= level                           # 初始化日志级别
            self.logger = self.create_logger()              # 创建定制化的logger对象

    def create_logger(self):
        """
        根据初始化信息创建logger对象
        :return: logger对象

        """
        # logging.basicConfig(level=self.LEVEL,format=self.FORMAT,datefmt=self.DATEFMT)
        logger = logging.getLogger(__name__)  # 初始化记录器
        logger.setLevel(self.LEVEL)

        logformater = logging.Formatter(self.FORMAT)

        if self.FILENAME:
            loghandler = logging.FileHandler(os.path.join(self.log_dirs, self.FILENAME))
            loghandler.setFormatter(logformater)
            logger.addHandler(loghandler)
            # loghandler.close()
            # print(dir(loghandler))
        else:
            loghandler = logging.Handler()
            loghandler.setFormatter(logformater)
            logger.addHandler(loghandler)

        filter = logging.Filter(__name__)
        logger.addFilter(filter)

        return logger

    def log_decoratore(self, func):
        """
        定义一个装饰器，记录日志
        :param func:
        :return:
        """
        @wraps(func)
        def log(*args, **kwargs):
            try:
                # print('当前执行的函数是： ', func.__name__)
                func_name = func.__name__

                return func(*args, **kwargs)
            except Exception as e:
                # traceback.print_exc()
                # trace = traceback.format_exc()
                self.logger.exception(e)
                # logger.log(level=self.LEVEL, msg='Error func params : {}, {}'.format(args, kwargs), extra=locals())
        return log







