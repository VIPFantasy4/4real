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

    @staticmethod
    def autodetect(cards, owner, combo=None):
        if not cards:
            return Pass(owner, None), None
        if combo is None:
            return
        return combo.detect(cards, owner)

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

    def detect(self, cards: dict, owner) -> tuple:
        real = None
        right = self.card[0] - 1
        if self.card[0]:
            left = min(cards)
            for v in range(right, left - 1, -1):
                if v in cards:
                    if len(cards[v]) == 4:
                        if not real:
                            real = v
                        continue
                    card = next(iter(cards[v]))
                    return self.whoami()(owner, [card], card), {v: {card}}
        elif self.card[1] and 0 in cards:
            card = (0, 0)
            return self.whoami()(owner, [card], card), {0: {card}}
        for v in range(max(cards), right, -1):
            if v in cards and len(cards) == 4:
                real = v
                break
        if real:
            return RealBomb(owner, [(real, j) for j in range(4)], real), {real: cards[real]}
        return Pass(owner, None), None


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

    def detect(self, cards: dict, owner) -> tuple:
        real = None
        right = self.v - 1
        left = min(cards)
        fallback = {}
        for v in range(right, max(left - 1, 0), -1):
            if v in cards:
                qty = len(cards[v])
                if qty == 4:
                    if not real:
                        real = v
                    continue
                if qty > 1:
                    if qty == 2:
                        return self.whoami()(owner, sorted(cards[v]), v), {v: cards[v]}
                    if qty not in fallback:
                        fallback[qty] = v
        if 3 in fallback:
            v = fallback[3]
            iterator = iter(cards[v])
            s = {next(iterator) for _ in range(2)}
            return self.whoami()(owner, sorted(s), v), {v: s}
        for v in range(max(cards), right, -1):
            if v in cards and len(cards) == 4:
                real = v
                break
        if real:
            return RealBomb(owner, [(real, j) for j in range(4)], real), {real: cards[real]}
        if 0 in cards and len(cards[0]) == 2:
            return JokerBomb(owner, [(0, 0), (0, 1)]), {0: cards[0]}
        return Pass(owner, None), None


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

    def detect(self, cards: dict, owner) -> tuple:
        v = self.v - 1
        while v > 1:
            view = []
            for i in range(v, v + self.qty):
                if i in cards:
                    view.append(next(iter(cards[i])))
                    continue
                break
            else:
                return self.whoami()(owner, view, v), {card[0]: {card} for card in view}
            v -= self.qty - len(view)
        for v in range(max(cards), max(min(cards) - 1, 0), -1):
            if v in cards and len(cards) == 4:
                return RealBomb(owner, [(v, j) for j in range(4)], v), {v: cards[v]}
        if 0 in cards and len(cards[0]) == 2:
            return JokerBomb(owner, [(0, 0), (0, 1)]), {0: cards[0]}
        return Pass(owner, None), None


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

    def detect(self, cards: dict, owner) -> tuple:
        count = self.qty // 2
        v = self.v - 1
        while v > 1:
            view = []
            for i in range(v, v + count):
                if i in cards and len(cards[i]) > 1:
                    iterator = iter(cards[i])
                    view.extend(next(iterator) for _ in range(2))
                    continue
                break
            else:
                return self.whoami()(owner, view, v), {view[i][0]: {view[i], view[i + 1]} for i in range(0, self.qty, 2)}
            v -= count - len(view)
        for v in range(max(cards), max(min(cards) - 1, 0), -1):
            if v in cards and len(cards) == 4:
                return RealBomb(owner, [(v, j) for j in range(4)], v), {v: cards[v]}
        if 0 in cards and len(cards[0]) == 2:
            return JokerBomb(owner, [(0, 0), (0, 1)]), {0: cards[0]}
        return Pass(owner, None), None


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

    def detect(self, cards: dict, owner) -> tuple:
        real = None
        right = self.v - 1
        left = min(cards)
        for v in range(right, max(left - 1, 0), -1):
            if v in cards:
                qty = len(cards[v])
                if qty == 4:
                    if not real:
                        real = v
                    continue
                if qty == 3:
                    return self.whoami()(owner, sorted(cards[v]), v), {v: cards[v]}
        for v in range(max(cards), right, -1):
            if v in cards and len(cards) == 4:
                real = v
                break
        if real:
            return RealBomb(owner, [(real, j) for j in range(4)], real), {real: cards[real]}
        if 0 in cards and len(cards[0]) == 2:
            return JokerBomb(owner, [(0, 0), (0, 1)]), {0: cards[0]}
        return Pass(owner, None), None


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

    def detect(self, cards: dict, owner) -> tuple:
        real = None
        right = self.v - 1
        left = min(cards)
        for v in range(right, max(left - 1, 0), -1):
            if v in cards:
                qty = len(cards[v])
                if qty == 4:
                    if not real:
                        real = v
                    continue
                if qty == 3:
                    view = sorted(cards[v])
                    fallback = {}
                    for k in range(max(cards), left - 1, -1):
                        if k != v and k in cards:
                            qty = len(cards[k])
                            if qty == 1:
                                view.extend(cards[k])
                                return self.whoami()(owner, view, v), {v: cards[v], k: cards[k]}
                            if qty not in fallback:
                                fallback[qty] = k
                    k = None
                    if 2 in fallback and fallback[2]:
                        k = fallback[2]
                    elif 3 in fallback:
                        k = fallback[3]
                    if k:
                        card = next(iter(cards[k]))
                        view.append(card)
                        return self.whoami()(owner, view, v), {v: cards[v], k: {card}}
                    if 4 in fallback:
                        k = fallback[4]
                        return RealBomb(owner, [(k, j) for j in range(4)], k), {k: cards[k]}
                    return JokerBomb(owner, [(0, 0), (0, 1)]), {0: cards[0]}
        for v in range(max(cards), right, -1):
            if v in cards and len(cards) == 4:
                real = v
                break
        if real:
            return RealBomb(owner, [(real, j) for j in range(4)], real), {real: cards[real]}
        if 0 in cards and len(cards[0]) == 2:
            return JokerBomb(owner, [(0, 0), (0, 1)]), {0: cards[0]}
        return Pass(owner, None), None


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

    def detect(self, cards: dict, owner) -> tuple:
        real = None
        right = self.v - 1
        left = min(cards)
        for v in range(right, max(left - 1, 0), -1):
            if v in cards:
                qty = len(cards[v])
                if qty == 4:
                    if not real:
                        real = v
                    continue
                if qty == 3:
                    view = sorted(cards[v])
                    fallback = {}
                    for k in range(max(cards), left - 1, -1):
                        if k != v and k in cards:
                            qty = len(cards[k])
                            if qty > 1:
                                if qty == 2:
                                    if k:
                                        view.extend(cards[k])
                                        return self.whoami()(owner, view, v), {v: cards[v], k: cards[k]}
                                elif qty not in fallback:
                                    fallback[qty] = k
                    if 3 in fallback:
                        k = fallback[3]
                        iterator = iter(cards[k])
                        s = {next(iterator) for _ in range(2)}
                        view.append(s)
                        return self.whoami()(owner, view, v), {v: cards[v], k: s}
                    if 4 in fallback:
                        k = fallback[4]
                        return RealBomb(owner, [(k, j) for j in range(4)], k), {k: cards[k]}
                    return JokerBomb(owner, [(0, 0), (0, 1)]), {0: cards[0]}
        for v in range(max(cards), right, -1):
            if v in cards and len(cards) == 4:
                real = v
                break
        if real:
            return RealBomb(owner, [(real, j) for j in range(4)], real), {real: cards[real]}
        if 0 in cards and len(cards[0]) == 2:
            return JokerBomb(owner, [(0, 0), (0, 1)]), {0: cards[0]}
        return Pass(owner, None), None


