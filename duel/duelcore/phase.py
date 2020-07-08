# -*- coding: utf-8 -*-

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
        self._next_phase = None
        self._turn = None
        self._next_turn = None

    @property
    def turn(self):
        return self._turn

    def __next__(self):
        raise NotImplementedError

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._chain.shift(self._next_phase)

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
            self._first = self._turn = addr
            key_list = list(gamblers.keys())
            self._next_turn = key_list[(key_list.index(self.turn) + 1) % 3]
            self._three = self.DECK[-3:]
        else:
            log.error('Invalid room%s can not enter DrawPhase', self._chain.duel.view())
            raise DrawPhaseRuntimeError(generate_traceback())
        return self.till_i_die()

    async def run_out(self, fut):
        await asyncio.sleep(10)
        if not fut.done():
            fut.set_result(None)

    async def till_i_die(self):
        await self._chain.duel.send({
            'name': '',
            'args': None,
            'kwargs': None
        })
        fut = asyncio.get_event_loop().create_future()
        self._fut = fut
        task = asyncio.create_task(self.run_out(fut))
        choice = await fut
        if isinstance(choice, int):
            task.cancel()
        self._fut = None
        _id, status, gamblers = self._chain.duel.view()
        if choice:
            gamblers[self.turn].role += 1
        _sum = sum(gambler.role for gambler in gamblers.values())
        if self._next_turn:
            key_list = list(gamblers.keys())
            next_turn = key_list[(key_list.index(self.turn) + 1) % 3]
            if next_turn is not self._first:
                self._turn = self._next_turn
                self._next_turn = key_list[(key_list.index(self._next_turn) + 1) % 3]
            else:
                self._next_turn = None
                if _sum:
                    if gamblers[self._first].role:
                        self._turn = self._first
                    else:
                        next_turn = key_list[(key_list.index(self._first) + 1) % 3]
                        if _sum > 2:
                            self._turn = next_turn
                        elif gamblers[next_turn].role:
                            next_turn
                        else:
                            self.turn
                else:
                    pass
        else:
