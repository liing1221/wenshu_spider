# -*- coding: utf-8 -*-
"""
    @Project     : baiji_specification_spider
    @File        : mongomanage.py
    @Create_Date : 2019-03-13 12:35
    @Update_Date : 2019-03-13 12:35
    @Author      : liing
    @Email       : liing1221@163.com
    @Software    : PyCharm
"""
import pymongo
from pymongo.errors import PyMongoError
from middlewares.settings import MONGO_HOST, MONGO_PORT, MONGO_DB


class MongoManager:
    """
    药物说明书数据存储到mongo数据库
    """
    def __init__(self):
        """
        初始化mongo链接
        """
        self.host = MONGO_HOST
        self.port = MONGO_PORT
        self.db = MONGO_DB
        try:
            self.mongoclient = pymongo.MongoClient(
                'mongodb://{}:{}/'.format(self.host, self.port))   # 两种连接方式
            # self.mongoclient = pymongo.MongoClient(host=self.HOST, port=self.PORT)

            self.db = self.mongoclient[self.db]                    # 初始化数据库链接
            collist = self.db.list_collection_names()
            if 'review_patent' in collist:
                print('Mongo数据库 review_patent 集合已存在 ...')
            self.col = self.db['review_patent']                # 连接到集合
            self.col.create_index('id')
            self.col.create_index('决定号')                  # 将'决定号'字段创建索引，1为升序，-1为降序
        except PyMongoError as e:
            print('Mongo数据库链接出错:{}'.format(e))

    def save_patent(self, item):
        """
        存储说复审专利数据到mongo数据库
        :param item:
        :return:
        """
        if isinstance(item, dict):
            try:
                row = self.col.insert_one(item)
                print("Save to mongo OK!")
                return row
            except PyMongoError as e:
                print(
                    'Save patent to mongo Error!\n{}'.format(e))
        else:
            print(item)
            raise TypeError
