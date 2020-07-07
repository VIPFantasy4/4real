# -*- coding: utf-8 -*-

from .deck import Deck
import weakref
import random
import math


class Phase:
    def __init__(self, chain):
        self._chain = weakref.proxy(chain)
        self._next = None

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._chain.shift(self._next)

    async def tick(self):
        raise NotImplementedError


class DrawPhase(Phase):
    DECK = [(0, 0), (0, 1)] + [(i, j) for i in range(1, 14) for j in range(4)]

    def __enter__(self):
        if self._chain.duel.validate():
            _id, status, gamblers = self._chain.duel.view()
            random.shuffle(self.DECK)
            once = random.randint(4, 17)
            t = int(math.ceil(17 / once))
            triple = [{} for _ in range(3)]
            for i in range(t):
                n = once * 3 * i
                for j in range(n, n + (17 - once * i if t - 1 == i else once)):
                    for i in range(3):
                        card = self.DECK[j + once * i]
                        triple[i].setdefault(card[0], []).append(card[1])
            for addr, gambler in random.sample(gamblers.items(), 3):
                gambler.deal(triple.pop())
        return self
