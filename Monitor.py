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

PATH = os.path.abspath(os.path.dirname(__file__))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    os.path.join(PATH, 'Monitor.log'),
    maxBytes=1*1024*1024,
    backupCount=10
)
handler.setFormatter(logging.Formatter('%(asctime)s  %(message)s'))
logger.addHandler(handler)


class Monitor:
    def __init__(self):
        self.nbcb_1004_income = '-'
        self.nbcb_1004_limit = None
        self.nbcb_1005_income = '-'
        self.nbcb_1005_limit = None
        self.spdb_flag = 0
        self.spdb_2301187111_income = '-'
        self.spdb_2301187111_limit = None
        self.parserconfig()

    def parserconfig(self):
        config = configparser.ConfigParser()
        config.read(os.path.join(PATH, 'Monitor.ini'))
        self.timeout = config.getint('DEFAULT', 'timeout', fallback=5)
        self.log_interval = config.getint(
            'DEFAULT', 'log_interval', fallback=15)
        self.config_interval = config.getint(
            'DEFAULT', 'config_interval', fallback=150)
        self.income_interval = config.getint(
            'DEFAULT', 'income_interval', fallback=3600)
        self.agent = config.get('DEFAULT', 'agent', fallback='Monitor')
        self.nbcb_interval = config.getint('nbcb', 'interval', fallback=7)
        self.spdb_interval = config.getint('spdb', 'interval', fallback=1)
        self.spdb_cookies = config.get('spdb', 'cookies', fallback='')

    async def income(self):
        while True:
            headers = {'User-Agent': self.agent}
            data = {'prodId': 1004, 'replyPage': 1}
            try:
                self.nbcb_1004_income = BeautifulSoup(requests.post('https://mybank.nbcb.com.cn/doorbank/queryNav.do',
                                                                    params=data, headers=headers).text, 'html.parser').find('td', class_='td4').text
            except:
                self.nbcb_1004_income = '-'
            data = {'prodId': 1005, 'replyPage': 1}
            try:
                self.nbcb_1005_income = BeautifulSoup(requests.post('https://mybank.nbcb.com.cn/doorbank/queryNav.do',
                                                                    params=data, headers=headers).text, 'html.parser').find('td', class_='td4').text
            except:
                self.nbcb_1005_income = '-'
            headers = {'Cookie': self.spdb_cookies}
            data = {'FinanceNo': '2301187111',
                    'nearDate': 'nearOneWeek', 'Hierarchy': '2301187111-A'}
            try:
                self.spdb_2301187111_income = loads(requests.post('https://ebank.spdb.com.cn/msper-web-finance/QueryFinanceIncomeByAjax.json',
                                                                  json=data, headers=headers).json()['dataList'])[-1]
            except:
                self.spdb_2301187111_income = '-'
            await asyncio.sleep(self.income_interval)

    async def nbcb(self):
        while True:
            try:
                headers = {'User-Agent': self.agent}
                data = {'riskLevel': 2, 'isSelling': 1, 'orderType': 2,
                        'investTerm': 4, 'TemplateCode': 9901, 'WEB_CHN': 'NH'}
                limit = requests.post('https://e.nbcb.com.cn/perbank/HB06201_noSessionFinancialProds.do',
                                      params=data, headers=headers, timeout=self.timeout).json()['cd']['iProdUseLimits']
                for i in limit:
                    if i['prodId'] == '1004':
                        self.nbcb_1004_limit = self.markup(
                            self.nbcb_1004_limit, (f'天利鑫B({self.nbcb_1004_income})', i['totUseLimit']))
                    if i['prodId'] == '1005':
                        self.nbcb_1005_limit = self.markup(
                            self.nbcb_1005_limit, (f'如意鑫A({self.nbcb_1005_income})', i['totUseLimit']))
            except:
                self.nbcb_1004_limit = self.nbcb_1005_limit = None
            await asyncio.sleep(self.nbcb_interval)

    def _spdb(self, test=False):
        if test or self.spdb_flag:
            headers = {'Cookie': self.spdb_cookies}
            data = {'FinanceNo': '2301187111',
                    'nearDate': 'nearOneWeek', 'Hierarchy': '2301187111-A'}
            try:
                limit = requests.post('https://ebank.spdb.com.cn/msper-web-finance/QueryAvlLimitAmnt.json',
                                      json=data, headers=headers, timeout=self.timeout).json()['CanUseQuota'].replace(',', '')
                if not test:
                    self.spdb_2301187111_limit = self.markup(
                        self.spdb_2301187111_limit, (f'天添盈增利1号({self.spdb_2301187111_income}%)', limit))
                self.spdb_flag = 1
            except:
                self.spdb_flag = 0
                self.spdb_2301187111_limit = None
                raise ValueError

    async def spdb(self, interval, test=False):
        while True:
            try:
                self._spdb()
            except:
                pass
            await asyncio.sleep(self.spdb_interval)

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
        products = [self.nbcb_1004_limit,
                    self.nbcb_1005_limit, self.spdb_2301187111_limit]
        products = [i for i in products if i]
        contents = []
        for i in products:
            if with_mark:
                contents.append(f'{i[0]}-{i[1]:<13}')
            else:
                contents.append(f'{i[0]}-{i[1][:-1]:<12}')
        output = ''
        for i in contents:
            output += i
        return output

    async def record(self):
        while True:
            logger.info(self.formatter(with_mark=False))
            await asyncio.sleep(self.log_interval)

    async def reload(self):
        while True:
            self.parserconfig()
            await asyncio.sleep(self.config_interval)

    async def display(self):
        while True:
            now = f'{datetime.now():%Y-%m-%d %H:%M:%S}'
            print('', end='\r')
            print(f'{now:<21}{self.formatter()}', end='\r')
            await asyncio.sleep(0.1)

    async def main(self):
        await asyncio.gather(
            self.income(),
            self.nbcb(),
            self.spdb(self.config_interval, test=True),
            self.spdb(self.spdb_interval),
            self.record(),
            self.reload(),
            self.display()
        )


if __name__ == '__main__':
    try:
        asyncio.run(Monitor().main())
    except KeyboardInterrupt:
        pass
