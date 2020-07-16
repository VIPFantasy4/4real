# -*- coding: utf-8 -*-

import weakref


class Gambler:
    def __init__(self, duel, addr):
        self.addr = addr
        self._duel = weakref.proxy(duel)
        self._cards = None
        self.role = 0
        self.bot = -1

    @property
    def gg(self):
        if not self._cards:
            return True

    def deal(self, cards):
        if self._cards is None:
            self._cards = cards
        else:
            for card in cards:
                self._cards.setdefault(card[0], set()).add(card)

    def play(self, cards: dict):
        for k in cards:
            if k not in self._cards or not self._cards[k].issuperset(cards[k]):
                raise
        for k in cards:
            self._cards[k].difference_update(cards[k])
            if not self._cards[k]:
                del self._cards[k]

    def auto(self):
        return None
