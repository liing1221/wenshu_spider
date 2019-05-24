# -*- coding: utf-8 -*-
"""
    @Project     : wenshu_spider
    @File        : wenshu_case_list_spider.py
    @Create_Date : 2019-05-14 13:59
    @Update_Date : 2019-05-14 13:59
    @Author      : liing
    @Email       : liing1221@163.com
    @Software    : PyCharm
    @Description : 从2000年按月发起关键字检索请求，并记录状态到page_err.txt,
                   "1、"表示请求失败，"1-、"表示请求解析失败，"1+、"表示解析存储成功
"""
from __future__ import print_function
import re
import sys
import time
import json
import math
import random
import execjs
import requests
from urllib.parse import quote
from fake_useragent import UserAgent
from requests import adapters, Response
from requests.exceptions import ChunkedEncodingError
from requests.exceptions import ReadTimeout, ProxyError, ConnectionError, ContentDecodingError
from middlewares.settings import RETRY, TIMEOUT, CONTRAST_TABLE, MONTH_TABLE
from middlewares.keywordmanage import get_keyword
from middlewares.proxymanage import ProxyManager
from middlewares.mysqlmanage import SqlManager
from middlewares.js import js_wzwschallenge
from middlewares.vl5x import getvjkl5
from middlewares.docid import decode_docid


requests.adapters.DEFAULT_RETRIES = 10


