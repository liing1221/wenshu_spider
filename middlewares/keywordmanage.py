# -*- coding: utf-8 -*-
"""
    @Project     : wenshu_spider
    @File        : keywordmanage.py
    @Create_Date : 2019-05-14 12:01
    @Update_Date : 2019-05-14 12:01
    @Author      : liing
    @Email       : liing1221@163.com
    @Software    : PyCharm
"""
from __future__ import print_function
from middlewares.settings import KEYWORD_FILE, CONTRAST_TABLE




def get_keyword():
    """
    从检索关键字记录文件：query_keyword.txt读取并返回检索关键字的字典
    :return:
    """
    with open(KEYWORD_FILE, 'r', encoding='utf-8') as f:
        while True:
            line = f.readline()
            if not line:
                break
            elif line[:2] == '##':
                continue
            else:
                row = {}
                keywords = line.split('、')[1].split(',')
                for keyword in keywords:
                    keyword = keyword.split(':')
                    # key = CONTRAST_TABLE[keyword[0]]
                    key = keyword[0]
                    value = keyword[1].strip()
                    row.setdefault(key, value)
                yield row



if __name__ == "__main__":
    for row in get_keyword():
        print(row, flush=True)
