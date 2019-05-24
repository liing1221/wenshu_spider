# -*- coding: utf-8 -*-
"""
    @Project     : wenshu_spider
    @File        : wenshu_case_detail_spider.py
    @Create_Date : 2019-05-21 15:39
    @Update_Date : 2019-05-21 15:39
    @Author      : liing
    @Email       : liing1221@163.com
    @Software    : PyCharm
"""
from __future__ import print_function
import os
import re
import time
import json
import random
import execjs
import requests
from urllib.parse import quote
from fake_useragent import UserAgent
from requests import adapters, Response
from concurrent.futures import ProcessPoolExecutor
from requests.exceptions import ChunkedEncodingError
from requests.exceptions import ReadTimeout, ProxyError, ConnectionError, ContentDecodingError
from middlewares.settings import RETRY, TIMEOUT, CONTRAST_TABLE, LEN_SQR, DATA_FILE
from middlewares.proxymanage import ProxyManager
from middlewares.redismanage import RedisManager
from middlewares.mysqlmanage import SqlManager
from middlewares.js import js_wzwschallenge


requests.adapters.DEFAULT_RETRIES = 10


class CaseDetailSpider:
    '''根据传入的案件信息（docid， jstj）抓取解析存储案件详情'''

    def __init__(self, row):
        """

        """
        self.item = {}
        self.row = row
        self.params = quote(row['JSTJ'])
        self.retries = RETRY
        self.timeout = TIMEOUT
        self.len_sqr = LEN_SQR  # 申请人判断：解析时80以内判断是案件人信息，以上为文字描述
        self.guid = ''
        self.number = ''
        self.proxymanager = ProxyManager(pool=False)
        self.sqlmanager = SqlManager(2)
        # self.f = open('./middlewares/page_err.txt', 'a')
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
        ua = UserAgent().random
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
        headers.setdefault('User-Agent', ua)
        url = 'http://wenshu.court.gov.cn/ValiCode/GetCode'
        data = {'guid': self.guid}
        try:
            proxies = self.make_proxies()
            response = self.s.post(url, data=data, proxies=proxies, headers=headers, timeout=TIMEOUT)
            # response = self.s.post(url, data=data, headers=headers, timeout=TIMEOUT)
            if isinstance(response, Response) and response.status_code == 200:
                number = response.text
                return number
            else:
                raise ValueError("获取number参数出错!")
        except (ReadTimeout, ProxyError, ConnectionError, ContentDecodingError, ChunkedEncodingError,
                ValueError, KeyError):
            return self.get_number()

    def get_vjkl5(self):
        """"""
        ua = UserAgent().random
        url = 'http://wenshu.court.gov.cn/list/list/?sorttype=1&number={}&guid={}{}'
        url = url.format(self.number, self.guid, self.params, timeout=TIMEOUT)
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
        headers.setdefault('User-Agent', ua)
        try:
            proxies = self.make_proxies()
            print('进程：{} Proxies>>> {}'.format(os.getpid(), proxies))
            response = self.s.get(url, proxies=proxies, headers=headers, timeout=TIMEOUT)
            # response = self.s.get(url, headers=headers, timeout=TIMEOUT)
            if isinstance(response, Response) and response.status_code == 200:
                response.encoding = 'utf-8'
                try:
                    dynamicurl = re.search('dynamicurl="(.*?)"', response.text).group(1)
                    wzwsquestion = re.search('wzwsquestion="(.*?)"', response.text).group(1)
                    wzwsfactor = re.search('wzwsfactor="(.*?)"', response.text).group(1)
                    wzwsmethod = re.search('wzwsmethod="(.*?)"', response.text).group(1)
                    wzwsparams = re.search('wzwsparams="(.*?)"', response.text).group(1)
                except AttributeError:
                    return None

                js_dynamicurl = '''
                var dynamicurl="{}";var wzwsquestion="{}";var wzwsfactor="{}";var wzwsmethod="{}";var wzwsparams="{}";
                '''.format(dynamicurl, wzwsquestion, wzwsfactor, wzwsmethod, wzwsparams)
                js_code = js_dynamicurl + js_wzwschallenge
                ctx = execjs.compile(js_code)
                wzwschallenge = ctx.call("wzwschallenge")
                print('进程：{} wzwschallenge>>> {}'.format(os.getpid(), wzwschallenge))
                next_url = 'http://wenshu.court.gov.cn' + dynamicurl + '?' + 'wzwschallenge=' + wzwschallenge

                self.s.get(next_url, proxies=proxies, headers=headers, timeout=TIMEOUT)
                # resp = self.s.get(next_url, headers=headers, timeout=TIMEOUT)
                vjkl5 = self.s.cookies.get_dict()['vjkl5']
                return vjkl5
            else:
                raise ValueError("获取number参数出错!")
        except (ReadTimeout, ProxyError, ConnectionError, ContentDecodingError, ChunkedEncodingError,
                ValueError, KeyError) as e:
            print(e)
            return

    def get_page(self):
        """"""
        row = self.row
        retry = RETRY
        url1 = 'http://wenshu.court.gov.cn/content/content?DocID={}&KeyWord='.format(row['docid'])
        url = 'http://wenshu.court.gov.cn/CreateContentJS/CreateContentJS.aspx?DocID={}'.format(row['docid'])

        def fun():
            proxies = self.make_proxies()
            self.guid = self.make_guid()
            print('进程：{} Start get Number'.format(os.getpid()))
            self.number = self.get_number()
            print('进程：{} Start get vjkl5'.format(os.getpid()))
            self.vjkl5 = self.get_vjkl5()
            if not self.vjkl5:
                return
            nonlocal retry
            if retry <= 0:
                return None
            else:
                retry -= 1
            headers = {
                'Host': 'wenshu.court.gov.cn',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Accept': 'text/javascript, application/javascript, */*',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': url1,
                'Accept-Encoding': 'gzip,deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9'
            }

            try:
                print('进程：{} Start get Response'.format(os.getpid()))
                headers.setdefault('User-Agent', UserAgent().random)
                response = self.s.get(url, headers=headers, proxies=proxies, timeout=TIMEOUT)
                # response = self.s.get(url, headers=headers, timeout=TIMEOUT)
                if isinstance(response, Response) and response.status_code == 200:
                    response.encoding = 'utf-8'
                    try:
                        dynamicurl = re.search('dynamicurl="(.*?)"', response.text).group(1)
                        wzwsquestion = re.search('wzwsquestion="(.*?)"', response.text).group(1)
                        wzwsfactor = re.search('wzwsfactor="(.*?)"', response.text).group(1)
                        wzwsmethod = re.search('wzwsmethod="(.*?)"', response.text).group(1)
                        wzwsparams = re.search('wzwsparams="(.*?)"', response.text).group(1)
                    except AttributeError:
                        return None

                    js_dynamicurl = '''
                    var dynamicurl="{}";var wzwsquestion="{}";var wzwsfactor="{}";var wzwsmethod="{}";var wzwsparams
                    ="{}";'''.format(dynamicurl, wzwsquestion, wzwsfactor, wzwsmethod, wzwsparams)
                    js_code = js_dynamicurl + js_wzwschallenge
                    ctx = execjs.compile(js_code)
                    wzwschallenge = ctx.call("wzwschallenge")
                    print('进程：{} wzwschallenge>>> {}'.format(os.getpid(), wzwschallenge))
                    next_url = 'http://wenshu.court.gov.cn' + dynamicurl + '?' + 'wzwschallenge=' + wzwschallenge

                    resp = self.s.get(next_url, proxies=proxies, headers=headers, timeout=TIMEOUT)
                    # resp = self.s.get(next_url, headers=headers, timeout=TIMEOUT)
                    if isinstance(resp, Response) and resp.status_code == 200:
                        resp.encoding = 'utf-8'
                        if 'window.location.href=' in response.text:
                            raise ValueError("请求详情页出错!")
                        else:
                            return resp
                    else:
                        raise ValueError("请求详情页出错!")
                else:
                    raise ValueError("请求详情页出错!")
            except (ReadTimeout, ProxyError, ConnectionError, ContentDecodingError, ChunkedEncodingError,
                    ValueError, KeyError) as e:
                print(e)
                if retry == 3 or retry == 1:
                    time.sleep(60)
                return fun()
        return fun()

    def parse_page(self, response):
        """"""
        item = {}
        item['page'] = response.content
        try:
            caseinfos = re.search(r'caseinfo=JSON.stringify\((.*?)\);\$\(', response.text, re.S).group(1)
        except AttributeError:
            return
        caseinfos = json.loads(caseinfos, encoding='utf-8')
        for caseinfo in caseinfos.items():
            if caseinfo[0] in CONTRAST_TABLE.keys():
                if caseinfo[0] not in item.keys():
                    item[CONTRAST_TABLE[caseinfo[0]]] = caseinfo[1]
                elif not item[CONTRAST_TABLE[caseinfo[0]]]:
                    item[CONTRAST_TABLE[caseinfo[0]]] = caseinfo[1]
            else:
                print('进程：{} 解析caseinfo:未存储字段：{}'.format(os.getpid(), caseinfo))

        item['WSFBRQ'] = re.search(r'\\"PubDate\\":\\"(.*?)\\",\\"Html', response.text, re.S).group(1)
        names = re.findall(r'<a type=\'dir\' name=\'(.*?)\'', response.text, re.S)
        print('进程：{} 解析段落names>>> {}'.format(os.getpid(), names))
        try:
            item["WBSB"] = re.search(r'(<a type=\'dir\' name=\'WBSB\'.*?)<a type', response.text, re.S).group(1)
        except AttributeError:
            item['WBSB'] = ''
        try:
            if "SSJL" in names:
                item['DSRXX'] = re.search(r'(<a type=\'dir\' name=\'DSRXX\'.*?)<a type', response.text, re.S).group(1)
            else:
                item['DSRXX'] = re.search(r'(<a type=\'dir\' name=\'DSRXX\'.*?判决如下：.*?>)', response.text, re.S).group(1)
        except AttributeError:
            item['DSRXX'] = ''
        try:
            item['SSJL'] = item['CPYZ'] = ''
            if "SSJL" in names and "CPYZ" in names:
                ssjl = re.search(r'(<a type=\'dir\' name=\'SSJL\'.*?)<a type', response.text, re.S)
                if ssjl:
                    item['SSJL'] = ssjl.group(1)
                cpyz = re.search(r'(<a type=\'dir\' name=\'CPYZ\'.*?判决如下：.*?>)', response.text, re.S)
                if cpyz:
                    item['CPYZ'] = cpyz.group(1)
            elif "SSJL" in names and "CPYZ" not in names:
                ssjl = re.search(r'(<a type=\'dir\' name=\'SSJL\'.*?判决如下：.*?>)', response.text, re.S)
                if ssjl:
                    item['SSJL'] = ssjl.group(1)
            elif "SSJL" not in names and "CPYZ" in names:
                cpyz = re.search(r'(<a type=\'dir\' name=\'CPYZ\'.*?判决如下：.*?>)', response.text, re.S)
                if cpyz:
                    item['CPYZ'] = cpyz.group(1)
            else:
                pass
        except AttributeError:
            return
        try:
            item['PJJG'] = item['WBWB'] = ''
            if "PJJG" in names and 'WBWB' in names:
                pjjg = re.search(r'(<a type=\'dir\' name=\'PJJG\'.*?)<a type=', response.text, re.S)
                if pjjg:
                    item['PJJG'] = pjjg.group(1)
                div_wbwb = re.search(r'(<a type=\'dir\' name=\'WBWB\'.*?</div>)\\"}";', response.text, re.S)
                if div_wbwb:
                    item['WBWB'] = div_wbwb.group(1)
            elif "PJJG" in names and 'WBWB' not in names:
                pjjg = re.search(r'(<a type=\'dir\' name=\'PJJG\'.*?)<div style=\'TEXT-ALIGN: right;', response.text,
                                 re.S)
                if pjjg:
                    item['PJJG'] = pjjg.group(1)
                div_wbwb = re.search(r'判决如下：.*?>.*?(<div style=\'TEXT-ALIGN: right;.*?>审.*?</div>)\\"}";',
                                     response.text, re.S)
                if div_wbwb:
                    item['WBWB'] = div_wbwb.group(1)
            elif "PJJG" not in names and 'WBWB' in names:
                pjjg = re.search(r'判决如下：.*?>(.*?)<a type=', response.text, re.S)
                if pjjg:
                    item['PJJG'] = pjjg.group(1)
                div_wbwb = re.search(r'(<a type=\'dir\' name=\'WBWB\'.*?</div>)\\"}";', response.text, re.S)
                if div_wbwb:
                    item['WBWB'] = div_wbwb.group(1)
            elif "PJJG" not in names and 'WBWB' not in names:
                pjjg = re.search(r'判决如下：.*?>(.*?)<div style=\'TEXT-ALIGN: right;', response.text, re.S)
                if pjjg:
                    item['PJJG'] = pjjg.group(1)
                div_wbwb = re.search(r'判决如下：.*?>.*?(<div style=\'TEXT-ALIGN: right;.*?>审.*?</div>)\\"}";',
                                     response.text, re.S)
                if div_wbwb:
                    item['WBWB'] = div_wbwb.group(1)
            else:
                pass
        except AttributeError:
            pass

        if item['DSRXX']:
            elements = re.findall(r'LINE-HEIGHT.*?16pt;\'>(.*?)</div>', item['DSRXX'], re.S)
        else:
            elements = re.findall(r'LINE-HEIGHT.*?16pt;\'>(.*?)</div>', response.text, re.S)
        item['TCSQR'] = item['BSQR'] = item['YSBG'] = item['YSDSR'] = key = ''
        dic = {}
        try:
            for n, ele in enumerate(elements):
                if len(ele) > self.len_sqr:
                    break

                # if item['TCSQR']:
                #     tcsqr = item['TCSQR'].split('：')[1]
                #     if len(tcsqr) < 8 and tcsqr in ele:
                #         break
                #     elif len(tcsqr) >= 8 and tcsqr[:6] in ele:
                #         break
                #     else:
                #         pass
                for j in ['法定代表人', '委托代理人']:
                    if j in ele:
                        dic[CONTRAST_TABLE[j]] += ele
                        continue
                for i in ['上诉人', '原告', "申请人", '申请再审人', "再审申请人", '被上诉人', '被告', '原审被告',
                          '被申请人', '原审第三人']:
                    el = ele[:len(i)]
                    if i == el:
                        if dic and key:
                            item[key] += json.dumps(dic, ensure_ascii=False)
                        key = CONTRAST_TABLE[i]
                        dic.clear()
                        dic[key] = ele
                        dic['WTDLR'] = dic['FDDBR'] = ''
                        break
            item[key] += json.dumps(dic, ensure_ascii=False)
        except KeyError:
            self.len_sqr = 2 * LEN_SQR
            for n, ele in enumerate(elements):
                if len(ele) > self.len_sqr:
                    break
                for j in ['法定代表人', '委托代理人']:
                    if j in ele:
                        dic[CONTRAST_TABLE[j]] += ele
                        continue
                for i in ['上诉人', '原告', "申请人", '申请再审人', "再审申请人", '被上诉人', '被告', '原审被告',
                          '被申请人', '原审第三人']:
                    el = ele[:len(i)]
                    if i == el:
                        if dic and key:
                            item[key] += json.dumps(dic, ensure_ascii=False)
                        key = CONTRAST_TABLE[i]
                        dic.clear()
                        dic[key] = ele
                        dic['WTDLR'] = dic['FDDBR'] = ''
                        break
            item[key] += json.dumps(dic, ensure_ascii=False)

        if item['WBWB']:
            wbwbs = re.findall(r'16pt;\'>(.*?)</div>', item['WBWB'], re.S)
        else:
            div_wbwb = re.search(r'(>审.*?</div>)\\"}";', response.text, re.S).group(1)
            wbwbs = re.findall(r'>(.*?)<', div_wbwb, re.S)
        item['SPZ'] = item['SPY'] = item['DLSPY'] = item['SJY'] = item['PSY'] = ''
        for wbwb in wbwbs:
            if len(wbwb) > 20:
                break
            for w in ["审判长", "审判员", "代理审判员", "书记员", "代书记员", "人民陪审员", "陪审员"]:
                spli = w[-1]
                part = wbwb.split(spli)
                part1 = part[0].replace('\u3000', '').replace(' ', '') + spli
                if len(part) < 2:
                    continue
                elif len(part) == 2:
                    part2 = part[1].replace('\u3000', '').replace(' ', '')
                else:
                    part2 = ';'.join(spli.join(part[1:]).replace('\u3000', '').replace(' ', '').split(part1))
                if w == part1:
                    key = CONTRAST_TABLE[w]
                    if w != "代书记员":
                        if not item[key]:
                            item[key] += part2
                        else:
                            item[key] += ';' + part2
                    else:
                        if not item[key]:
                            item[key] += part2 + '(代)'
                        else:
                            item[key] += ';' + part2 + '(代)'
                    break

        return item

    def save_item(self, item):
        """"""
        date = time.strftime('%Y%m%d', time.localtime(time.time()))
        filepath = DATA_FILE + date + '/'
        filename_page = filepath + '{}.txt'.format(item['docid'])
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        with open(filename_page, 'wb') as f:
            f.write(item['page'])
        item['DOC'] = filename_page
        item.pop('page')
        self.sqlmanager.update_one_cases(item, self.row['id'])

    def __del__(self):
        self.s.close()


def put_caseTo_redis():
    '''任务入redis队列'''
    dbmanager = SqlManager(4)
    redismanager = RedisManager()
    queue_key = 'queue_cases'
    for row in dbmanager.get_one_cases():
        if not row:
            break
        else:
            redismanager.put_queue(queue_key, row)


def get_details(row):
    """"""
    casedetailspider = CaseDetailSpider(row)
    print('进程：{} Start get page!'.format(os.getpid()))
    response = casedetailspider.get_page()
    if isinstance(response, Response):
        print('进程：{} Start parse page!'.format(os.getpid()))
        item = casedetailspider.parse_page(response)
        if item and item['SPZ']:
            print('进程：{} Start save item!'.format(os.getpid()))
            casedetailspider.save_item(item)
        else:
            print('进程：{} 数据id:{} 入队！'.format(os.getpid(), row['id']), end='  ', flush=True)
    else:
        print('进程：{} 数据id:{} 入队！'.format(os.getpid(), row['id']), end='  ', flush=True)


def cocurrent_run(processes):
    """建立进程池并发执行搜索"""
    pool = ProcessPoolExecutor()
    for i in range(processes):
        time.sleep(1)
        pool.submit(get_details)
    pool.shutdown()


def spider_details():
    """"""
    redismanager = RedisManager()
    queue_key = 'queue_cases'
    while True:
        row = redismanager.get_queue(queue_key)
        if row:
            print('进程：{} Start spider>> {}!'.format(os.getpid(), row))
            casedetailspider = CaseDetailSpider(row)
            print('进程：{} Start get page!'.format(os.getpid()))
            response = casedetailspider.get_page()
            if isinstance(response, Response):
                print('进程：{} Start parse page!'.format(os.getpid()))
                item = casedetailspider.parse_page(response)
                if item:
                    print('进程：{} Start save item!'.format(os.getpid()))
                    casedetailspider.save_item(item)
                else:
                    queue_key = 'queue_cases'
                    print('进程：{} '.format(os.getpid()), end='  ', flush=True)
                    redismanager.put_queue(queue_key, row)
            else:
                queue_key = 'queue_cases'
                print('进程：{} '.format(os.getpid()), end='  ', flush=True)
                redismanager.put_queue(queue_key, row)
        else:
            break


if __name__ == "__main__":
    # row = {
    # "id": 883,
    # "JSTJ": "&conditions=searchWord+%E4%B8%93%E5%88%A9%E6%B3%95+FLYJ++%E6%B3%95%E5%BE%8B%E4%BE%9D%E6%8D%AE%3A%E4%B8%93%E5%88%A9%E6%B3%95&conditions=searchWord++CPRQ++%E8%A3%81%E5%88%A4%E6%97%A5%E6%9C%9F%3A2014-11-01%20TO%202014-11-30",
    # "docid": "9171d6d2-fcbb-4ab1-95c5-39ffc41f94b2",
    # "status": "0"
    # }
    # get_details(row)

    spider_details()
