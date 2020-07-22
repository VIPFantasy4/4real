# -*- coding: utf-8 -*-

class Combo:
    @classmethod
    def whoami(cls):
        return cls

    @staticmethod
    def fromcards(cards: dict, owner):
        return MAPPING

    def __init__(self, owner):
        self._owner = owner

    @property
    def owner(self):
        return self._owner


class Single(Combo):
    pass


class Pair(Combo):
    pass


class Seq(Combo):
    pass


class PairSeq(Combo):
    pass


class Triple(Combo):
    pass


class TripleWithSingle(Triple):
    pass


class TripleWithPair(Triple):
    pass


class Plane(Combo):
    pass


class FakeBomb(Combo):
    pass


class RealBomb(Combo):
    pass


class JokerBomb(Combo):
    pass


class Pass(Combo):
    def __bool__(self):
        return False

    def __eq__(self, o: object) -> bool:
        return o is None


MAPPING = {
    1: (Single,),
    2: (Pair, JokerBomb),
    3: (Triple,),
    4: (TripleWithSingle, RealBomb),
    5: (TripleWithPair, Seq),
    6: (FakeBomb, PairSeq, Seq, Plane),
    7: (Seq,),
    8: (FakeBomb, PairSeq, Plane, Seq),
    9: (Seq, Plane),
    10: (PairSeq, Plane, Seq),
    11: (Seq,),
    12: (PairSeq, Plane, Seq,),
    13: (),
    14: (PairSeq,),
    15: (Plane,),
    16: (PairSeq, Plane),
    17: (),
    18: (PairSeq, Plane),
    19: (),
    20: (PairSeq, Plane)
}

hierarchy
