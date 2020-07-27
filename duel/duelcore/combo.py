# -*- coding: utf-8 -*-

class Combo:
    @classmethod
    def whoami(cls):
        return cls

    @staticmethod
    def fromcards(cards: dict, owner):
        if not cards:
            return Pass(owner)
        overview = {
            'qty': 0,
            'max': None,
            'min': None,
            'map': {}
        }
        for k, v in cards.items():
            qty = len(v)
            if qty:
                if not overview['qty']:
                    overview['max'] = k
                    overview['min'] = k
                elif k < overview['max']:
                    overview['max'] = k
                elif k > overview['min']:
                    overview['min'] = k
                overview['map'].setdefault(qty, []).append(k)
                overview['qty'] += qty
        adaptors = MAPPING.get(overview['qty'])
        for adaptor in adaptors:
            args = adaptor.validate(overview, cards)
            if args is not None:
                return adaptor(owner, *args)

    def __init__(self, owner):
        self._owner = owner

    def __gt__(self, other):
        if isinstance(other, self.whoami()) and self.v < other.v:
            return True
        return False

    @property
    def owner(self):
        return self._owner


class Single(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        if overview['qty'] == 1:
            return (overview['max'], cards[overview['min']][0]),

    def __init__(self, owner, card):
        super().__init__(owner)
        self.card: tuple = card

    def __gt__(self, other):
        if isinstance(other, Single):
            if not self.card[0] and not other.card[0]:
                if not self.card[1]:
                    return True
            elif self.card[0] < other.card[0]:
                return True
        return False


class Pair(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        if overview['qty'] == 2 and 2 in overview['map'] and overview['map'][2][0]:
            return overview['max'],

    def __init__(self, owner, v):
        super().__init__(owner)
        self.v: int = v


class Seq(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        if overview['qty'] > 4 and overview['max'] > 1 and 1 in overview['map'] and len(overview['map']) == 1 and list(range(overview['max'], overview['min'] + 1)) == sorted(overview['map'][1]):
            return overview['qty'], overview['max']

    def __init__(self, owner, qty, v):
        super().__init__(owner)
        self.qty: int = qty
        self.v: int = v

    def __gt__(self, other):
        if isinstance(other, self.whoami()) and self.qty == other.qty and self.v < other.v:
            return True
        return False


class PairSeq(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        if overview['qty'] > 5 and overview['max'] > 1 and 2 in overview['map'] and len(overview['map']) == 1 and list(range(overview['max'], overview['min'] + 1)) == sorted(overview['map'][2]):
            return overview['qty'], overview['max']

    def __init__(self, owner, qty, v):
        super().__init__(owner)
        self.qty: int = qty
        self.v: int = v

    def __gt__(self, other):
        if isinstance(other, self.whoami()) and self.qty == other.qty and self.v < other.v:
            return True
        return False


class Triple(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        if overview['qty'] == 3 and 3 in overview['map']:
            return overview['max'],

    def __init__(self, owner, v):
        super().__init__(owner)
        self.v: int = v


class TripleWithSingle(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        if overview['qty'] == 4 and 3 in overview['map']:
            return overview['map'][3][0],

    def __init__(self, owner, v):
        super().__init__(owner)
        self.v: int = v


class TripleWithPair(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        if overview['qty'] == 5 and 3 in overview['map'] and 2 in overview['map']:
            return overview['map'][3][0],

    def __init__(self, owner, v):
        super().__init__(owner)
        self.v: int = v


class Plane(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        if 3 in overview['map']:
            if 4 in overview['map']:
            else:
                seq = sorted(overview['map'][3])
                count = len(seq)
                if count > 1:
                    if 1 in seq:
                        if count > 3 and list(range(seq[0] + 1, seq[-1] + 1)) == seq[1:]:
                            if count == 4:
                                specified
                                pass
                            elif count == 4 + len(overview['map'].get(1, ())) + 2 * len(overview['map'].get(2, ())):
                                return count - 1, overview['qty'], seq[1]
                    elif count == 2:
                        if 1 in overview['map']:
                            if len(overview['map'][1]) == 2:
                                return count, overview['qty'], seq[0]
                        elif 2 * len(overview['map'].get(2, ())) in (0, 2, 4):
                            return count, overview['qty'], seq[0]
        elif 4 in overview['map']:

    def __init__(self, owner, count, qty, v):
        super().__init__(owner)
        self.count: int = count
        self.qty: int = qty
        self.v: int = v

    def __gt__(self, other):
        if isinstance(other, self.whoami()) and self.qty == other.qty and self.v < other.v:
            return True
        return False


class FakeBomb(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        if 4 in overview['map']:
            if overview['qty'] == 6:
                if 1 in overview['map']:
                    if len(overview['map'][1]) == 2:
                        return overview['qty'], overview['map'][4][0]
                elif 2 in overview['map'] and len(overview['map'][2]) == 1:
                    return overview['qty'], overview['map'][4][0]
            elif overview['qty'] == 8:
                if 2 in overview['map']:
                    if len(overview['map'][2]) == 2:
                        return overview['qty'], overview['map'][4][0]
                elif len(overview['map'][4]) == 2:
                    return overview['qty'], overview['max']

    def __init__(self, owner, qty, v):
        super().__init__(owner)
        self.qty: int = qty
        self.v: int = v

    def __gt__(self, other):
        if isinstance(other, self.whoami()) and self.qty == other.qty and self.v < other.v:
            return True
        return False


class RealBomb(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        if overview['qty'] == 4 and 4 in overview['map']:
            return overview['max'],

    def __init__(self, owner, v):
        super().__init__(owner)
        self.v: int = v

    def __gt__(self, other):
        if isinstance(other, RealBomb) and self.v > other.v:
            return False
        if isinstance(other, JokerBomb):
            return False
        return True


class JokerBomb(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        if overview['qty'] == 2 and 2 in overview['map'] and not overview['map'][2][0]:
            return ()

    def __gt__(self, other):
        return True


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