class CaseListSpider:
    """
    根据检索关键字,在文书网发起检索请求，抓取关键字相关的案件列表信息
    """

    def __init__(self):
        """"""
        self.item = {}
        self.retries = RETRY
        self.timeout = TIMEOUT
        self.proxymanager = ProxyManager(pool=False)
        self.sqlmanager = SqlManager(4)
        self.f = open('./middlewares/page_err.txt', 'a+')
        # 保持回话
        self.s = requests.Session()
        pass

    def make_proxies(self):
        """"""
        # 　代理设置
        ip_port = self.proxymanager.get_proxy()
        ip = ip_port[0]
        port = ip_port[1].strip()
        proxies = {
            'http': 'http://{}:{}'.format(ip, port),
            'https': 'http://{}:{}'.format(ip, port)
        }
        return proxies

    @staticmethod
    def make_params(row):
        """
        构造post请求参数
        :param row:检索关键字字典
        :return:
        """
        # 模板：'&conditions=searchWord+a+QWJS++%E5%85%A8%E6%96%87%E6%A3%80%E7%B4%A2:a'
        query_params = ''
        for item in row.items():
            word_class = CONTRAST_TABLE[item[0]]
            if word_class == 'CPRQ':
                word = ''
            else:
                word = quote(item[1])
            _ = quote(item[0] + ':' + item[1])
            query_params += '&conditions=searchWord+{}+{}++{}'.format(word, word_class, _)
        return query_params

    @staticmethod
    def make_guid():
        guid1 = ''
        for _, i in enumerate(range(8)):
            num = int((1 + random.random()) * 65536) | 0
            guid = hex(num)[3:]
            if _ == 0 or _ == 3:
                guid1 += guid
            elif _ == 1 or _ == 2 or _ == 4:
                guid1 += (guid + '-')
            else:
                guid1 += guid
        return guid1

    def get_number(self):
        """"""
        headers = {
            'Host': 'wenshu.court.gov.cn',
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'Origin': 'http://wenshu.court.gov.cn',
            'X-Requested-With': 'XMLHttpRequest',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Language': 'zh-CN,zh;q = 0.9',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': 'http://wenshu.court.gov.cn/'
        }
        url = 'http://wenshu.court.gov.cn/ValiCode/GetCode'
        data = {'guid': self.guid}
        retry = self.retries

        def fun():
            nonlocal retry
            retry -= 1
            try:
                headers.setdefault('User-Agent', self.ua)
                proxies = self.make_proxies()
                response = self.s.post(url, data=data, proxies=proxies, headers=headers, timeout=TIMEOUT)
                # response = self.s.post(url, data=data, headers=headers)
                if isinstance(response, Response) and response.status_code == 200:
                    number = response.text
                    return number
                else:
                    raise ValueError("获取number参数出错!")
            except (ReadTimeout, ProxyError, ConnectionError, ContentDecodingError, ChunkedEncodingError,
                    ValueError, KeyError):
                if retry > 0:
                    return fun()
                else:
                    return None
        return fun()

    def get_vjkl5(self):
        """"""
        url = 'http://wenshu.court.gov.cn/list/list/?sorttype=1&number={}&guid={}{}'
        url = url.format(self.number, self.guid, self.params)
        headers = {
            'Host': 'wenshu.court.gov.cn',
            'Connection': 'keep-alive',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,'
                      '*/*;q=0.8,application/signed-exchange;v=b3',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'http://wenshu.court.gov.cn/',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Language': 'zh-CN,zh;q = 0.9',
        }
        headers.setdefault('User-Agent', self.ua)
        try:
            proxies = self.make_proxies()
            response = self.s.get(url, proxies=proxies, headers=headers, timeout=TIMEOUT)
            # response = self.s.get(url, headers=headers)
            if isinstance(response, Response) and response.status_code == 200:
                response.encoding = 'utf-8'
                try:
                    dynamicurl = re.search('dynamicurl="(.*?)"', response.text).group(1)
                    wzwsquestion = re.search('wzwsquestion="(.*?)"', response.text).group(1)
                    wzwsfactor = re.search('wzwsfactor="(.*?)"', response.text).group(1)
                    wzwsmethod = re.search('wzwsmethod="(.*?)"', response.text).group(1)
                    wzwsparams = re.search('wzwsparams="(.*?)"', response.text).group(1)
                except AttributeError:
                    raise ValueError("获取vjkl5参数出错!解析错误")

                js_dynamicurl = '''
                var dynamicurl="{}";var wzwsquestion="{}";var wzwsfactor="{}";var wzwsmethod="{}";var wzwsparams="{}";
                '''.format(dynamicurl, wzwsquestion, wzwsfactor, wzwsmethod, wzwsparams)
                js_code = js_dynamicurl + js_wzwschallenge
                ctx = execjs.compile(js_code)
                wzwschallenge = ctx.call("wzwschallenge")
                print('wzwschallenge>>> ', wzwschallenge)
                next_url = 'http://wenshu.court.gov.cn' + dynamicurl + '?' + 'wzwschallenge=' + wzwschallenge

                self.s.get(next_url, proxies=proxies, headers=headers, timeout=TIMEOUT)
                # resp = self.s.get(next_url, headers=headers)
                vjkl5 = self.s.cookies.get_dict()['vjkl5']
                if not vjkl5:
                    raise ValueError("获取vjkl5参数出错!")
                else:
                    return vjkl5
            else:
                raise ValueError("获取vjkl5参数出错!")
        except (ReadTimeout, ProxyError, ConnectionError, ContentDecodingError, ValueError, KeyError) as e:
            print(e)
            return self.get_vjkl5()

    def get_caselist_page(self, row, index=1):
        """
        发起检索请求，返回检索后的页面response
        :param row: 检索关键字字典
        :param index: 检索结果页面
        :return:
        """
        retry = RETRY
        # 构造请求参数
        url = 'http://wenshu.court.gov.cn/List/ListContent'
        headers = {
            'Host': 'wenshu.court.gov.cn',
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'Origin': 'http://wenshu.court.gov.cn',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Language': 'zh-CN,zh;q = 0.9',
        }
        headers.setdefault('User-Agent', self.ua)
        param = ''
        for key, value in row.items():
            param += '{}:{},'.format(key, value)
        param = param.strip(',')
        data = {
            'Direction': 'desc',
            'guid': self.guid,
            'Index': str(index),
            'number': self.number,
            'Order': '裁判日期',
            'Page': '20',
            'Param': param,
            'vl5x': self.vl5x
        }

        def fun():
            proxies = self.make_proxies()
            nonlocal retry
            if retry <= 0:
                return None
            else:
                retry -= 1
            try:
                # 发起检索请求
                print('请求第{}次——'.format(RETRY - retry), end='', flush=True)
                #   &guid={}   guid,
                refer = 'http://wenshu.court.gov.cn/list/list/?sorttype=1&number={}&guid={}{}'
                referer = refer.format(self.number, self.guid, self.params)
                headers.update({'Referer': referer})

                response = self.s.post(url, headers=headers, proxies=proxies, data=data, timeout=TIMEOUT)
                # response = self.s.post(url, headers=headers, data=data, timeout=TIMEOUT)
                if isinstance(response, Response):
                    print('{}'.format(response.status_code), flush=True)
                    # print(response.text)
                    if response.text == '"[]"' or response.text == '"remind key"':
                        print("响应错误!从新获取参数number、vl5x!", flush=True)

                        self.guid = self.make_guid()
                        # 获取请求参数number
                        self.number = self.get_number()
                        print('number>>> ', self.number)
                        # 获取请求cookie:vjkl5, 并获取请求参数vl5x
                        vjkl5 = self.get_vjkl5()
                        print('vjkl5>>> ', vjkl5)
                        # print('cookies>>> ', s.cookies.get_dict())
                        self.vl5x = getvjkl5(vjkl5)
                        print('vl5x>>> ', self.vl5x)
                        raise ValueError("Response 响应错误!{}".format(response.text))

                    else:
                        caselist = re.findall(r'{.+?}', response.json(), re.S)   # 使用response.json()处理防止json.loads()报错
                        caselist = [json.loads(i) for i in caselist]
                        try:
                            count = caselist[0]['Count']
                            self.item['JSJGSL'] = int(count)
                            print("响应正常!", flush=True)
                            return caselist
                        except (KeyError, IndexError):
                            raise ValueError("请求结果异常!")

                else:
                    raise ValueError("Response 请求出错!")
            except (ReadTimeout, ProxyError, ConnectionError, ContentDecodingError, ChunkedEncodingError,
                    ValueError, KeyError):
                if retry == 3 or retry == 1:
                    time.sleep(60)
                return fun()
        return fun()

    def parse_page(self, caselist):
        """
        解析页面响应，返回页面数据
        :param caselist:
        :return:
        """
        runeval = ''
        for i, case in enumerate(caselist):
            # case = json.loads(case)
            if i == 0:
                runeval = caselist[0]['RunEval']
                pass
            else:
                print(i)
                self.item['CPYZDYW'] = case['裁判要旨段原文']
                self.item['AJLX'] = case['案件类型']
                self.item['CPRQ'] = case['裁判日期']
                self.item['AJMC'] = case['案件名称']
                self.item['docid'] = case['文书ID']
                self.item['SPCX'] = case['审判程序']
                self.item['AH'] = case['案号']
                self.item['FYMC'] = case['法院名称']
                if '不公开理由' in case.keys():
                    self.item['BGKLY'] = case['不公开理由']
                else:
                    self.item['BGKLY'] = ''
                self.item['docid'] = decode_docid(runeval, case['文书ID'])

                print(self.item['docid'])
                self.sqlmanager.inset_wenshu_cases(self.item)
                self.item.clear()
                # yield self.item

    def do_spider(self, row):
        """"""
        # 请求头
        self.s.cookies.clear()
        self.ua = UserAgent().random
        # 获取请求随机参数guid
        self.guid = self.make_guid()
        print('guid1>>>> {}'.format(self.guid), flush=True)
        self.s.cookies.update({'guid': self.guid})
        # 获取请求参数number
        self.number = self.get_number()
        print('number>>> ', self.number)
        self.params = self.make_params(row)
        # 获取请求cookie:vjkl5, 并获取请求参数vl5x
        vjkl5 = self.get_vjkl5()
        print('vjkl5>>> ', vjkl5)
        # print('cookies>>> ', s.cookies.get_dict())
        self.vl5x = getvjkl5(vjkl5)
        print('vl5x>>> ', self.vl5x)

        # 发起检索请求，获取案件列表页，并解析
        print('请求第 1 页!', flush=True)
        caselist = self.get_caselist_page(row)

        try:
            pages = math.ceil(self.item['JSJGSL'] / 10)
        except KeyError:
            self.f.write('1、')   # 检索失败
            return
        if pages == 0:
            self.f.write('1+ 、')  # 解析存储成功(无数据）
            return
        elif pages == 1:
            if isinstance(caselist, list):
                self.item['JSTJ'] = self.params
                try:
                    self.parse_page(caselist)
                    self.f.write('1+ 、')  # 解析存储成功
                except Exception:
                    self.f.write('1- 、')  # 解析存储失败
            else:
                self.f.write('1、')  # 检索失败
                # print("检索结果列表响应出错， 程序退出!")
                # sys.exit(-1)
        else:
            if isinstance(caselist, list):
                self.item['JSTJ'] = self.params
                try:
                    self.parse_page(caselist)
                    self.f.write('1+ 、')  # 解析存储成功
                except Exception:
                    self.f.write('1- 、')  # 解析存储失败
            else:
                self.f.write('1、')  # 检索失败
                # print("检索结果列表响应出错， 程序退出!")
                # sys.exit(-1)
            print('pages>>> ', pages)
            for page in range(2, pages + 1):
                print('请求第 {} 页!'.format(page), flush=True)
                try:
                    caselist = self.get_caselist_page(row, index=page)
                except Exception:
                    self.f.write('{}、'.format(page))  # 检索失败
                if isinstance(caselist, list):
                    self.item['JSTJ'] = self.params
                    try:
                        self.parse_page(caselist)
                        self.f.write('{}+ 、'.format(page))  # 解析存储成功
                    except Exception:
                        self.f.write('{}- 、'.format(page))  # 解析存储失败
                else:
                    self.f.write('{}、'.format(page))  # 检索失败

    def __del__(self):
        self.f.close()


def date_judge(year, month):
    """输入年月， 返回当月有多少天"""
    if month != 2:
        dates = MONTH_TABLE[str(month)]
    else:
        if year % 4 != 0 and year % 400 != 0:
            dates = 28
        else:
            dates = 29
    return dates


def get_case_list():
    """从2000年1月1日开始，按月检索关键字，并记录检索失败日期与检索失败页码"""
    caselistspider = CaseListSpider()
    for row in get_keyword():
        s_row = json.dumps(row, ensure_ascii=False)
        for year in range(2000, 2020):
            for month in range(1, 13):
                if year == 2008 and month == 6:
                    sys.exit(0)
                else:
                    dates = date_judge(year, month)
                    row['裁判日期'] = '{}-{}-01 TO {}-{}-{}'.format(str(year), str(month), str(year), str(month),
                                                                   str(dates))
                    line = '    ' + row['裁判日期'] + ' : '

                    caselistspider.f.write(s_row)
                    caselistspider.f.write(line)
                    print(s_row)
                    print(line)

                    caselistspider.do_spider(row)

                    caselistspider.f.write('\n')
                    if month == 12:
                        caselistspider.f.write('\n')
                    caselistspider.f.flush()


if __name__ == "__main__":
    get_case_list()