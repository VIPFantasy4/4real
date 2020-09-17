# -*- coding: utf-8 -*-

from .exceptions import *
import weakref
import log


class Chain:
    def regress(self):
        return self.phase and self.phase.regress(), self.times, self.three, self.track and tuple(
            combo.regress() for combo in self.track)

    def __init__(self, duel):
        self._duel = weakref.proxy(duel)
        self.phase = None
        self.times = None
        self.three = None
        self.track = None

    @property
    def duel(self):
        return self._duel

    def start_over(self, times):
        from .phase import DrawPhase
        self.phase = DrawPhase(self)
        self.times = times
        self.track = []

    async def duel_start(self):
        while self.phase:
            try:
                async with self.phase as till_i_die:
                    await till_i_die
            except (DrawPhaseRuntimeError,) as e:
                raise ChainRuntimeError(repr(e))

    async def bot(self, addr, bot):
        if self.bot.__name__ in self.duel.funcs:
            _id, status, gamblers = self.duel.view()
            if addr in gamblers:
                gambler = gamblers[addr]
                try:
                    if gambler.bot > 0:
                        if bot:
                            raise DuelRuntimeError
                        else:
                            gambler.bot = -1
                    elif bot:
                        gambler.bot = 1
                    else:
                        raise DuelRuntimeError
                    await self.duel.heartbeat()
                    if gambler.fut is not None:
                        if not gambler.fut.done():
                            if bot:
                                gambler.fut.set_result(None)
                            else:
                                gambler.fut.set_exception(HumanOperationResume)
                        gambler.fut = None
                except DuelRuntimeError:
                    log.info(
                        'A preventable request from addr: %s with bot: %s that attempts to set gambler.bot: %s is definitely redundant',
                        addr, bot, gambler.bot)
