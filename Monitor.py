#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import configparser
import logging
import os
from datetime import datetime
from json import loads
from logging.handlers import RotatingFileHandler

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(os.path.join(os.path.abspath(os.path.dirname(
    __file__)), 'Monitor.log'), maxBytes=1*1024*1024, backupCount=10)
handler.setFormatter(logging.Formatter('%(asctime)s  %(message)s'))
logger.addHandler(handler)


class Monitor:
    def __init__(self):
        self.spdb_flag = 0
        self.nbcb_1004 = None
        self.nbcb_1005 = None
        self.spdb_2301187111 = None
        self.parserconfig()

    def parserconfig(self):
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.abspath(
            os.path.dirname(__file__)), 'Monitor.ini'))
        self.log_interval = config.getint(
            'DEFAULT', 'log_interval', fallback=15)
        self.config_interval = config.getint(
            'DEFAULT', 'config_interval', fallback=150)
        self.agent = config.get('DEFAULT', 'agent', fallback='Monitor')
        self.nbcb_interval = config.getint('nbcb', 'interval', fallback=7)
        self.spdb_interval = config.getint('spdb', 'interval', fallback=1)
        self.spdb_cookies = config.get('spdb', 'cookies', fallback='')

    async def nbcb(self):
        try:
            headers = {'user-agent': self.agent}
            data = {'prodId': 1004, 'replyPage': 1}
            income_1004 = BeautifulSoup(requests.post('https://mybank.nbcb.com.cn/doorbank/queryNav.do',
                                                      params=data, headers=headers).text, 'html.parser').find('td', class_='td4').text
            data = {'prodId': 1005, 'replyPage': 1}
            income_1005 = BeautifulSoup(requests.post('https://mybank.nbcb.com.cn/doorbank/queryNav.do',
                                                      params=data, headers=headers).text, 'html.parser').find('td', class_='td4').text
            data = {'riskLevel': 2, 'isSelling': 1, 'orderType': 2,
                    'investTerm': 4, 'TemplateCode': 9901, 'WEB_CHN': 'NH'}
            limit = requests.post('https://e.nbcb.com.cn/perbank/HB06201_noSessionFinancialProds.do',
                                  params=data, headers=headers).json()['cd']['iProdUseLimits']
            for i in limit:
                if i['prodId'] == '1004':
                    self.nbcb_1004 = self.markup(
                        self.nbcb_1004, (f'天利鑫B({income_1004})', i['totUseLimit']))
                if i['prodId'] == '1005':
                    self.nbcb_1005 = self.markup(
                        self.nbcb_1005, (f'如意鑫A({income_1005})', i['totUseLimit']))
        except:
            self.nbcb_1004 = self.nbcb_1005 = None
        await asyncio.sleep(self.nbcb_interval)
        asyncio.ensure_future(self.nbcb())

    async def spdb(self, test=False):
        if test or self.spdb_flag:
            headers = {'Cookie': self.spdb_cookies}
            data = {'FinanceNo': '2301187111',
                    'nearDate': 'nearOneWeek', 'Hierarchy': '2301187111-A'}
            income = loads(requests.post('https://ebank.spdb.com.cn/msper-web-finance/QueryFinanceIncomeByAjax.json',
                                         json=data, headers=headers).json()['dataList'])[-1]
            limit = requests.post('https://ebank.spdb.com.cn/msper-web-finance/QueryAvlLimitAmnt.json',
                                  json=data, headers=headers).json()['CanUseQuota'].replace(',', '')
            if not test:
                self.spdb_2301187111 = self.markup(
                    self.spdb_2301187111, (f'天添盈增利1号({income}%)', limit))
                await asyncio.sleep(self.spdb_interval)
                asyncio.ensure_future(self.spdb())

    async def spdb_test(self):
        try:
            await self.spdb(test=True)
            if not self.spdb_flag:
                asyncio.ensure_future(self.spdb())
            self.spdb_flag = 1
        except:
            self.spdb_flag = 0
            self.spdb_2301187111 = None
        await asyncio.sleep(self.config_interval)
        asyncio.ensure_future(self.spdb_test())

    def markup(self, product, value):
        if not product:
            return (value[0], value[1]+'→')
        if product[0] != value[0]:
            raise ValueError
        if float(product[1][:-1]) > float(value[1]):
            return (value[0], value[1]+'↓')
        elif float(product[1][:-1]) == float(value[1]):
            return (value[0], value[1]+'→')
        else:
            return (value[0], value[1]+'↑')

    def formatter(self, with_mark=True):
        products = [self.nbcb_1004, self.nbcb_1005, self.spdb_2301187111]
        products = [i for i in products if i]
        contents = []
        for i in products:
            if with_mark:
                contents.append('{}-{:<13}'.format(i[0], i[1]))
            else:
                contents.append('{}-{:<12}'.format(i[0], i[1][:-1]))
        output = ''
        for i in contents:
            output += i
        return output

    async def record(self):
        logger.info(self.formatter(with_mark=False))
        await asyncio.sleep(self.log_interval)
        asyncio.ensure_future(self.record())

    async def reload(self):
        self.parserconfig()
        await asyncio.sleep(self.config_interval)
        asyncio.ensure_future(self.reload())

    async def display(self):
        print('', end='\r')
        print('{:<21}{}'.format(datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S'), self.formatter()), end='\r')
        await asyncio.sleep(1)
        asyncio.ensure_future(self.display())

    async def main(self):
        asyncio.ensure_future(self.nbcb())
        asyncio.ensure_future(self.spdb_test())
        asyncio.ensure_future(self.record())
        asyncio.ensure_future(self.reload())
        asyncio.ensure_future(self.display())


if __name__ == '__main__':
    logging.getLogger('asyncio').setLevel(logging.CRITICAL)
    try:
        loop = asyncio.get_event_loop()
        asyncio.ensure_future(Monitor().main())
        loop.run_forever()
    except:
        loop.stop()
    finally:
        loop.close()
