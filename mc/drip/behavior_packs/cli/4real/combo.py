class Combo(object):
    @classmethod
    def whoami(cls):
        return cls

    @staticmethod
    def fromargs(args):
        return globals()[args[0]](*args[1:])

    @staticmethod
    def propose(cards, combo):
        if combo:
            return combo.detect(cards)
        else:
            combo = Combo.fromcards(cards, None)
            if combo is None:
                return Combo.autodetect(cards)
            proposal = {}
            for card in combo.view:
                k = card[0]
                if k in proposal:
                    proposal[k] += 1
                else:
                    proposal[k] = 1
            return [(proposal,)]

    @staticmethod
    def fromcards(cards, owner):
        if not cards:
            return
        overview = {
            'qty': 0,
            'max': None,
            'min': None,
            'map': {}
        }
        for k, v in cards.iteritems():
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
    def autodetect(cards):
        if not cards:
            return []
        fallback = {}
        for item in sorted(cards.iteritems(), reverse=True):
            qty = len(item[1])
            if qty == 1:
                view = list(item[1])
                k = item[0]
                if k > 5:
                    c = {2: 0, 3: 0, 4: 0}
                    while k > 2:
                        k -= 1
                        if k in cards:
                            qty = len(cards[k])
                            if qty in (3, 4):
                                if c[qty]:
                                    break
                                c[qty] += 1
                            elif qty == 2:
                                if c[2] == 2:
                                    break
                                c[qty] += 1
                            view.append(next(iter(cards[k])))
                            continue
                        break
                    view.reverse()
                qty = len(view)
                if qty > 4:
                    return [({card[0]: 1 for card in view},)]
                if 3 in fallback:
                    v = fallback[3]
                    view = sorted(cards[v])
                    view.extend(item[1])
                    return [({item[0]: 1, v: 3},)]
                return [({item[0]: 1},)]
            if qty == 2:
                if item[0]:
                    view = list(item[1])
                    k = item[0]
                    if k > 3:
                        while k > 2:
                            k -= 1
                            if k in cards and len(cards[k]) == 2:
                                view.extend(cards[k])
                                continue
                            break
                        view.reverse()
                    qty = len(view)
                    if qty > 5:
                        v = view[0][0]
                        return [({k: 2 for k in xrange(v, v + qty // 2)},)]
                    if 3 in fallback:
                        v = fallback[3]
                        view = sorted(cards[v])
                        view.extend(item[1])
                        return [({item[0]: 2, v: 3},)]
                    return [({item[0]: 2},)]
            elif qty not in fallback:
                fallback[qty] = item[0]
        if 3 in fallback:
            v = fallback[3]
            return [({v: 3},)]
        v = fallback[4]
        return [({v: 4},)]

    def __init__(self, owner, view):
        self._owner = owner
        self._view = view and tuple(view)

    @property
    def owner(self):
        return self._owner

    @property
    def view(self):
        return self._view

    @property
    def times(self):
        if self.whoami() in (RealBomb, JokerBomb):
            return 2
        return False


class Single(Combo):
    @staticmethod
    def validate(overview, cards):
        if overview['qty'] == 1:
            card = next(iter(cards[overview['max']]))
            return [card], card

    def regress(self):
        return self.__class__.__name__, self.owner.addr, self.view, self.card

    def __init__(self, owner, view, card):
        super(Single, self).__init__(owner, view)
        self.card = card

    def __gt__(self, other):
        if isinstance(other, Single):
            if not self.card[0] and not other.card[0]:
                if not self.card[1]:
                    return True
            elif self.card[0] < other.card[0]:
                return True
        return False

    def detect(self, cards):
        proposals = []
        right = self.card[0] - 1
        if self.card[0]:
            left = min(cards)
            for v in xrange(right, left - 1, -1):
                if v in cards:
                    qty = len(cards[v])
                    if qty == 4:
                        proposals.append((qty, -v, {v: qty}))
                        proposals.append((5, -v, {v: 1}))
                        continue
                    proposals.append((qty, -v, {v: 1}))
        elif self.card[1] and 0 in cards:
            proposals.append((1, 0, {0: 1}))
        for v in xrange(max(cards), right, -1):
            if v in cards and len(cards) == 4:
                proposals.append((4, -v, {v: 4}))
        return sorted(proposals)


class Pair(Combo):
    @staticmethod
    def validate(overview, cards):
        if overview['qty'] == 2 and 2 in overview['map'] and overview['map'][2][0]:
            return sorted(cards[overview['max']]), overview['max']

    def regress(self):
        return self.__class__.__name__, self.owner.addr, self.view, self.v

    def __init__(self, owner, view, v):
        super(Pair, self).__init__(owner, view)
        self.v = v

    def __gt__(self, other):
        if isinstance(other, self.whoami()) and self.v < other.v:
            return True
        return False

    def detect(self, cards):
        proposals = []
        right = self.v - 1
        left = min(cards)
        for v in xrange(right, max(left - 1, 0), -1):
            if v in cards:
                qty = len(cards[v])
                if qty == 4:
                    proposals.append((qty, -v, {v: qty}))
                    proposals.append((5, -v, {v: 2}))
                    continue
                if qty > 1:
                    proposals.append((qty, -v, {v: 2}))
        for v in xrange(max(cards), right, -1):
            if v in cards and len(cards) == 4:
                proposals.append((4, -v, {v: 4}))
        if 0 in cards and len(cards[0]) == 2:
            proposals.append((4, 0, {0: 2}))
        return sorted(proposals)


class Seq(Combo):
    @staticmethod
    def validate(overview, cards):
        if overview['qty'] > 4 and overview['max'] > 1 and 1 in overview['map'] and len(overview['map']) == 1:
            seq = sorted(overview['map'][1])
            if list(xrange(overview['max'], overview['min'] + 1)) == seq:
                return [next(iter(cards[k])) for k in seq], overview['qty'], overview['max']

    def regress(self):
        return self.__class__.__name__, self.owner.addr, self.view, self.qty, self.v

    def __init__(self, owner, view, qty, v):
        super(Seq, self).__init__(owner, view)
        self.qty = qty
        self.v = v

    def __gt__(self, other):
        if isinstance(other, self.whoami()) and self.qty == other.qty and self.v < other.v:
            return True
        return False

    def detect(self, cards):
        proposals = []
        v = self.v - 1
        while v > 1:
            proposal = {}
            for i in xrange(v, v + self.qty):
                if i in cards:
                    proposal[i] = 1
                    continue
                break
            else:
                proposals.append((0, -i, proposal))
                v -= 1
                continue
            v -= self.qty - len(proposal)
        for v in xrange(max(cards), max(min(cards) - 1, 0), -1):
            if v in cards and len(cards) == 4:
                proposals.append((4, -v, {v: 4}))
        if 0 in cards and len(cards[0]) == 2:
            proposals.append((4, 0, {0: 2}))
        return sorted(proposals)


class PairSeq(Combo):
    @staticmethod
    def validate(overview, cards):
        if overview['qty'] > 5 and overview['max'] > 1 and 2 in overview['map'] and len(overview['map']) == 1:
            seq = sorted(overview['map'][2])
            if list(xrange(overview['max'], overview['min'] + 1)) == seq:
                view = []
                for k in seq:
                    view.extend(sorted(cards[k]))
                return view, overview['qty'], overview['max']

    def regress(self):
        return self.__class__.__name__, self.owner.addr, self.view, self.qty, self.v

    def __init__(self, owner, view, qty, v):
        super(PairSeq, self).__init__(owner, view)
        self.qty = qty
        self.v = v

    def __gt__(self, other):
        if isinstance(other, self.whoami()) and self.qty == other.qty and self.v < other.v:
            return True
        return False

    def detect(self, cards):
        proposals = []
        count = self.qty // 2
        v = self.v - 1
        while v > 1:
            proposal = {}
            for i in xrange(v, v + count):
                if i in cards and len(cards[i]) > 1:
                    proposal[i] = 2
                    continue
                break
            else:
                proposals.append((0, -i, proposal))
                v -= 1
                continue
            v -= count - len(proposal)
        for v in xrange(max(cards), max(min(cards) - 1, 0), -1):
            if v in cards and len(cards) == 4:
                proposals.append((4, -v, {v: 4}))
        if 0 in cards and len(cards[0]) == 2:
            proposals.append((4, 0, {0: 2}))
        return sorted(proposals)


class Triple(Combo):
    @staticmethod
    def validate(overview, cards):
        if overview['qty'] == 3 and 3 in overview['map']:
            return sorted(cards[overview['max']]), overview['max']

    def regress(self):
        return self.__class__.__name__, self.owner.addr, self.view, self.v

    def __init__(self, owner, view, v):
        super(Triple, self).__init__(owner, view)
        self.v = v

    def __gt__(self, other):
        if isinstance(other, self.whoami()) and self.v < other.v:
            return True
        return False

    def detect(self, cards):
        proposals = []
        right = self.v - 1
        left = min(cards)
        for v in xrange(right, max(left - 1, 0), -1):
            if v in cards:
                qty = len(cards[v])
                if qty == 4:
                    proposals.append((qty, -v, {v: qty}))
                    proposals.append((5, -v, {v: 3}))
                    continue
                if qty == 3:
                    proposals.append((qty, -v, {v: qty}))
        for v in xrange(max(cards), right, -1):
            if v in cards and len(cards) == 4:
                proposals.append((4, -v, {v: 4}))
        if 0 in cards and len(cards[0]) == 2:
            proposals.append((4, 0, {0: 2}))
        return sorted(proposals)


class TripleWithSingle(Combo):
    @staticmethod
    def validate(overview, cards):
        if overview['qty'] == 4 and 3 in overview['map']:
            view = sorted(cards[overview['map'][3][0]])
            view.extend([next(iter(cards[overview['map'][1][0]]))])
            return view, overview['map'][3][0]

    def regress(self):
        return self.__class__.__name__, self.owner.addr, self.view, self.v

    def __init__(self, owner, view, v):
        super(TripleWithSingle, self).__init__(owner, view)
        self.v = v

    def __gt__(self, other):
        if isinstance(other, self.whoami()) and self.v < other.v:
            return True
        return False

    def detect(self, cards):
        proposals = []
        right = self.v - 1
        left = min(cards)
        single = None
        for v in xrange(right, max(left - 1, 0), -1):
            if v in cards:
                qty = len(cards[v])
                if qty == 4:
                    proposals.append((qty, -v, {v: qty}))
                    continue
                if qty == 3:
                    if single:
                        proposals.append((0, -v, {v: qty, single: 1}))
                        continue
                    fallback = {}
                    for k in xrange(max(cards), left - 1, -1):
                        if k != v and k in cards:
                            qty = len(cards[k])
                            if qty == 1:
                                single = k
                                proposals.append((0, -v, {v: 3, single: 1}))
                                break
                            if qty not in fallback:
                                fallback[qty] = k
                    if single:
                        continue
                    if not fallback:
                        return []
                    if 2 in fallback and fallback[2]:
                        k = fallback[2]
                        single = k
                        proposals.append((0, -v, {v: 3, single: 1}))
                        continue
                    elif 3 in fallback:
                        k = fallback[3]
                        if k > v:
                            single = k
                            proposals.append((0, -v, {v: 3, single: 1}))
                        else:
                            single = v
                            proposals.append((0, -v, {v: 3, k: 1}))
                        continue
                    if 4 in fallback:
                        k = fallback[4]
                    else:
                        k = 0
                    single = v
                    proposals.append((0, -v, {v: 3, k: 1}))
        for v in xrange(max(cards), right, -1):
            if v in cards and len(cards) == 4:
                proposals.append((4, -v, {v: 4}))
        if 0 in cards and len(cards[0]) == 2:
            proposals.append((4, 0, {0: 2}))
        return sorted(proposals)


class TripleWithPair(Combo):
    @staticmethod
    def validate(overview, cards):
        if overview['qty'] == 5 and 3 in overview['map'] and 2 in overview['map']:
            view = sorted(cards[overview['map'][3][0]])
            view.extend(sorted(cards[overview['map'][2][0]]))
            return view, overview['map'][3][0]

    def regress(self):
        return self.__class__.__name__, self.owner.addr, self.view, self.v

    def __init__(self, owner, view, v):
        super(TripleWithPair, self).__init__(owner, view)
        self.v = v

    def __gt__(self, other):
        if isinstance(other, self.whoami()) and self.v < other.v:
            return True
        return False

    def detect(self, cards):
        proposals = []
        right = self.v - 1
        left = min(cards)
        pair = None
        for v in xrange(right, max(left - 1, 0), -1):
            if v in cards:
                qty = len(cards[v])
                if qty == 4:
                    proposals.append((qty, -v, {v: qty}))
                    continue
                if qty == 3:
                    if pair:
                        proposals.append((0, -v, {v: qty, pair: 2}))
                        continue
                    fallback = {}
                    for k in xrange(max(cards), left - 1, -1):
                        if k != v and k in cards:
                            qty = len(cards[k])
                            if qty > 1:
                                if qty == 2:
                                    if k:
                                        pair = k
                                        proposals.append((0, -v, {v: 3, pair: 2}))
                                        break
                                if qty not in fallback:
                                    fallback[qty] = k
                    if pair:
                        continue
                    if not fallback:
                        return []
                    if 3 in fallback:
                        k = fallback[3]
                        if k > v:
                            pair = k
                            proposals.append((0, -v, {v: 3, pair: 2}))
                        else:
                            pair = v
                            proposals.append((0, -v, {v: 3, k: 2}))
                        continue
                    if 4 in fallback:
                        k = fallback[4]
                    else:
                        k = 0
                    pair = v
                    proposals.append((0, -v, {v: 3, k: 2}))
        for v in xrange(max(cards), right, -1):
            if v in cards and len(cards) == 4:
                proposals.append((4, -v, {v: 4}))
        if 0 in cards and len(cards[0]) == 2:
            proposals.append((4, 0, {0: 2}))
        return sorted(proposals)


class Plane(Combo):
    @staticmethod
    def validate(overview, cards):
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
                    if seq[0] > 1 and len(seq) == 3 and list(xrange(seq[0], seq[-1] + 1)) == seq:
                        args = 3, 12, seq[0]
                elif overview['qty'] == 15:
                    seq = sorted(overview['map'][3])
                    if seq[0] > 1 and len(seq) == 3 and list(xrange(seq[0], seq[-1] + 1)) == seq and 2 in overview['map']:
                        args = 3, 15, seq[0]
                elif overview['qty'] == 16:
                    seq = sorted(overview['map'][3] + overview['map'][4])
                    count = len(seq)
                    if count == 4:
                        if seq[0] > 1 and list(xrange(seq[0], seq[-1] + 1)) == seq:
                            args = 4, 16, seq[0]
                    elif count == 5 and list(xrange(seq[1], seq[-2] + 1)) == seq[1:-1]:
                        if seq[0] > 1 and seq[0] + 1 == seq[1]:
                            args = 4, 16, seq[0]
                        elif seq[-1] - 1 == seq[-2]:
                            args = 4, 16, seq[1]
                elif overview['qty'] == 20:
                    seq = sorted(overview['map'][3] + overview['map'][4])
                    count = len(seq)
                    if count == 5:
                        if list(xrange(seq[1], seq[-2] + 1)) == seq[1:-1]:
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
                        if count > 3 and list(xrange(seq[1], seq[-1] + 1)) == seq[1:]:
                            if count == 4:
                                args = count - 1, overview['qty'], seq[1]
                            elif count == 4 + len(overview['map'].get(1, ())) + 2 * len(overview['map'].get(2, ())):
                                args = count - 1, overview['qty'], seq[1]
                    elif count in (2, 3):
                        if list(xrange(seq[0], seq[-1] + 1)) == seq:
                            if 1 in overview['map']:
                                if len(overview['map'][1]) + 2 * len(overview['map'].get(2, ())) == count:
                                    args = count, overview['qty'], seq[0]
                            elif 2 * len(overview['map'].get(2, ())) in (0, count, 2 * count):
                                args = count, overview['qty'], seq[0]
                    elif 1 in overview['map']:
                        least = len(overview['map'][1]) + 2 * len(overview['map'].get(2, ()))
                        if count == least:
                            if list(xrange(seq[0], seq[-1] + 1)) == seq:
                                args = count, overview['qty'], seq[0]
                        elif least < 3 and count == least + 4 and list(xrange(seq[1], seq[-2] + 1)) == seq[1:-1]:
                            if seq[0] + 1 == seq[1]:
                                args = count - 1, overview['qty'], seq[0]
                            elif seq[-1] - 1 == seq[-2]:
                                args = count - 1, overview['qty'], seq[1]
                    elif 2 in overview['map']:
                        least = len(overview['map'][2])
                        if least > 1:
                            if list(xrange(seq[0], seq[-1] + 1)) == seq:
                                if count in (least, 2 * least):
                                    args = count, overview['qty'], seq[0]
                        elif count == 6 and list(xrange(seq[1], seq[-2] + 1)) == seq[1:-1]:
                            if seq[0] + 1 == seq[1]:
                                args = count - 1, overview['qty'], seq[0]
                            elif seq[-1] - 1 == seq[-2]:
                                args = count - 1, overview['qty'], seq[1]
                    elif list(xrange(seq[1], seq[-2] + 1)) == seq[1:-1]:
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
            if list(xrange(seq[0], seq[-1] + 1)) == seq:
                args = len(seq), overview['qty'], seq[0]

        if args:
            view = []
            for s in cards.itervalues():
                view.extend(s)
            count, qty, v = args
            return view, count, qty, v

    def regress(self):
        return self.__class__.__name__, self.owner.addr, self.view, self.count, self.qty, self.v

    def __init__(self, owner, view, count, qty, v):
        super(Plane, self).__init__(owner, view)
        self.count = count
        self.qty = qty
        self.v = v

    def __gt__(self, other):
        if isinstance(other, self.whoami()) and self.count == other.count and self.qty == other.qty and self.v < other.v:
            return True
        return False

    def detect(self, cards):
        proposals = []
        v = self.v - 1
        while v > 1:
            view = []
            proposal = {}
            right = v + self.count
            for i in xrange(v, right):
                if i in cards and len(cards[i]) == 3:
                    proposal[i] = 3
                    view.extend(cards[i])
                    continue
                break
            else:
                count = self.qty - 3 * self.count
                if not count:
                    proposals.append((0, -i, proposal))
                    v -= 1
                    continue
                else:
                    fallback = {}
                    for k in xrange(max(cards), right - 1, -1):
                        if k in cards and len(cards[k]) < 3:
                            fallback.setdefault(len(cards[k]), []).append(k)
                    for k in xrange(v - 1, min(cards) - 1, -1):
                        if k in cards and len(cards[k]) < 3:
                            if not k and len(cards[k]) == 2:
                                continue
                            fallback.setdefault(len(cards[k]), []).append(k)
                    proper = False
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
                            proper = True
                    else:
                        count //= 2
                        if len(fallback.get(2, ())) >= count:
                            for k in fallback[2][:count]:
                                view.extend(cards[k])
                            proper = True
                    if proper:
                        for card in view[3 * self.count:]:
                            k = card[0]
                            if k in proposal:
                                proposal[k] += 1
                            else:
                                proposal[k] = 1
                        proposals.append((0, 1 - right, proposal))
                        v -= 1
                        continue
            v -= self.count - len(view)
        for v in xrange(max(cards), max(min(cards) - 1, 0), -1):
            if v in cards and len(cards) == 4:
                proposals.append((4, -v, {v: 4}))
        if 0 in cards and len(cards[0]) == 2:
            proposals.append((4, 0, {0: 2}))
        return sorted(proposals)


class FakeBomb(Combo):
    @staticmethod
    def validate(overview, cards):
        if 4 in overview['map']:
            if overview['qty'] == 6:
                if 1 in overview['map']:
                    if len(overview['map'][1]) == 2:
                        v = overview['map'][4][0]
                        view = [(v, j) for j in xrange(4)]
                        view.extend(sorted(next(iter(cards[k])) for k in overview['map'][1]))
                        return view, overview['qty'], v
                elif 2 in overview['map'] and len(overview['map'][2]) == 1:
                    v = overview['map'][4][0]
                    view = [(v, j) for j in xrange(4)]
                    view.extend(sorted(cards[overview['map'][2][0]]))
                    return view, overview['qty'], v
            elif overview['qty'] == 8:
                if 2 in overview['map']:
                    if len(overview['map'][2]) == 2:
                        v = overview['map'][4][0]
                        view = [(v, j) for j in xrange(4)]
                        for k in sorted(overview['map'][2]):
                            view.extend(sorted(cards[k]))
                        return view, overview['qty'], v
                elif len(overview['map'][4]) == 2:
                    # can be specified
                    v = overview['max']
                    i = overview['min']
                    view = [(v, j) for j in xrange(4)]
                    view.extend((i, j) for j in xrange(4))
                    return view, overview['qty'], v

    def regress(self):
        return self.__class__.__name__, self.owner.addr, self.view, self.qty, self.v

    def __init__(self, owner, view, qty, v):
        super(FakeBomb, self).__init__(owner, view)
        self.qty = qty
        self.v = v

    def __gt__(self, other):
        if isinstance(other, self.whoami()) and self.qty == other.qty and self.v < other.v:
            return True
        return False

    def detect(self, cards):
        proposals = []
        right = self.v - 1
        left = min(cards)
        for v in xrange(right, max(left - 1, 0), -1):
            if v in cards and len(cards[v]) == 4:
                proposal = {v: 4}
                if self.qty == 6:
                    fallback = {1: []}
                    prime = 1
                else:
                    fallback = {2: []}
                    prime = 2
                for k in xrange(max(cards), left - 1, -1):
                    if k != v and k in cards:
                        qty = len(cards[k])
                        if qty == prime:
                            if not k and prime == 2:
                                continue
                            fallback[qty].append(k)
                            if len(fallback[qty]) == 2:
                                break
                        elif qty not in fallback and qty > prime:
                            fallback[qty] = k
                count = len(fallback[prime])
                if count == 2:
                    for i in xrange(2):
                        k = fallback[prime][i]
                        proposal[k] = prime
                    proposals.append((0, -v, proposal))
                    continue
                if self.qty == 6:
                    if 2 in fallback:
                        if not count or fallback[1][0] < fallback[2]:
                            k = fallback[2]
                            proposal[k] = 2
                            proposals.append((0, -v, proposal))
                            continue
                    if count:
                        k = fallback[1][0]
                        card = None
                        if 2 in fallback:
                            card = next(iter(cards[fallback[2]]))
                        elif 3 in fallback:
                            card = next(iter(cards[fallback[3]]))
                        if card:
                            proposal[k] = 1
                            proposal[card[0]] = 1
                            proposals.append((0, -v, proposal))
                elif count and 3 in fallback:
                    k = fallback[2][0]
                    proposal[k] = 2
                    proposal[fallback[3]] = 2
                    proposals.append((0, -v, proposal))
                if len(proposal) == 1:
                    proposals.append((4, -v, proposal))
                continue
        for v in xrange(max(cards), right, -1):
            if v in cards and len(cards) == 4:
                proposals.append((4, -v, {v: 4}))
        if 0 in cards and len(cards[0]) == 2:
            proposals.append((4, 0, {0: 2}))
        return sorted(proposals)


class RealBomb(Combo):
    @staticmethod
    def validate(overview, cards):
        if overview['qty'] == 4 and 4 in overview['map']:
            v = overview['max']
            return [(v, j) for j in xrange(4)], v

    def regress(self):
        return self.__class__.__name__, self.owner.addr, self.view, self.v

    def __init__(self, owner, view, v):
        super(RealBomb, self).__init__(owner, view)
        self.v = v

    def __gt__(self, other):
        if isinstance(other, RealBomb) and self.v > other.v:
            return False
        if isinstance(other, JokerBomb):
            return False
        return True

    def detect(self, cards):
        proposals = []
        right = self.v - 1
        left = min(cards)
        for v in xrange(right, max(left - 1, 0), -1):
            if v in cards and len(cards[v]) == 4:
                proposals.append((4, -v, {v: 4}))
        if 0 in cards and len(cards[0]) == 2:
            proposals.append((4, 0, {0: 2}))
        return sorted(proposals)


class JokerBomb(Combo):
    @staticmethod
    def validate(overview, cards):
        if overview['qty'] == 2 and 2 in overview['map'] and not overview['map'][2][0]:
            return [(0, 0), (0, 1)],

    def regress(self):
        return self.__class__.__name__, self.owner.addr, self.view

    def __gt__(self, other):
        return True

    def detect(self, cards):
        return []


class Pass(Combo):
    def regress(self):
        return self.__class__.__name__, self.owner.addr, self.view

    def __eq__(self, o):
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
