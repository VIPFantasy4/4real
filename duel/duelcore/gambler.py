# -*- coding: utf-8 -*-

import weakref

class Gambler:
    def __init__(self, duel, addr):
        self.addr = addr
        self._duel = weakref.proxy(duel)
        self._cards = None

    def deal(self, cards):
        self._cards = cards