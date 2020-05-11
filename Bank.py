#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from time import sleep

import requests


class Bank:
    def __init__(self):
        self.name = ''
        self.income = 0
        self.limit = ''
        self.agent = 'Chrome'

    def __str__(self):
        self.fetch()
        return self.formatter()

    def fetch(self):
        pass

    @staticmethod
    def markup(old, new):
        if old != '':
            old = float(old.replace('↑', '').replace('↓', ''))
            if old > new:
                return f'{new}↓'
            elif old < new:
                return f'{new}↑'
            else:
                return f'{old}'
        return f'{new}↑'

    def formatter(self):
        return f'{self.name}({self.income}) {self.limit:<13}'


class NBCB(Bank):
    def __init__(self, id):
        super().__init__()
        self.id = id
        self.headers = {'X_GW_APP_ID': '1101', 'X-GW-BACK-HTTP-METHOD': 'GET',
                        'User-Agent': self.agent}
        self.url = 'https://i.nbcb.com.cn/zhongtai/finance/prds/p-onsale-channel?turnPageBeginPos=1&turnPageShowNum=6&prdOrigin=0&prdClassify=0'

    def fetch(self):
        respone = requests.post(self.url, headers=self.headers).json()
        for i in respone['body']['list']:
            if i['prdCode'] == self.id:
                self.name = i['prdName']
                self.income = i['expectedRateShow']
                self.limit = self.markup(self.limit, i['perUseLimit'])
                break


class Monitor:
    def __init__(self):
        self.tasks = []
        self.content = ''
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = RotatingFileHandler(
            'Monitor.log',
            maxBytes=1*1024*1024,
            backupCount=10,
            encoding='utf8'
        )
        handler.setFormatter(logging.Formatter('%(asctime)s  %(message)s'))
        self.logger.addHandler(handler)

    def add(self, *objs):
        for obj in objs:
            self.tasks.append(obj)

    async def reload(self):
        while True:
            self.content = ''.join([str(i) for i in self.tasks])
            await asyncio.sleep(1)

    async def record(self):
        while True:
            self.logger.info(self.content.replace('↑', '').replace('↓', ''))
            await asyncio.sleep(15)

    async def display(self):
        while True:
            now = f'{datetime.now():%Y-%m-%d %H:%M:%S}'
            print('', end='\r')
            print(f'{now:<21}{self.content}', end='\r')
            await asyncio.sleep(0.1)

    async def run(self):
        await asyncio.gather(
            self.reload(),
            self.display(),
            self.record(),
            return_exceptions=True
        )


if __name__ == '__main__':
    m = Monitor()
    m.add(NBCB('1005'), NBCB('1004'))
    try:
        asyncio.run(m.run())
    except KeyboardInterrupt:
        pass
