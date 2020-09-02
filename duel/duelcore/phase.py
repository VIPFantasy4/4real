# -*- coding: utf-8 -*-

from collections import OrderedDict
from .combo import Combo
import log
import duelcore
import asyncio
import time
import random
import math


class Phase:
    def regress(self):
        return self.__class__.__name__, self.turn

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

    async def __aenter__(self):
        raise NotImplementedError

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._chain.phase = self._next


class DrawPhase(Phase):
    DECK = [(0, 0), (0, 1)] + [(i, j) for i in range(1, 14) for j in range(4)]

    async def __aenter__(self):
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
            self._next = GangPhase(self._chain, tuple(self.DECK[-3:]), od, addr)
            self._chain.duel.funcs[self.show_hand.__name__] = self.show_hand
            await self._chain.duel.heartbeat()
        else:
            log.error('Invalid room%s can not enter DrawPhase', self._chain.duel.view())
            raise duelcore.DrawPhaseRuntimeError(duelcore.generate_traceback())
        return self.till_i_die()

    async def till_i_die(self):
        await asyncio.sleep(duelcore.DP_LIFETIME)
        del self._chain.duel.funcs[self.show_hand.__name__]

    async def show_hand(self, addr):
        if self._chain.phase is self:
            _id, status, gamblers = self._chain.duel.view()
            if addr in gamblers:
                gambler = gamblers[addr]
                if not gambler.show_hand:
                    gambler.show_hand = True
                    self._chain.times *= 2
                    if not self.turn:
                        self._turn = addr
                        key_list = list(gamblers.keys())
                        order = key_list.index(addr)
                        key_list = key_list[order:] + key_list[:order]
                        od = OrderedDict()
                        for key in key_list:
                            od[key] = gamblers[key]
                            gamblers.move_to_end(key)
                        self._next._od = od
                        self._next._turn = addr
                    await self._chain.duel.heartbeat()


class GangPhase(Phase):
    def __init__(self, chain, three, od, turn):
        super().__init__(chain)
        self._three = three
        self._turn = turn
        self._od: OrderedDict = od

    async def __aenter__(self):
        self._chain.duel.funcs[self.choose.__name__] = self.choose
        await self._chain.duel.heartbeat()
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
        del self._chain.duel.funcs[self.choose.__name__]
        if choice:
            if self._chain.times < 0:
                self._chain.times = abs(self._chain.times)
            else:
                self._chain.times *= 2
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
                self._chain.times = abs(self._chain.times)
                _id, status, gamblers = self._chain.duel.view()
                og = random.choice(tuple(gamblers.values()))
            else:
                self._turn = key_list[0]
                self._next = GangPhase(self._chain, self._three, self._od, self.turn)
        if self._next is None:
            og.og = True
            og.deal(self._three)
            self._chain.three = self._three
            self._next = PlusPhase(self._chain)
            self._next._next = MainPhase(self._chain, og)
            self._next._turn = 0

    async def choose(self, addr, choice):
        if self.fut and not self.fut.done() and addr == self.turn and isinstance(choice, int) and choice in (0, 1):
            self.fut.set_result(choice)


class PlusPhase(Phase):
    async def __aenter__(self):
        self._chain.duel.funcs[self.times.__name__] = self.times
        await self._chain.duel.heartbeat()
        return self.till_i_die()

    async def run_out(self, fut):
        await asyncio.sleep(duelcore.PP_TIMEOUT)
        if not fut.done():
            fut.set_result(None)

    async def till_i_die(self):
        fut = asyncio.get_event_loop().create_future()
        self._fut = fut
        task = asyncio.create_task(self.run_out(fut))
        prior = await fut
        del self._chain.duel.funcs[self.times.__name__]
        if prior:
            task.cancel()
        self._chain.duel.funcs[self._next.show_hand.__name__] = self._next.show_hand

    async def times(self, addr, times):
        if self.fut and not self.fut.done() and times in (1, 2, 4):
            _id, status, gamblers = self._chain.duel.view()
            if addr in gamblers:
                gambler = gamblers[addr]
                if not gambler.times:
                    gambler.times = times
                    if times != 1:
                        self._chain.times *= times
                    self._turn += 1
                    if self.turn == 3:
                        self.fut.set_result(True)
                    await self._chain.duel.heartbeat()


class MainPhase(Phase):
    def __init__(self, chain, od, turn=None):
        super().__init__(chain)
        if not isinstance(od, OrderedDict):
            turn = od.addr
            print(turn, 'og')
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

    async def __aenter__(self):
        self._chain.duel.funcs[self.play.__name__] = self.play
        await self._chain.duel.heartbeat()
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
        self._chain.duel.funcs.pop(self.show_hand.__name__, None)
        del self._chain.duel.funcs[self.play.__name__]
        gambler = self._od[self.turn]
        if isinstance(combo, duelcore.Combo):
            task.cancel()
            times = combo.times
            if times:
                self._chain.times *= times
            self._track.append(combo)
        else:
            gambler.auto(self._track)
        if gambler.gg:
            print(f'this dude: {gambler.addr} win')
            await self._chain.duel.heartbeat()
        else:
            self._od.move_to_end(self.turn)
            self._turn = next(iter(self._od.keys()))
            self._next = MainPhase(self._chain, self._od, self._turn)

    async def show_hand(self, addr):
        if self.show_hand.__name__ in self._chain.duel.funcs and addr == self.turn:
            gambler = self._od[addr]
            if not gambler.show_hand:
                gambler.show_hand = True
                self._chain.times *= 2
            await self._chain.duel.heartbeat()

    async def play(self, addr, cards):
        if self.fut and not self.fut.done() and addr == self.turn and isinstance(cards, dict):
            gambler = self._od[addr]
            try:
                gambler.scan(cards)
                first, second = self._track[-2:] + [None for _ in range(2 - len(self._track))]
                last = second if second else first
                combo = Combo.fromcards(cards, gambler)
                if combo is not None:
                    if (not combo or combo > last) if last else combo:
                        gambler.play(cards)
                        self.fut.set_result(combo)
                        return
                log.info(
                    'A preventable request from addr: %s with combo: %s against the last: %s is definitely negated',
                    addr, combo, last)
            except duelcore.InconsistentDataError as e:
                log.error('Exception occurred in play by request argument cards: %s from addr: %s', cards, addr)
                log.error('%s: %s', e.__class__.__name__, e)
