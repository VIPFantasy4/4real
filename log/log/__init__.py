# -*- coding: utf-8 -*-

import datetime


def log(fmt: str, *args):
    print(f'{datetime.datetime.now().isoformat()} {fmt}' % args)


def info(fmt: str, *args):
    log(f'[INFO] {fmt}', *args)


def error(fmt: str, *args):
    log(f'[ERROR] {fmt}', *args)
