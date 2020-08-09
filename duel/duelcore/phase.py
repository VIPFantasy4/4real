# -*- coding: utf-8 -*-

from collections import OrderedDict
import log
import duelcore
import asyncio
import time
import weakref
import random
import math


class Phase:
    def __reduce__(self):
        return tuple, ((self.__class__.__name__, self.turn),)

    def __init__(self, chain):
        self._chain = chain
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
        self._chain.phase = self._next


class DrawPhase(Phase):
    DECK = [(0, 0), (0, 1)] + [(i, j) for i in range(1, 14) for j in range(4)]

    def __reduce__(self):
        return self._next.__reduce__()

    def __enter__(self):
        if self._chain.duel.validate():
            _id, status, gamblers = self._chain.duel.view()
            random.shuffle(self.DECK)
            once = random.randint(*duelcore.DP_CLOSED_INTERVAL)
            t = int(math.ceil(17 / once))
            triple = [{} for _ in range(3)]
            for i in range(t):
                n = once * 3 * i
                if t - 1 == i:
                    once = 17 - once * i
                for j in range(n, n + once):
                    for i in range(3):
                        card = self.DECK[j + once * i]
                        triple[i].setdefault(card[0], set()).add(card)
            for addr, gambler in random.sample(gamblers.items(), 3):
                gambler.deal(triple.pop())
            key_list = list(gamblers.keys())
            order = key_list.index(addr)
            key_list = key_list[order:] + key_list[:order]
            od = OrderedDict()
            for key in key_list:
                od[key] = gamblers[key]
                gamblers.move_to_end(key)
            self._next = GangPhase(self._chain, self.DECK[-3:], od, addr)
        else:
            log.error('Invalid room%s can not enter DrawPhase', self._chain.duel.view())
            raise duelcore.DrawPhaseRuntimeError(duelcore.generate_traceback())
        return self.till_i_die()

    async def till_i_die(self):
        await self._chain.duel.heartbeat()


class GangPhase(Phase):
    def __init__(self, chain, three, od, turn):
        super().__init__(chain)
        self._three = three
        self._turn = turn
        self._od: OrderedDict = od

    def __enter__(self):
        return self.till_i_die()

    async def run_out(self, fut):
        await asyncio.sleep(duelcore.GP_TIMEOUT)
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
            gambler = self._od[self.turn]
            gambler.role += 1
            if len(self._od) == 1 or gambler.role > 1:
                og = gambler
            else:
                self._od.move_to_end(self.turn)
                self._turn = next(iter(self._od.keys()))
                self._next = GangPhase(self._chain, self._three, self._od, self.turn)
        else:
            gambler = self._od.pop(self.turn)
            key_list = list(self._od.keys())
            if gambler.role:
                og = self._od[key_list[-1]]
            elif not key_list:
                _id, status, gamblers = self._chain.duel.view()
                og = random.choice(tuple(gamblers.values()))
            else:
                self._turn = key_list[0]
                self._next = GangPhase(self._chain, self._three, self._od, self.turn)
        if self._next is None:
            og.og = True
            og.deal(self._three)
            self._chain.three = self._three
            self._next = MainPhase(self._chain, og)
        await self._chain.duel.heartbeat()


class MainPhase(Phase):
    def __init__(self, chain, od, turn=None):
        super().__init__(chain)
        if not isinstance(od, OrderedDict):
            turn = od.addr
            _id, status, gamblers = self._chain.duel.view()
            key_list = list(gamblers.keys())
            order = key_list.index(turn)
            key_list = key_list[order:] + key_list[:order]
            od = OrderedDict()
            for key in key_list:
                od[key] = gamblers[key]
        self._turn = turn
        self._od: OrderedDict = od
        self._track = self._chain.track

    def __enter__(self):
        return self.till_i_die()

    async def run_out(self, fut, delay):
        await asyncio.sleep(self._od[self.turn].bot > 0 and duelcore.BOT_DELAY or duelcore.MP_TIMEOUT - delay)
        if not fut.done():
            self._od[self.turn].bot += 1
            fut.set_result(None)

    async def till_i_die(self, started_at=0):
        fut = asyncio.get_event_loop().create_future()
        self._fut = fut
        resumed_at = int(time.monotonic())
        task = asyncio.create_task(self.run_out(fut, started_at and resumed_at - started_at))
        try:
            combo = await fut
        except duelcore.HumanOperationResume:
            task.cancel()
            await self.till_i_die(resumed_at)
            return
        self._fut = None
        gambler = self._od[self.turn]
        if isinstance(combo, duelcore.Combo):
            task.cancel()
            self._track.append(combo)
        else:
            gambler.auto(self._track)
        if gambler.gg:
            pass
        else:
            self._od.move_to_end(self.turn)
            self._turn = next(iter(self._od.keys()))
            self._next = MainPhase(self._chain, self._od, self._turn)
            await self._chain.duel.heartbeat()
