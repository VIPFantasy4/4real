# -*- coding: utf-8 -*-

class Combo:
    @staticmethod
    def fromcards(cards: dict):
        return


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
