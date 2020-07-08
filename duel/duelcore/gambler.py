# -*- coding: utf-8 -*-

import weakref


class Gambler:
    def __init__(self, duel, addr):
        self.addr = addr
        self._duel = weakref.proxy(duel)
        self._cards = None
        self._role = 0

    def deal(self, cards):
        self._cards = cards

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, role):
        self._role = role
