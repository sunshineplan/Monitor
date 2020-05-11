#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

from Bank import NBCB

PATH = os.path.abspath(os.path.dirname(__file__))


class Monitor:
    def __init__(self):
        self.tasks = []
        self.content = ''
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = RotatingFileHandler(
            os.path.join(PATH, 'Monitor.log'),
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
            self.logger.info(self.content.replace('↑', ' ').replace('↓', ' '))
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
