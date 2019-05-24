# -*- coding: utf-8 -*-

import time
import pymysql
from pymysql import escape_string
from pymysql.err import MySQLError, InternalError, OperationalError
from DBUtils.PooledDB import PooledDB
from middlewares.settings import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PWD, MYSQL_DB


class SqlManager:

    SERVER_IP = MYSQL_HOST
    PORT = MYSQL_PORT
    USER = MYSQL_USER
    PASSWORD = MYSQL_PWD
    DB_NAME = MYSQL_DB

    def __init__(self, max_num_thread):
        """
        初始化一个数据库连接池：默认有2个空闲连接
        :param max_num_thread: 数据库连接池的最大连接数量
        """
        try:
            self.connection_pool = PooledDB(
                creator=pymysql,                # 使用链接数据库的模块
                maxconnections=max_num_thread,  # 连接池允许的最大连接数，0和None表示不限制连接数
                mincached=2,                    # 初始化时，链接池中至少创建的空闲的链接，0表示不创建
                host=self.SERVER_IP,
                port=self.PORT,
                user=self.USER,
                password=self.PASSWORD,
                database=self.DB_NAME,
                charset='utf8'
            )
        except OperationalError as e:
            print("Error occur in connect to mysql. Error message:\n    {}".format(e))
        except InternalError as e:
            print(
                "Error occur in connect to  database {} at {}. Error message:\n    {}".format(
                    self.DB_NAME, self.SERVER_IP, e))

    def inset_wenshu_cases(self, row):
        """插入数据"""
        conn = self.connection_pool.connection()
        cursor = conn.cursor()
        try:
            create_at = time.strftime('%Y-%m-%d %H:%M:%S')
            add_url = ("INSERT INTO wenshu_patent_cases (`JSJGSL`,`CPYZDYW`,`AJLX`,`CPRQ`,`AJMC`,`create_at`, `status`,"
                       "`SPCX`, `AH`, `FYMC`, `BGKLY`, `docid`,`JSTJ`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,"
                       " %s, %s, %s, %s)")
            data_url = (row['JSJGSL'], row['CPYZDYW'], row['AJLX'], row['CPRQ'], row['AJMC'], create_at, '0',
                        row['SPCX'], row['AH'], row['FYMC'], row['BGKLY'], row['docid'], row['JSTJ'])
            cursor.execute(add_url, data_url)
            conn.commit()
            print("插入数据库成功!>>> {}".format(row['AJMC']), flush=True)
        except MySQLError as e:
            print("Error occur in inset_wenshu_cases(). Error message:\n    {}".format(e))

        finally:
            cursor.close()
            conn.close()

    def get_one_cases(self):
        conn = self.connection_pool.connection()
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        try:
            sql = "SELECT id, JSTJ, docid, status FROM wenshu_patent_cases WHERE status=0 ORDER BY `id`;"
            cursor.execute(sql)
            if cursor.rowcount == 0:
                return
            else:
                for i in range(cursor.rowcount):
                    row = cursor.fetchone()
                    yield row
        except MySQLError as e:
            print("Error occur in get_one_cases(). Error message:\n    {}".format(e))

        finally:
            cursor.close()
            conn.close()

    def update_one_cases(self, row, row_id):
        """"""
        conn = self.connection_pool.connection()
        cursor = conn.cursor()
        try:
            parm = ''
            create_at = time.strftime('%Y-%m-%d %H:%M:%S')
            row['status'] = '1'
            row['create_at'] = create_at
            keys = ['FYID', 'AJJBQKYW', 'FYDS', 'FYSF', 'WBSBDLYW', 'FYQY', 'CPYZDYW', 'FYQX', 'DocContent', 'BZWS',
                    'SSJLDYW', 'PJJGDYW', 'WSWBYW', 'SSCYRXXBFYW', 'WSLX', 'WSQWLX', 'JAFS', 'XLCJ', 'FJYW',
                    'WSFBRQ', 'WBSB', 'DSRXX',  'CPYZ', 'PJJG', 'WBWB', 'TCSQR', 'BSQR', 'YSBG', 'YSDSR',
                    'SPZ', 'SPY', 'DLSPY', 'PSY', 'SJY', 'DOC', 'status', 'create_at'] # 'SSJL',
            for item in row.items():
                if item[0] in keys:
                    if item[1]:
                        value = escape_string(item[1])
                        parm += '{}="{}",'.format(item[0], value)
                    else:
                        parm += "{}='{}',".format(item[0], item[1])
            parm = parm.strip(',')

            update_sql = "UPDATE wenshu_patent_cases SET {} where id = '{}';".format(parm, row_id)
            print(update_sql)
            cursor.execute(update_sql)
            conn.commit()
            print("更新数据库成功!>>> {}".format(row_id), flush=True)
        except MySQLError as e:
            print("Error occur in update_one_cases(). Error message:\n    {}".format(e))
        finally:
            cursor.close()
            conn.close()



if __name__ == "__main__":
    dbmanager = SqlManager(2)
    for row in dbmanager.get_one_cases():
        print(row)