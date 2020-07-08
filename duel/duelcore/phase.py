# -*- coding: utf-8 -*-

from collections import OrderedDict
from .exceptions import *
import log
import asyncio
import weakref
import random
import math


class Phase:
    def __init__(self, chain):
        self._chain = weakref.proxy(chain)
        self._fut = None
        self._next = None
        self._turn = None

    @property
    def turn(self):
        return self._turn

    @property
    def fut(self):
        return self._fut

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._chain.shift(self._next)


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
            key_list = list(gamblers.keys())
            order = key_list.index(addr)
            key_list = key_list[order:] + key_list[:order]
            od = OrderedDict()
            for key in key_list:
                od[key] = gamblers[key]
            self._next = GangPhase(self._chain, self.DECK[-3:], od, addr)
        else:
            log.error('Invalid room%s can not enter DrawPhase', self._chain.duel.view())
            raise DrawPhaseRuntimeError(generate_traceback())
        return self.till_i_die()

    async def till_i_die(self):
        await self._chain.duel.send({
            'name': '',
            'args': None,
            'kwargs': None
        })


class GangPhase(Phase):
    def __init__(self, chain, three, od, turn):
        super().__init__(chain)
        self._three = three
        self._turn = turn
        self._od = od

    def __enter__(self):
        return self.till_i_die()

    async def run_out(self, fut):
        await asyncio.sleep(10)
        if not fut.done():
            fut.set_result(None)

    async def till_i_die(self):
        fut = asyncio.get_event_loop().create_future()
        self._fut = fut
        task = asyncio.create_task(self.run_out(fut))
        choice = await fut
        if isinstance(choice, int):
            task.cancel()
        self._fut = None
        if choice:
            pass
