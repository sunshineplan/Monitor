#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import configparser
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    'Monitor.log', maxBytes=1*1024*1024, backupCount=10)
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
        config.read('Monitor.ini')
        self.log_interval = config.getint(
            'DEFAULT', 'log_interval', fallback=15)
        self.config_interval = config.getint(
            'DEFAULT', 'config_interval', fallback=300)
        self.agent = config.get('DEFAULT', 'agent', fallback='Monitor')
        self.nbcb_interval = config.getint('nbcb', 'interval', fallback=7)
        self.spdb_interval = config.getint('spdb', 'interval', fallback=1)
        self.spdb_test_interval = config.getint(
            'spdb', 'test_interval', fallback=60)
        self.spdb_cookies = config.get('spdb', 'cookies', fallback='')

    async def nbcb(self):
        try:
            data = {'riskLevel': 2, 'isSelling': 1, 'orderType': 2,
                    'investTerm': 4, 'TemplateCode': 9901, 'WEB_CHN': 'NH'}
            response = requests.get('https://e.nbcb.com.cn/perbank/HB06201_noSessionFinancialProds.do',
                                    params=data, headers={'user-agent': self.agent})
            for i in response.json()['cd']['iProdUseLimits']:
                if i['prodId'] == '1004':
                    self.nbcb_1004 = self.markup(
                        self.nbcb_1004, ('天利鑫B', i['totUseLimit']))
                if i['prodId'] == '1005':
                    self.nbcb_1005 = self.markup(
                        self.nbcb_1005, ('如意鑫A', i['totUseLimit']))
        except:
            self.nbcb_1004 = self.nbcb_1005 = None
        await asyncio.sleep(self.nbcb_interval)
        asyncio.ensure_future(self.nbcb())

    async def spdb(self, test=False):
        if test or self.spdb_flag:
            data = {'FinanceNo': '2301187111'}
            response = requests.post(
                'https://ebank.spdb.com.cn/msper-web-finance/QueryAvlLimitAmnt.json', json=data, headers={'Cookie': self.spdb_cookies})
            jsonresponse = response.json()
            if not test:
                self.spdb_2301187111 = self.markup(
                    self.spdb_2301187111, ('天添盈增利1号', jsonresponse['CanUseQuota'].replace(',', '')))
                await asyncio.sleep(self.spdb_interval)
                asyncio.ensure_future(self.spdb())

    async def spdb_test(self):
        try:
            await self.spdb(test=True)
            self.spdb_flag = 1
        except:
            self.spdb_flag = 0
            self.spdb_2301187111 = None
        await asyncio.sleep(self.spdb_test_interval)
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
                contents.append('{}-{}'.format(i[0], i[1]))
            else:
                contents.append('{}-{}'.format(i[0], i[1][:-1]))
        output = ''
        for i in contents:
            output += f'{i:<18}'
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
        print('{:<21}{}'.format(datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S'), self.formatter()), end='\r')
        await asyncio.sleep(1)
        asyncio.ensure_future(self.display())

    async def main(self):
        asyncio.ensure_future(self.spdb_test())
        asyncio.ensure_future(self.nbcb())
        asyncio.ensure_future(self.spdb())
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