class Plane(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        args = None

        if 3 in overview['map']:
            if 4 in overview['map']:
                if overview['qty'] == 8:
                    if abs(overview['map'][3][0] - overview['map'][4][0]) == 1:
                        v = min(overview['map'][3][0], overview['map'][4][0])
                        if v > 1:
                            args = 2, 8, v
                elif overview['qty'] == 10:
                    seq = sorted(overview['map'][3])
                    if len(seq) == 2 and seq[0] > 1 and seq[0] + 1 == seq[1]:
                        args = 2, 10, seq[0]
                elif overview['qty'] == 12:
                    seq = sorted(overview['map'][3] + overview['map'][4])
                    if seq[0] > 1 and len(seq) == 3 and list(range(seq[0], seq[-1] + 1)) == seq:
                        args = 3, 12, seq[0]
                elif overview['qty'] == 15:
                    seq = sorted(overview['map'][3])
                    if seq[0] > 1 and len(seq) == 3 and list(range(seq[0], seq[-1] + 1)) == seq and 2 in overview['map']:
                        args = 3, 15, seq[0]
                elif overview['qty'] == 16:
                    seq = sorted(overview['map'][3] + overview['map'][4])
                    count = len(seq)
                    if count == 4:
                        if seq[0] > 1 and list(range(seq[0], seq[-1] + 1)) == seq:
                            args = 4, 16, seq[0]
                    elif count == 5 and list(range(seq[1], seq[-2] + 1)) == seq[1:-1]:
                        if seq[0] > 1 and seq[0] + 1 == seq[1]:
                            args = 4, 16, seq[0]
                        elif seq[-1] - 1 == seq[-2]:
                            args = 4, 16, seq[1]
                elif overview['qty'] == 20:
                    seq = sorted(overview['map'][3] + overview['map'][4])
                    count = len(seq)
                    if count == 5:
                        if list(range(seq[1], seq[-2] + 1)) == seq[1:-1]:
                            if seq[0] > 1 and seq[0] + 1 == seq[1]:
                                if seq[-1] - 1 == seq[-2]:
                                    args = 5, 20, seq[0]
                                elif 1 not in overview['map'] and seq[:-1] == sorted(overview['map'][3]):
                                    args = 4, 20, seq[0]
                            elif 1 not in overview['map'] and seq[-1] - 1 == seq[-2] and seq[1:] == sorted(overview['map'][3]):
                                args = 4, 20, seq[0]
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
                            args = 5, 20, seq[1]
                        elif count == 4 and 1 not in overview['map'] and seq[left:right] == sorted(overview['map'][3]):
                            args = 4, 20, seq[left]
            else:
                seq = sorted(overview['map'][3])
                count = len(seq)
                if count > 1:
                    if seq[0] == 1:
                        if count > 3 and list(range(seq[1], seq[-1] + 1)) == seq[1:]:
                            if count == 4:
                                args = count - 1, overview['qty'], seq[1]
                            elif count == 4 + len(overview['map'].get(1, ())) + 2 * len(overview['map'].get(2, ())):
                                args = count - 1, overview['qty'], seq[1]
                    elif count in (2, 3):
                        if list(range(seq[0], seq[-1] + 1)) == seq:
                            if 1 in overview['map']:
                                if len(overview['map'][1]) + 2 * len(overview['map'].get(2, ())) == count:
                                    args = count, overview['qty'], seq[0]
                            elif 2 * len(overview['map'].get(2, ())) in (0, count, 2 * count):
                                args = count, overview['qty'], seq[0]
                    elif 1 in overview['map']:
                        least = len(overview['map'][1]) + 2 * len(overview['map'].get(2, ()))
                        if count == least:
                            if list(range(seq[0], seq[-1] + 1)) == seq:
                                args = count, overview['qty'], seq[0]
                        elif least < 3 and count == least + 4 and list(range(seq[1], seq[-2] + 1)) == seq[1:-1]:
                            if seq[0] + 1 == seq[1]:
                                args = count - 1, overview['qty'], seq[0]
                            elif seq[-1] - 1 == seq[-2]:
                                args = count - 1, overview['qty'], seq[1]
                    elif 2 in overview['map']:
                        least = len(overview['map'][2])
                        if least > 1:
                            if list(range(seq[0], seq[-1] + 1)) == seq:
                                if count in (least, 2 * least):
                                    args = count, overview['qty'], seq[0]
                        elif count == 6 and list(range(seq[1], seq[-2] + 1)) == seq[1:-1]:
                            if seq[0] + 1 == seq[1]:
                                args = count - 1, overview['qty'], seq[0]
                            elif seq[-1] - 1 == seq[-2]:
                                args = count - 1, overview['qty'], seq[1]
                    elif list(range(seq[1], seq[-2] + 1)) == seq[1:-1]:
                        if seq[0] + 1 == seq[1]:
                            if seq[-1] - 1 == seq[-2]:
                                if count == 4:
                                    # can be specified
                                    pass
                                args = count, overview['qty'], seq[0]
                            elif count == 4:
                                args = count - 1, overview['qty'], seq[0]
                        elif count == 4 and seq[-1] - 1 == seq[-2]:
                            args = count - 1, overview['qty'], seq[1]
        elif 4 in overview['map'] and len(overview['map']) == 1 and 1 not in overview['map'][4]:
            seq = sorted(overview['map'][4])
            if list(range(seq[0], seq[-1] + 1)) == seq:
                args = len(seq), overview['qty'], seq[0]

        if args:
            view = []
            for s in cards.values():
                view.extend(s)
            count, qty, v = args
            return view, count, qty, v

    def __init__(self, owner, view, count, qty, v):
        super().__init__(owner, view)
        self.count: int = count
        self.qty: int = qty
        self.v: int = v

    def __gt__(self, other):
        if isinstance(other, self.whoami()) and self.count == other.count and self.qty == other.qty and self.v < other.v:
            return True
        return False

    def detect(self, cards: dict, owner) -> tuple:
        v = self.v - 1
        while v > 1:
            view = []
            right = v + self.count
            for i in range(v, right):
                if i in cards and len(cards[i]) == 3:
                    view.extend(cards[i])
                    continue
                break
            else:
                count = self.qty - 3 * self.count
                if not count:
                    return self.whoami()(owner, view, v), {k: cards[k] for k in range(v, right)}
                else:
                    fallback = {}
                    for k in range(max(cards), right - 1, -1):
                        if k in cards and len(cards[k]) < 3:
                            fallback.setdefault(len(cards[k]), []).append(k)
                    for k in range(v - 1, min(cards) - 1, -1):
                        if k in cards and len(cards[k]) < 3:
                            if not k and len(cards[k]) == 2:
                                continue
                            fallback.setdefault(len(cards[k]), []).append(k)
                    if count == self.count:
                        if len(fallback.get(1, ())) + 2 * len(fallback.get(2, ())) >= count:
                            i = 0
                            while i < count:
                                left = count - i
                                if 1 in fallback:
                                    k = fallback[1][0]
                                    if 2 not in fallback or k > fallback[2][0]:
                                        i += 1
                                        view.extend(cards[k])
                                        del fallback[1][0]
                                        if not fallback[1]:
                                            del fallback[1]
                                        continue
                                k = fallback[2][0]
                                if left > 1:
                                    i += 2
                                    view.extend(cards[k])
                                    del fallback[2][0]
                                    if not fallback[2]:
                                        del fallback[2]
                                else:
                                    i += 1
                                    view.append(next(iter(cards[k])))
                            cards = {k: cards[k] for k in range(v, right)}
                            for card in view[3 * self.count:]:
                                cards.setdefault(card[0], set()).add(card)
                            return self.whoami()(owner, view, v), cards
                    else:
                        count //= 2
                        if len(fallback.get(2, ())) >= count:
                            for k in fallback[2][:count]:
                                view.extend(cards[k])
                            cards = {k: cards[k] for k in range(v, right)}
                            for card in view[3 * self.count:]:
                                cards.setdefault(card[0], set()).add(card)
                            return self.whoami()(owner, view, v), cards
            v -= self.count - len(view)
        for v in range(max(cards), max(min(cards) - 1, 0), -1):
            if v in cards and len(cards) == 4:
                return RealBomb(owner, [(v, j) for j in range(4)], v), {v: cards[v]}
        if 0 in cards and len(cards[0]) == 2:
            return JokerBomb(owner, [(0, 0), (0, 1)]), {0: cards[0]}
        return Pass(owner, None), None


class FakeBomb(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        if 4 in overview['map']:
            if overview['qty'] == 6:
                if 1 in overview['map']:
                    if len(overview['map'][1]) == 2:
                        v = overview['map'][4][0]
                        view = [(v, j) for j in range(4)]
                        view.extend(sorted(next(iter(cards[k])) for k in overview['map'][1]))
                        return view, overview['qty'], v
                elif 2 in overview['map'] and len(overview['map'][2]) == 1:
                    v = overview['map'][4][0]
                    view = [(v, j) for j in range(4)]
                    view.extend(sorted(cards[overview['map'][2][0]]))
                    return view, overview['qty'], v
            elif overview['qty'] == 8:
                if 2 in overview['map']:
                    if len(overview['map'][2]) == 2:
                        v = overview['map'][4][0]
                        view = [(v, j) for j in range(4)]
                        for k in sorted(overview['map'][2]):
                            view.extend(sorted(cards[k]))
                        return view, overview['qty'], v
                elif len(overview['map'][4]) == 2:
                    # can be specified
                    v = overview['max']
                    i = overview['min']
                    view = [(v, j) for j in range(4)]
                    view.extend((i, j) for j in range(4))
                    return view, overview['qty'], v

    def __init__(self, owner, view, qty, v):
        super().__init__(owner, view)
        self.qty: int = qty
        self.v: int = v

    def __gt__(self, other):
        if isinstance(other, self.whoami()) and self.qty == other.qty and self.v < other.v:
            return True
        return False

    def detect(self, cards: dict, owner) -> tuple:
        right = self.v - 1
        left = min(cards)
        for v in range(right, max(left - 1, 0), -1):
            if v in cards and len(cards[v]) == 4:
                if self.qty == 6:
                    fallback = {1: []}
                    prime = 1
                else:
                    fallback = {2: []}
                    prime = 2
                for k in range(max(cards), left - 1, -1):
                    if k != v and k in cards:
                        qty = len(cards[k])
                        if qty == prime:
                            fallback[qty].append(k)
                            if len(fallback[qty]) == 2:
                                break
                        elif qty not in fallback and qty > prime:
                            fallback[qty] = k
                count = len(fallback[prime])
                if count == 2:
                    view = sorted(cards[v])
                    for i in range(2):
                        view.extend(cards[fallback[prime][i]])
                    fallback[prime].append(v)
                    return self.whoami()(owner, view, v), {k: cards[k] for k in fallback[prime]}
                if self.qty == 6:
                    if 2 in fallback:
                        if not count or fallback[1][0] < fallback[2]:
                            view = sorted(cards[v])
                            k = fallback[2]
                            view.extend(cards[k])
                            return self.whoami()(owner, view, v), {v: cards[v], k: cards[k]}
                    if count:
                        k = fallback[1][0]
                        card = None
                        if 2 in fallback:
                            card = next(iter(cards[fallback[2]]))
                        elif 3 in fallback:
                            card = next(iter(cards[fallback[3]]))
                        if card:
                            view = sorted(cards[v])
                            view.append(card)
                            view.extend(cards[k])
                            return self.whoami()(owner, view, v), {v: cards[v], k: cards[k], card[0]: {card}}
                elif count and 3 in fallback:
                    k = fallback[2][0]
                    view = sorted(cards[v])
                    view.extend(cards[k])
                    iterator = iter(cards[fallback[3]])
                    s = {next(iterator) for _ in range(2)}
                    view.extend(s)
                    return self.whoami()(owner, view, v), {v: cards[v], k: cards[k], fallback[3]: s}
                if 4 in fallback:
                    v = max(fallback[4], v)
                return RealBomb(owner, [(v, j) for j in range(4)], v), {v: cards[v]}
        for v in range(max(cards), right, -1):
            if v in cards and len(cards) == 4:
                return RealBomb(owner, [(v, j) for j in range(4)], v), {v: cards[v]}
        if 0 in cards and len(cards[0]) == 2:
            return JokerBomb(owner, [(0, 0), (0, 1)]), {0: cards[0]}
        return Pass(owner, None), None


class RealBomb(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        if overview['qty'] == 4 and 4 in overview['map']:
            v = overview['max']
            return [(v, j) for j in range(4)], v

    def __init__(self, owner, view, v):
        super().__init__(owner, view)
        self.v: int = v

    def __gt__(self, other):
        if isinstance(other, RealBomb) and self.v > other.v:
            return False
        if isinstance(other, JokerBomb):
            return False
        return True

    def detect(self, cards: dict, owner) -> tuple:
        right = self.v - 1
        left = min(cards)
        for v in range(right, max(left - 1, 0), -1):
            if v in cards and len(cards[v]) == 4:
                return self.whoami()(owner, [(v, j) for j in range(4)], v), {v: cards[v]}
        if 0 in cards and len(cards[0]) == 2:
            return JokerBomb(owner, [(0, 0), (0, 1)]), {0: cards[0]}
        return Pass(owner, None), None


class JokerBomb(Combo):
    @staticmethod
    def validate(overview: dict, cards: dict) -> tuple:
        if overview['qty'] == 2 and 2 in overview['map'] and not overview['map'][2][0]:
            return [(0, 0), (0, 1)],

    def __gt__(self, other):
        return True

    def detect(self, cards: dict, owner) -> tuple:
        return Pass(owner, None), None


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
