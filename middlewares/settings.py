# -*- coding: utf-8 -*-
"""
    @Project     : baiji_specification_spider
    @File        : settings.py
    @Create_Date : 2019-03-06 11:18
    @Update_Date : 2019-03-06 11:18
    @Author      : liing
    @Email       : liing1221@163.com
    @Software    : PyCharm
"""

# 项目基本信息配置
PROJECT = 'wenshu'
RETRY = 5
TIMEOUT = 30
PROCESSES = 10
LEN_SQR = 90     # 申请人判断：解析时80以内判断是案件人信息，以上为文字描述
KEYWORD_FILE = 'D:/liing_code/spider_projects/wenshu_spider/middlewares/query_keyword.txt'
DATA_FILE = 'D:\\liing_code\\spider_projects\\wenshu_spider\\spider_datas/'

# Mysql数据库配置
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PWD = '123456'
MYSQL_DB = 'test'

# Redis配置
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
KEY_ = ''


# MongoDB数据库配置
MONGO_HOST = 'localhost'
MONGO_PORT = '27017'
MONGO_DB = 'gov_patent'


MONTH_TABLE = {
    '1':31,
    '2':28,
    '3':31,
    '4':30,
    '5':31,
    '6':30,
    '7':31,
    '8':31,
    '9':30,
    '10':31,
    '11':30,
    '12':31,
}
CONTRAST_TABLE = {

    # 数据库部分
    '检索条件': 'JSTJ',
    '检索结果数量': 'JSJGSL',
    '案件名称': 'AJMC',
    '案件类型': 'AJLX',
    '案号': 'AH',
    '审判程序': 'SPCX',
    '法院名称': 'FYMC',  # 'FYMC'
    '裁判日期': 'CPRQ',
    '裁判要旨段原文': 'CPYZDYW',
    '不公开理由': 'BGKLY',
    '文书类型': 'WSLX',
    '文书ID': 'docid',

    "申请再审人（一审被告、二审上诉人、原申请再审人）": "TCSQR",  # "retrial_Applicant",
    "再审申请人": "TCSQR",
    '申请再审人': "TCSQR",
    "申请人": 'TCSQR',
    "上诉人": "TCSQR",
    "原告": "TCSQR",                                    # "retrial_Applicant",
    "被申请人（一审原告、二审被上诉人、原被申请人)": "BSQR",  # "respondent",
    "被申请人": "BSQR",
    "被上诉人": "BSQR",
    "被告": "BSQR",
    "原审被告": "YSBG",     # "original_defendant",
    "原审第三人": "YSDSR",  # ""Third_party",
    "审判长": "SPZ",
    "代理审判员": "DLSPY",
    "审判员": "SPY",
    "人民陪审员": "PSY",
    "陪审员": "PSY",
    "书记员": "SJY",
    "代书记员":'SJY',
    "首部": "WBSB",
    "DSRXX": "DSRXX",
    "事实": "SSJL",
    "理由": "CPYZ",
    "判决结果": "PJJG",
    "尾部": "WBWB",

    '法院ID': 'FYID',
    '法院地市': 'FYDS',
    '法院省份': 'FYSF',
    "法院区域": "FYQY",
    "法院区县": "FYQX",
    "案件基本情况段原文": "AJJBQKYW",
    "文本首部段落原文": "WBSBDLYW",
    "DocContent": "DocContent",
    "补正文书": "BZWS",
    "诉讼记录段原文": "SSJLDYW",
    "判决结果段原文": "PJJGDYW",
    "文本尾部原文": "WSWBYW",
    "诉讼参与人信息部分原文": "SSCYRXXBFYW",
    "文书全文类型": 'WSQWLX',
    "结案方式": 'JAFS',
    "效力层级": 'XLCJ',
    "附加原文": "FJYW",

    '专利号': 'PN',
    '文书文档路径': 'DOC',
    '处理状态': 'status',  # '0未处理，1已处理'
    '文书发布日期': 'WSFBRQ',
    '更新时间': 'create_at',

    # 检索相关
    '全文检索': 'QWJS',
    '案由': 'AY',

    '法院层级': 'FYCJ',
    '审判人员': 'SPRY',
    '当事人': 'DSR',
    '律所': 'LS',
    '律师': 'LAWYER',
    '法律依据': 'FLYJ',
    "法定代表人": "FDDBR",  # "Legal_representative",
    "委托代理人": "WTDLR",  # "authorized_agent",

}