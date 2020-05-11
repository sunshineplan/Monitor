#!/usr/bin/env python3
# -*- coding: utf-8 -*-


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
