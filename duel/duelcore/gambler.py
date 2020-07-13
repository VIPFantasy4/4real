# -*- coding: utf-8 -*-

import weakref


class Gambler:
    def __init__(self, duel, addr):
        self.addr = addr
        self._duel = weakref.proxy(duel)
        self._cards = None
        self.role = 0
        self.bot = -1

    def deal(self, cards):
        if self._cards is None:
            self._cards = cards
        else:
            for card in cards:
                self._cards.setdefault(card[0], []).append(card[1])
