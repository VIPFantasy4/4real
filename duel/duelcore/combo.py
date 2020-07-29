# -*- coding: utf-8 -*-

class Combo:
    @classmethod
    def whoami(cls):
        return cls

    @staticmethod
    def fromcards(cards: dict, owner):
        if not cards:
            return Pass(owner, None)
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

    def __init__(self, owner, view):
        self._owner = owner
        self._view = view

    @property
    def owner(self):
        return self._owner

    @property
    def view(self):
        return self._view


class Single(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        if overview['qty'] == 1:
            card = next(iter(cards[overview['max']]))
            return [card], card

    def __init__(self, owner, view, card):
        super().__init__(owner, view)
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
            return sorted(cards[overview['max']]), overview['max']

    def __init__(self, owner, view, v):
        super().__init__(owner, view)
        self.v: int = v

    def __gt__(self, other):
        if isinstance(other, self.whoami()) and self.v < other.v:
            return True
        return False


class Seq(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        seq = sorted(overview['map'][1])
        if overview['qty'] > 4 and overview['max'] > 1 and 1 in overview['map'] and len(overview['map']) == 1 and list(range(overview['max'], overview['min'] + 1)) == seq:
            return [next(iter(cards[k])) for k in seq], overview['qty'], overview['max']

    def __init__(self, owner, view, qty, v):
        super().__init__(owner, view)
        self.qty: int = qty
        self.v: int = v

    def __gt__(self, other):
        if isinstance(other, self.whoami()) and self.qty == other.qty and self.v < other.v:
            return True
        return False


class PairSeq(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        seq = sorted(overview['map'][2])
        if overview['qty'] > 5 and overview['max'] > 1 and 2 in overview['map'] and len(overview['map']) == 1 and list(range(overview['max'], overview['min'] + 1)) == seq:
            view = []
            for k in seq:
                view.extend(sorted(cards[k]))
            return view, overview['qty'], overview['max']

    def __init__(self, owner, view, qty, v):
        super().__init__(owner, view)
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
            return sorted(cards[overview['max']]), overview['max']

    def __init__(self, owner, view, v):
        super().__init__(owner, view)
        self.v: int = v

    def __gt__(self, other):
        if isinstance(other, self.whoami()) and self.v < other.v:
            return True
        return False


class TripleWithSingle(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        if overview['qty'] == 4 and 3 in overview['map']:
            view = sorted(cards[overview['map'][3][0]])
            view.extend([next(iter(cards[overview['map'][1][0]]))])
            return view, overview['map'][3][0]

    def __init__(self, owner, view, v):
        super().__init__(owner, view)
        self.v: int = v

    def __gt__(self, other):
        if isinstance(other, self.whoami()) and self.v < other.v:
            return True
        return False


class TripleWithPair(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        if overview['qty'] == 5 and 3 in overview['map'] and 2 in overview['map']:
            view = sorted(cards[overview['map'][3][0]])
            view.extend(sorted(cards[overview['map'][2][0]]))
            return view, overview['map'][3][0]

    def __init__(self, owner, view, v):
        super().__init__(owner, view)
        self.v: int = v

    def __gt__(self, other):
        if isinstance(other, self.whoami()) and self.v < other.v:
            return True
        return False


class Plane(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        if 3 in overview['map']:
            if 4 in overview['map']:
                if overview['qty'] == 8:
                    if abs(overview['map'][3][0] - overview['map'][4][0]) == 1:
                        v = min(overview['map'][3][0], overview['map'][4][0])
                        if v > 1:
                            return 2, 8, v
                elif overview['qty'] == 10:
                    seq = sorted(overview['map'][3])
                    if len(seq) == 2 and seq[0] > 1 and seq[0] + 1 == seq[1]:
                        return 2, 10, seq[0]
                elif overview['qty'] == 12:
                    seq = sorted(overview['map'][3] + overview['map'][4])
                    if seq[0] > 1 and len(seq) == 3 and list(range(seq[0], seq[-1] + 1)) == seq:
                        return 3, 12, seq[0]
                elif overview['qty'] == 15:
                    seq = sorted(overview['map'][3])
                    if seq[0] > 1 and len(seq) == 3 and list(range(seq[0], seq[-1] + 1)) == seq and 2 in overview['map']:
                        return 3, 15, seq[0]
                elif overview['qty'] == 16:
                    seq = sorted(overview['map'][3] + overview['map'][4])
                    count = len(seq)
                    if count == 4:
                        if seq[0] > 1 and list(range(seq[0], seq[-1] + 1)) == seq:
                            return 4, 16, seq[0]
                    elif count == 5 and list(range(seq[1], seq[-2] + 1)) == seq[1:-1]:
                        if seq[0] > 1 and seq[0] + 1 == seq[1]:
                            return 4, 16, seq[0]
                        elif seq[-1] - 1 == seq[-2]:
                            return 4, 16, seq[1]
                elif overview['qty'] == 20:
                    seq = sorted(overview['map'][3] + overview['map'][4])
                    count = len(seq)
                    if count == 5:
                        if list(range(seq[1], seq[-2] + 1)) == seq[1:-1]:
                            if seq[0] > 1 and seq[0] + 1 == seq[1]:
                                if seq[-1] - 1 == seq[-2]:
                                    return 5, 20, seq[0]
                                elif 1 not in overview['map'] and seq[:-1] == sorted(overview['map'][3]):
                                    return 4, 20, seq[0]
                            elif 1 not in overview['map'] and seq[-1] - 1 == seq[-2] and seq[1:] == sorted(overview['map'][3]):
                                return 4, 20, seq[0]
                    elif count == 6 and seq[2] + 1 == seq[3]:
                        left = 2
                        right = 4
                        while right < count:
                            if seq[right - 1] + 1 == seq[right]:
                                right += 1
                                continue
                            break
                        while left:
                            if seq[left - 1] + 1 == seq[left]:
                                left -= 1
                                continue
                            break
                        if not left and seq[0] == 1:
                            left = 1
                        count = right - left
                        if count > 4:
                            return 5, 20, seq[1]
                        elif count == 4 and 1 not in overview['map'] and seq[left:right] == sorted(overview['map'][3]):
                            return 4, 20, seq[left]
            else:
                seq = sorted(overview['map'][3])
                count = len(seq)
                if count > 1:
                    if seq[0] == 1:
                        if count > 3 and list(range(seq[1], seq[-1] + 1)) == seq[1:]:
                            if count == 4:
                                return count - 1, overview['qty'], seq[1]
                            elif count == 4 + len(overview['map'].get(1, ())) + 2 * len(overview['map'].get(2, ())):
                                return count - 1, overview['qty'], seq[1]
                    elif count in (2, 3):
                        if list(range(seq[0], seq[-1] + 1)) == seq:
                            if 1 in overview['map']:
                                if len(overview['map'][1]) + 2 * len(overview['map'].get(2, ())) == count:
                                    return count, overview['qty'], seq[0]
                            elif 2 * len(overview['map'].get(2, ())) in (0, count, 2 * count):
                                return count, overview['qty'], seq[0]
                    elif 1 in overview['map']:
                        least = len(overview['map'][1]) + 2 * len(overview['map'].get(2, ()))
                        if count == least:
                            if list(range(seq[0], seq[-1] + 1)) == seq:
                                return count, overview['qty'], seq[0]
                        elif least < 3 and count == least + 4 and list(range(seq[1], seq[-2] + 1)) == seq[1:-1]:
                            if seq[0] + 1 == seq[1]:
                                return count - 1, overview['qty'], seq[0]
                            elif seq[-1] - 1 == seq[-2]:
                                return count - 1, overview['qty'], seq[1]
                    elif 2 in overview['map']:
                        least = len(overview['map'][2])
                        if least > 1:
                            if list(range(seq[0], seq[-1] + 1)) == seq:
                                if count in (least, 2 * least):
                                    return count, overview['qty'], seq[0]
                        elif count == 6 and list(range(seq[1], seq[-2] + 1)) == seq[1:-1]:
                            if seq[0] + 1 == seq[1]:
                                return count - 1, overview['qty'], seq[0]
                            elif seq[-1] - 1 == seq[-2]:
                                return count - 1, overview['qty'], seq[1]
                    elif list(range(seq[1], seq[-2] + 1)) == seq[1:-1]:
                        if seq[0] + 1 == seq[1]:
                            if seq[-1] - 1 == seq[-2]:
                                if count == 4:
                                    # can be specified
                                    pass
                                return count, overview['qty'], seq[0]
                            elif count == 4:
                                return count - 1, overview['qty'], seq[0]
                        elif count == 4 and seq[-1] - 1 == seq[-2]:
                            return count - 1, overview['qty'], seq[1]
        elif 4 in overview['map'] and len(overview['map']) == 1 and 1 not in overview['map'][4]:
            seq = sorted(overview['map'][4])
            if list(range(seq[0], seq[-1] + 1)) == seq:
                return len(seq), overview['qty'], seq[0]

    def __init__(self, owner, view, count, qty, v):
        super().__init__(owner, view)
        self.count: int = count
        self.qty: int = qty
        self.v: int = v

    def __gt__(self, other):
        if isinstance(other, self.whoami()) and self.count == other.count and self.qty == other.qty and self.v < other.v:
            return True
        return False


class FakeBomb(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        if 4 in overview['map']:
            if overview['qty'] == 6:
                if 1 in overview['map']:
                    if len(overview['map'][1]) == 2:
                        view = sorted(cards[overview['map'][4][0]])
                        view.extend(sorted(next(iter(cards[k])) for k in overview['map'][1]))
                        return view, overview['qty'], overview['map'][4][0]
                elif 2 in overview['map'] and len(overview['map'][2]) == 1:
                    view = sorted(cards[overview['map'][4][0]])
                    view.extend(sorted(cards[overview['map'][2][0]]))
                    return view, overview['qty'], overview['map'][4][0]
            elif overview['qty'] == 8:
                if 2 in overview['map']:
                    if len(overview['map'][2]) == 2:
                        view = sorted(cards[overview['map'][4][0]])
                        for k in sorted(overview['map'][2]):
                            view.extend(sorted(cards[k]))
                        return view, overview['qty'], overview['map'][4][0]
                elif len(overview['map'][4]) == 2:
                    # can be specified
                    view = sorted(cards[overview['max']])
                    view.extend(sorted(cards[overview['min']]))
                    return view, overview['qty'], overview['max']

    def __init__(self, owner, view, qty, v):
        super().__init__(owner, view)
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
            return sorted(cards[overview['max']]), overview['max']

    def __init__(self, owner, view, v):
        super().__init__(owner, view)
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
            return [(0, 0), (0, 1)],

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
