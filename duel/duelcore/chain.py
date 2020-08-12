# -*- coding: utf-8 -*-

from .exceptions import *
import weakref


class Chain:
    def __reduce__(self):
        return tuple, ((self.phase, self.times, self.three, self.track),)

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
                with self.phase as till_i_die:
                    await till_i_die
            except (DrawPhaseRuntimeError,) as e:
                raise ChainRuntimeError(repr(e))
