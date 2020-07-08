# -*- coding: utf-8 -*-

from .exceptions import *
from .phase import DrawPhase
import weakref


class Chain:
    def __init__(self, duel):
        self._duel = weakref.proxy(duel)
        self._phase = None

    @property
    def duel(self):
        return self._duel

    def start_over(self):
        self._phase = DrawPhase(self)

    def shift(self, phase):
        self._phase = phase

    async def duel_start(self):
        while self._phase:
            try:
                with self._phase as till_i_die:
                    await till_i_die
            except (DrawPhaseRuntimeError,):
                raise
