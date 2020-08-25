# -*- coding: utf-8 -*-

from .combo import Combo
from .exceptions import InconsistentDataError
import weakref


class Gambler:
    def regress(self):
        return self.addr, self._cards and {
            k: tuple(s) for k, s in self._cards.items()}, self.show_hand, self.role, self.og, self.bot

    def __init__(self, duel, addr):
        self.addr = addr
        self._duel = weakref.proxy(duel)
        self._cards = None
        self.show_hand = False
        self.role = 0
        self.og = False
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
                raise InconsistentDataError(f'forgery or stale cards: {cards} from addr: {self.addr} can not match self._cards: {self._cards}')
        if cards is self._cards:
            self._cards = {}
            return
        for k in cards:
            self._cards[k].difference_update(cards[k])
            if not self._cards[k]:
                del self._cards[k]

    def auto(self, track):
        first, second = track[-2:] + [None for _ in range(2 - len(track))]
        last = second if second else first
        cards = self._cards
        combo = Combo.fromcards(cards, self)
        if last:
            if combo is not None and combo > last:
                pass
            elif self.og or last.owner.og:
                combo, cards = Combo.autodetect(cards, self, last)
            else:
                # AI
                cards = {}
                combo = last.fromcards(cards, self)
        elif combo is None:
            combo, cards = Combo.autodetect(cards, self)
        if combo:
            self.play(cards)
        times = combo.times
        if times:
            self._duel._chain.times *= times
        track.append(combo)
