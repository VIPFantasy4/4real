# -*- coding: utf-8 -*-

from collections import OrderedDict
from combo import Combo
import client.extraClientApi as clientApi
import cfg

POKER = "textures/ui/poker/{}"
COLOR_CODE_MAPPING = {
    0: '§8{}'
}
M = {
    0: (),
    1: xrange(9, 10),
    2: xrange(9, 11),
    3: xrange(8, 11),
    4: xrange(8, 12),
    5: xrange(7, 12),
    6: xrange(7, 13),
    7: xrange(6, 13),
    8: xrange(6, 14),
    9: xrange(5, 14),
    10: xrange(5, 15),
    11: xrange(4, 15),
    12: xrange(4, 16),
    13: xrange(3, 16),
    14: xrange(3, 17),
    15: xrange(2, 17),
    16: xrange(2, 18),
    17: xrange(1, 18),
    18: xrange(1, 19),
    19: xrange(19),
    20: xrange(20),
}
COUNTDOWN = {
    'GangPhase': 7,
    'PlusPhase': 4,
    'MainPhase': 17
}


class Phase(object):
    def __init__(self, name, turn):
        self.name = name
        self.turn = turn


class Chain(object):
    def __init__(self, duel, phase, times, three, track):
        self.duel = duel  # type: Duel
        self.phase = Phase(*phase)
        self.times = abs(times)
        self.three = three
        self.track = track[:-2] + [Combo.fromargs(args) for args in track[-2:]]

        g = self.duel.g
        if self.three:
            pass
        g.SetText(g.times, str(self.times))

        countdown = COUNTDOWN.get(self.phase.name)
        if countdown:
            g.countdown = countdown

    def catch_up(self, phase, times, three, track):
        g = self.duel.g
        times = abs(times)
        if self.times != times:
            self.times = times
            g.SetText(g.times, str(times))
        if self.three != three:
            self.three = three
            pass
        phase = Phase(*phase)
        name = self.phase.name
        if name == 'DrawPhase':
            if name != phase.name:
                g.SetVisible(g.court + '/showhand', False)
        elif name == 'GangPhase':
            if name != phase.name:
                g.SetVisible(g.gang, False)
                g.SetVisible(g.mclock, False)
                g.SetVisible(g.lclock, False)
                g.SetVisible(g.rclock, False)
                g.SetVisible(g.choice, False)
                g.SetVisible(g.lchoice, False)
                g.SetVisible(g.rchoice, False)
        elif name == 'PlusPhase':
            if name != phase.name:
                g.SetVisible(g.plus, False)
                g.SetVisible(g.clock, False)
                g.SetVisible(g.choice, False)
                g.SetVisible(g.lchoice, False)
                g.SetVisible(g.rchoice, False)
        elif name == 'MainPhase':
            if name != phase.name:
                pass
            elif self.phase.turn == self.duel.uid != phase.turn:
                g.selected.clear()
                for i in xrange(20):
                    h = g.mh + '/m{}'.format(i)
                    g.SetPosition(h, g.origins[i])
        self.phase = phase
        if len(self.track) != len(track):
            g.SetVisible(g.notice, False)
        self.track = track[:-2] + [Combo.fromargs(args) for args in track[-2:]]

        countdown = COUNTDOWN.get(self.phase.name)
        if countdown:
            g.countdown = countdown


class Gambler(object):
    @property
    def choice(self):
        return self.duel.g.choice

    def __init__(self, duel, addr, cards, show_hand, role, og, times, bot):
        self.duel = duel  # type: Duel
        self.addr = addr
        self.cards = {}
        self.show_hand = show_hand
        self.role = role
        self.og = og
        self.times = times
        self.bot = bot

        g = self.duel.g
        phase = self.duel.chain.phase
        if phase.name == 'DrawPhase':
            if not show_hand:
                g.SetVisible(g.court + '/showhand', True)
        elif phase.name == 'PlusPhase':
            if not times:
                g.SetVisible(g.plus, True)
                g.SetVisible(g.clock, True)
            elif times == 1:
                g.SetText(g.choice, '不加倍')
                g.SetVisible(g.choice, True)
            elif times == 2:
                g.SetText(g.choice, '加倍')
                g.SetVisible(g.choice, True)
            elif times == 4:
                g.SetText(g.choice, '超级加倍')
                g.SetVisible(g.choice, True)
        elif phase.name == 'GangPhase':
            if phase.turn == addr:
                g.SetVisible(g.gang, True)
                g.SetVisible(g.mclock, True)
        elif phase.name == 'MainPhase':
            turn = phase.turn == addr
            slay = self._main(turn)
            if turn:
                if slay:
                    g.SetVisible(g.mclock, True)
                else:
                    g.SetVisible(g.clock, True)
                g.SetVisible(g.turn, True)
        if og:
            g.SetVisible(g.og, True)
        if bot > 0:
            g.SetVisible(g.auto, True)
        if times == 2:
            g.SetVisible(g.msu, True)
        elif times == 4:
            g.SetVisible(g.msup, True)
        if show_hand:
            g.SetVisible(g.msh, True)
        r = M[len(cards)]
        count = 0
        for i in xrange(20):
            h = g.mh + '/m{}'.format(i)
            on = i in r
            if on:
                card = tuple(cards[count])
                sprite = POKER.format(card)
                g.SetSprite(h + '/default', sprite)
                g.SetSprite(h + '/hover', sprite)
                g.SetSprite(h + '/pressed', sprite)
                count += 1
                self.cards[i] = card
            g.SetVisible(h, on)
        g.SetVisible(g.mh, True)

    def catch_up(self, addr, cards, show_hand, role, og, times, bot):
        self.role = role
        g = self.duel.g
        sh = False
        if self.show_hand != show_hand:
            sh = True
            if show_hand:
                g.SetVisible(g.msh, True)
            self.show_hand = show_hand
        phase = self.duel.chain.phase
        if phase.name == 'DrawPhase':
            if sh:
                if show_hand:
                    g.SetVisible(g.court + '/showhand', False)
                else:
                    g.SetVisible(g.court + '/showhand', True)
        elif phase.name == 'GangPhase':
            on = phase.turn == addr
            g.SetVisible(g.gang, on)
            g.SetVisible(g.mclock, on)
            if on:
                g.SetVisible(g.choice, False)
        elif phase.name == 'PlusPhase':
            if self.times != times:
                if not times:
                    g.SetVisible(g.plus, True)
                    g.SetVisible(g.clock, True)
                else:
                    g.SetVisible(g.plus, False)
                    g.SetVisible(g.clock, False)
                    if times == 1:
                        g.SetText(g.choice, '不加倍')
                        g.SetVisible(g.choice, True)
                    elif times == 2:
                        g.SetText(g.choice, '加倍')
                        g.SetVisible(g.choice, True)
                    elif times == 4:
                        g.SetText(g.choice, '超级加倍')
                        g.SetVisible(g.choice, True)
        elif phase.name == 'MainPhase':
            turn = phase.turn == addr
            slay = self._main(turn)
            if turn:
                g.SetVisible(g.choice, False)
                g.SetVisible(g.m, False)
            g.SetVisible(g.clock, turn and not slay)
            g.SetVisible(g.mclock, turn and slay)
            g.SetVisible(g.turn, turn)
        if self.times != times:
            if times == 2:
                g.SetVisible(g.msu, True)
            elif times == 4:
                g.SetVisible(g.msup, True)
            self.times = times
        if self.og != og:
            g.SetVisible(g.og, og)
            self.og = og
        if bot > 0 and not self.bot > 0:
            g.SetVisible(g.room + '/bot', False)
            g.SetVisible(g.auto, True)
        elif self.bot > 0 and not bot > 0:
            g.SetVisible(g.auto, False)
            g.SetVisible(g.room + '/bot', True)
        self.bot = bot
        if len(self.cards) != len(cards):
            g.selected.clear()
            g.last_result = None,
            g.proposals = None
            self.cards = {}
            r = M[len(cards)]
            count = 0
            for i in xrange(20):
                h = g.mh + '/m{}'.format(i)
                on = i in r
                if on:
                    card = tuple(cards[count])
                    sprite = POKER.format(card)
                    g.SetSprite(h + '/default', sprite)
                    g.SetSprite(h + '/hover', sprite)
                    g.SetSprite(h + '/pressed', sprite)
                    count += 1
                    self.cards[i] = card
                g.SetPosition(h, g.origins[i])
                g.SetVisible(h, on)

    def _main(self, turn):
        addr = self.addr
        g = self.duel.g
        track = self.duel.chain.track
        slay = False
        if turn:
            if not track:
                g.SetVisible(g.turn + '/pass', False)
                if self.show_hand:
                    slay = True
            elif track[-2:] + [None for _ in xrange(2 - len(track))] == [None, None]:
                slay = True
            if slay:
                if track:
                    g.SetVisible(g.turn + '/pass', False)
                g.SetVisible(g.turn + '/sh', False)
                g.SetVisible(g.turn + '/propose', False)
                g.SetVisible(g.turn + '/play', False)
                g.SetVisible(g.turn + '/hint', True)
                g.SetVisible(g.turn + '/slay', True)
            else:
                if track:
                    g.SetVisible(g.turn + '/sh', False)
                    g.SetVisible(g.turn + '/pass', True)
                g.SetVisible(g.turn + '/hint', False)
                g.SetVisible(g.turn + '/slay', False)
                g.SetVisible(g.turn + '/propose', True)
                g.SetVisible(g.turn + '/play', True)
        else:
            for combo in track[-2:]:
                if combo.owner == addr:
                    if combo.view:
                        view = combo.view
                        r = M[len(view)]
                        count = 0
                        for i in xrange(20):
                            c = g.m + '/c{}'.format(i)
                            on = i in r
                            if on:
                                g.SetSprite(c, POKER.format(tuple(view[count])))
                                count += 1
                            g.SetVisible(c, on)
                        g.SetVisible(g.m, True)
                    else:
                        g.SetText(g.choice, '不出')
                        g.SetVisible(g.choice, True)
                    break
        return slay


class L(object):
    @property
    def choice(self):
        return self.duel.g.lchoice

    def __init__(self, duel, addr, cards, show_hand, role, og, times, bot):
        self.duel = duel  # type: Duel
        self.addr = addr
        self.cards = cards
        self.show_hand = show_hand
        self.role = role
        self.og = og
        self.times = times
        self.bot = bot

        g = self.duel.g
        phase = self.duel.chain.phase
        if phase.name == 'PlusPhase':
            if times == 1:
                g.SetText(g.lchoice, '不加倍')
                g.SetVisible(g.lchoice, True)
            elif times == 2:
                g.SetText(g.lchoice, '加倍')
                g.SetVisible(g.lchoice, True)
            elif times == 4:
                g.SetText(g.lchoice, '超级加倍')
                g.SetVisible(g.lchoice, True)
        elif phase.name == 'GangPhase':
            if phase.turn == addr:
                g.SetVisible(g.lclock, True)
        elif phase.name == 'MainPhase':
            if phase.turn == addr:
                g.SetVisible(g.lclock, True)
            else:
                self._main()
        if show_hand:
            r = xrange(len(cards))
            count = 0
            for i in xrange(20):
                h = g.lh + '/h{}'.format(i)
                on = i in r
                if on:
                    g.SetSprite(h, POKER.format(tuple(cards[count])))
                    count += 1
                g.SetVisible(h, on)
            g.SetVisible(g.lh, True)
            g.SetText(g.lcount, str(len(cards)))
        else:
            g.SetText(g.lcount, str(cards))
        if times == 2:
            g.SetVisible(g.lsu, True)
        elif times == 4:
            g.SetVisible(g.lsup, True)
        if og:
            g.SetVisible(g.lbanker, True)
        if bot > 0:
            g.SetVisible(g.lrobot, True)

    def catch_up(self, addr, cards, show_hand, role, og, times, bot):
        self.role = role
        g = self.duel.g
        phase = self.duel.chain.phase
        if phase.name == 'GangPhase':
            on = phase.turn == addr
            g.SetVisible(g.lclock, on)
            if on:
                g.SetVisible(g.lchoice, False)
        elif phase.name == 'PlusPhase':
            if self.times != times:
                if times == 1:
                    g.SetText(g.lchoice, '不加倍')
                    g.SetVisible(g.lchoice, True)
                elif times == 2:
                    g.SetText(g.lchoice, '加倍')
                    g.SetVisible(g.lchoice, True)
                elif times == 4:
                    g.SetText(g.lchoice, '超级加倍')
                    g.SetVisible(g.lchoice, True)
        elif phase.name == 'MainPhase':
            turn = phase.turn == addr
            if turn:
                g.SetVisible(g.lchoice, False)
                g.SetVisible(g.l, False)
            else:
                self._main()
            g.SetVisible(g.lclock, turn)
        if self.times != times:
            if times == 2:
                g.SetVisible(g.lsu, True)
            elif times == 4:
                g.SetVisible(g.lsup, True)
            self.times = times
        if self.bot != bot:
            if bot > 0:
                g.SetVisible(g.lrobot, True)
            else:
                g.SetVisible(g.lrobot, False)
            self.bot = bot
        if self.og != og:
            g.SetVisible(g.lbanker, og)
            self.og = og
        qty = cards if isinstance(cards, int) else len(cards)
        if qty != (self.cards if isinstance(self.cards, int) else len(self.cards)):
            g.proposals = None
            g.SetText(g.lcount, str(qty))
            self.cards = cards
            if show_hand:
                self.show_hand = None
        if self.show_hand != show_hand:
            if show_hand:
                r = xrange(len(cards))
                count = 0
                for i in xrange(20):
                    h = g.lh + '/h{}'.format(i)
                    on = i in r
                    if on:
                        g.SetSprite(h, POKER.format(tuple(cards[count])))
                        count += 1
                    g.SetVisible(h, on)
            g.SetVisible(g.lh, show_hand)
            self.show_hand = show_hand

    def _main(self):
        addr = self.addr
        g = self.duel.g
        track = self.duel.chain.track
        for combo in track[-2:]:
            if combo.owner == addr:
                if combo.view:
                    view = combo.view
                    r = xrange(len(view))
                    count = 0
                    for i in xrange(20):
                        c = g.l + '/c{}'.format(i)
                        on = i in r
                        if on:
                            g.SetSprite(c, POKER.format(tuple(view[count])))
                            count += 1
                        g.SetVisible(c, on)
                    g.SetVisible(g.l, True)
                else:
                    g.SetText(g.lchoice, '不出')
                    g.SetVisible(g.lchoice, True)
                break


class R(object):
    @property
    def choice(self):
        return self.duel.g.rchoice

    def __init__(self, duel, addr, cards, show_hand, role, og, times, bot):
        self.duel = duel  # type: Duel
        self.addr = addr
        self.cards = cards
        self.show_hand = show_hand
        self.role = role
        self.og = og
        self.times = times
        self.bot = bot

        g = self.duel.g
        phase = self.duel.chain.phase
        if phase.name == 'PlusPhase':
            if times == 1:
                g.SetText(g.rchoice, '不加倍')
                g.SetVisible(g.rchoice, True)
            elif times == 2:
                g.SetText(g.rchoice, '加倍')
                g.SetVisible(g.rchoice, True)
            elif times == 4:
                g.SetText(g.rchoice, '超级加倍')
                g.SetVisible(g.rchoice, True)
        elif phase.name == 'GangPhase':
            if phase.turn == addr:
                g.SetVisible(g.rclock, True)
        elif phase.name == 'MainPhase':
            if phase.turn == addr:
                g.SetVisible(g.rclock, True)
            else:
                self._main()
        if show_hand:
            r = xrange(19, 19 - len(cards), -1)
            count = 0
            for i in xrange(20):
                h = g.rh + '/h{}'.format(i)
                on = i in r
                if on:
                    g.SetSprite(h, POKER.format(tuple(cards[count])))
                    count += 1
                g.SetVisible(h, on)
            g.SetVisible(g.rh, True)
            g.SetText(g.rcount, str(len(cards)))
        else:
            g.SetText(g.rcount, str(cards))
        if times == 2:
            g.SetVisible(g.rsu, True)
        elif times == 4:
            g.SetVisible(g.rsup, True)
        if og:
            g.SetVisible(g.rbanker, True)
        if bot > 0:
            g.SetVisible(g.rrobot, True)

    def catch_up(self, addr, cards, show_hand, role, og, times, bot):
        self.role = role
        g = self.duel.g
        phase = self.duel.chain.phase
        if phase.name == 'GangPhase':
            on = phase.turn == addr
            g.SetVisible(g.rclock, on)
            if on:
                g.SetVisible(g.rchoice, False)
        elif phase.name == 'PlusPhase':
            if self.times != times:
                if times == 1:
                    g.SetText(g.rchoice, '不加倍')
                    g.SetVisible(g.rchoice, True)
                elif times == 2:
                    g.SetText(g.rchoice, '加倍')
                    g.SetVisible(g.rchoice, True)
                elif times == 4:
                    g.SetText(g.rchoice, '超级加倍')
                    g.SetVisible(g.rchoice, True)
        elif phase.name == 'MainPhase':
            turn = phase.turn == addr
            if turn:
                g.SetVisible(g.rchoice, False)
                g.SetVisible(g.r, False)
            else:
                self._main()
            g.SetVisible(g.rclock, turn)
        if self.times != times:
            if times == 2:
                g.SetVisible(g.rsu, True)
            elif times == 4:
                g.SetVisible(g.rsup, True)
            self.times = times
        if self.bot != bot:
            if bot > 0:
                g.SetVisible(g.rrobot, True)
            else:
                g.SetVisible(g.rrobot, False)
            self.bot = bot
        if self.og != og:
            g.SetVisible(g.rbanker, og)
            self.og = og
        qty = cards if isinstance(cards, int) else len(cards)
        if qty != (self.cards if isinstance(self.cards, int) else len(self.cards)):
            g.proposals = None
            g.SetText(g.rcount, str(qty))
            self.cards = cards
            if show_hand:
                self.show_hand = None
        if self.show_hand != show_hand:
            if show_hand:
                r = xrange(19, 19 - len(cards), -1)
                count = 0
                for i in xrange(20):
                    h = g.rh + '/h{}'.format(i)
                    on = i in r
                    if on:
                        g.SetSprite(h, POKER.format(tuple(cards[count])))
                        count += 1
                    g.SetVisible(h, on)
            g.SetVisible(g.rh, show_hand)
            self.show_hand = show_hand

    def _main(self):
        addr = self.addr
        g = self.duel.g
        track = self.duel.chain.track
        for combo in track[-2:]:
            if combo.owner == addr:
                if combo.view:
                    view = combo.view
                    r = xrange(19, 19 - len(view), -1)
                    count = 0
                    for i in xrange(20):
                        c = g.r + '/c{}'.format(i)
                        on = i in r
                        if on:
                            g.SetSprite(c, POKER.format(tuple(view[count])))
                            count += 1
                        g.SetVisible(c, on)
                    g.SetVisible(g.r, True)
                else:
                    g.SetText(g.rchoice, '不出')
                    g.SetVisible(g.rchoice, True)
                break


class Duel(object):
    def __init__(self, g, uid, status, gamblers, chain):
        self.g = g  # type: GUI
        self.uid = uid
        self._status = status
        self.chain = Chain(self, *chain)
        od = OrderedDict()
        for cls, args in zip(((Gambler, R, L), (L, Gambler, R), (R, L, Gambler))[map(
                lambda args: args[0], gamblers).index(uid)], gamblers):
            gambler = cls(self, *args)
            od[gambler.addr] = gambler
        self.gamblers = od
        self._gang()

    def _gang(self):
        g = self.g
        if self.chain.phase.name == 'GangPhase':
            phase = self.chain.phase
            turn = phase.turn
            order = 0
            for addr in self.gamblers:
                if addr == turn:
                    break
                order += 1
            iterator = iter(self.gamblers)
            i = 0
            thug = 0
            while i < 3:
                addr = next(iterator)
                gambler = self.gamblers[addr]
                if i == order:
                    if addr == self.uid:
                        if gambler.role or thug:
                            g.SetText(g.gang + '/fightover/button_label', '抢地主')
                            g.SetText(g.gang + '/giveup/button_label', '不抢')
                        else:
                            g.SetText(g.gang + '/fightover/button_label', '叫地主')
                            g.SetText(g.gang + '/giveup/button_label', '不叫')
                    if not gambler.role:
                        break
                    thug += 1
                elif i < order:
                    if not i or not thug:
                        g.SetText(gambler.choice, gambler.role and '叫地主' or '不叫')
                    else:
                        g.SetText(gambler.choice, gambler.role and '抢地主' or '不抢')
                    g.SetVisible(gambler.choice, True)
                elif thug > 1:
                    g.SetText(gambler.choice, gambler.role and '抢地主' or '不抢')
                    g.SetVisible(gambler.choice, True)
                thug += gambler.role
                i += 1

    def catch_up(self, uid, status, gamblers, chain):
        self.uid = uid
        self._status = status
        self.chain.catch_up(*chain)
        od = OrderedDict()
        for args in gamblers:
            gambler = self.gamblers[args[0]]
            gambler.catch_up(*args)
            od[gambler.addr] = gambler
        self.gamblers = od
        self._gang()


class Cli(clientApi.GetClientSystemCls()):
    def Update(self):
        self._update()

    def Destroy(self):
        self.UnListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), 'UiInitFinished', self,
                              self.initialize)
        self.UnListenForEvent(cfg.MOD_NAMESPACE, cfg.MOD_SRV_NAME, 'G_DEBUT', self, self.debut)
        self.UnListenForEvent(cfg.MOD_NAMESPACE, cfg.MOD_SRV_NAME, 'G_COURT', self, self.catch_up)

        self._destroy()

    @property
    def info(self):
        return self._info

    @info.setter
    def info(self, info):
        self._info = info
        if self._g:
            self._g.real = info

    def __init__(self, *args):
        super(Cli, self).__init__(*args)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), 'UiInitFinished', self,
                            self.initialize)
        self.ListenForEvent(cfg.MOD_NAMESPACE, cfg.MOD_SRV_NAME, 'G_DEBUT', self, self.debut)
        self.ListenForEvent(cfg.MOD_NAMESPACE, cfg.MOD_SRV_NAME, 'G_COURT', self, self.catch_up)

        self._info = None
        self.cache = None
        self._g = None  # type: GUI
        self._debut = False

    def _update(self):
        pass

    def _destroy(self):
        pass

    def initialize(self, *args):
        clientApi.RegisterUI(cfg.MOD_NAMESPACE, cfg.UI_NAMESPACE, cfg.UI_CLASS, cfg.UI_MAIN)
        self._g = clientApi.CreateUI(cfg.MOD_NAMESPACE, cfg.UI_NAMESPACE, {"isHud": 0})  # type: GUI
        self._g._cli = self
        if self._debut:
            self._g.duel = self.cache
            if self.info:
                self._g.real = self.info
        else:
            self._g.standby()
            self.NotifyToServer('G_DEBUT', {
                'pid': clientApi.GetLocalPlayerId(),
            })

    def debut(self, data):
        if self.info is None:
            self.info = data['info']
        if not self._debut:
            self._debut = True
            args = data.get('args')
            if self._g:
                self._g.duel = args
            else:
                self.cache = args

    def catch_up(self, data):
        args = data['args']
        if self._g:
            self._g.duel = args
        else:
            self.cache = args
        if not self._debut:
            self._debut = True


class Task(object):
    FRAME = 0
    TIMES = 0

    def __init__(self, work, interval=1, times=None, skip=0):
        self.interval = interval
        self.times = times
        self.work = work

    def done(self):
        return self.times and self.TIMES >= self.times

    def loop(self):
        self.FRAME += 1
        if not self.FRAME % self.interval:
            self.work()
            self.FRAME = 0
            if self.times:
                self.TIMES += 1


class GUI(clientApi.GetScreenNodeCls()):
    def SetVisible(self, widget, on):
        if widget in self.clocks:
            if on:
                sec = self.clocks[widget]
                if sec is None and self.countdown is not None:
                    self.clocks[widget] = self.countdown
                    self.SetText(widget + '/sec', str(self.countdown))
            elif self.clocks[widget] is not None:
                self.clocks[widget] = None
        super(GUI, self).SetVisible(widget, on)

    def Update(self):
        if self.tasks:
            for i in xrange(len(self.tasks) - 1, -1, -1):
                task = self.tasks[i]
                task.loop()
                if task.done():
                    del self.tasks[i]

    def Create(self):
        self.AddTouchEventHandler(self.homepage + '/classic', self.classic)  # flip
        self.AddTouchEventHandler(self.c + '/classical', self.classical)  # flip
        self.AddTouchEventHandler(self.cc + '/rookie', self.rookie)  # flip
        self.AddTouchEventHandler(self.room + '/match', self.match)  # room
        self.AddTouchEventHandler(self.room + '/bot', self.bot)  # room
        self.AddTouchEventHandler(self.auto + '/resume', self.resume)  # room
        origins = []
        for i in xrange(20):
            h = self.mh + '/m{}'.format(i)
            origins.append(self.GetPosition(h))
            self.AddTouchEventHandler(h, self.select)
        self.origins = tuple(origins)
        self.AddTouchEventHandler(self.court + '/showhand', self.showhand)  # room
        self.AddTouchEventHandler(self.gang + '/fightover', self.fightover)  # room
        self.AddTouchEventHandler(self.gang + '/giveup', self.giveup)  # room
        self.AddTouchEventHandler(self.plus + '/su', self.su)  # room
        self.AddTouchEventHandler(self.plus + '/sup', self.sup)  # room
        self.AddTouchEventHandler(self.plus + '/calm', self.calm)  # room
        self.AddTouchEventHandler(self.turn + '/pass', self.skip)  # room
        self.AddTouchEventHandler(self.turn + '/propose', self.propose)  # room
        self.AddTouchEventHandler(self.turn + '/play', self.play)  # room
        self.AddTouchEventHandler(self.turn + '/sh', self.showhand)  # room
        self.AddTouchEventHandler(self.turn + '/hint', self.propose)  # room
        self.AddTouchEventHandler(self.turn + '/slay', self.play)  # room

    # <editor-fold desc="widgets">
    # region room
    @property
    def msup(self):
        return self.infobar + '/msup'

    @property
    def msu(self):
        return self.infobar + '/msu'

    @property
    def msh(self):
        return self.infobar + '/msh'

    @property
    def mclock(self):
        return self.court + '/mclock'

    @property
    def clock(self):
        return self.court + '/clock'

    @property
    def m(self):
        return self.court + '/m'

    @property
    def notice(self):
        return self.court + '/notice'

    @property
    def choice(self):
        return self.court + '/choice'

    @property
    def auto(self):
        return self.court + '/auto'

    @property
    def rrobot(self):
        return self.ricon + '/robot'

    @property
    def rchoice(self):
        return self.right + '/rchoice'

    @property
    def rclock(self):
        return self.right + '/rclock'

    @property
    def r(self):
        return self.right + '/r'

    @property
    def rh(self):
        return self.right + '/rh'

    @property
    def rsup(self):
        return self.right + '/rsup'

    @property
    def rsu(self):
        return self.right + '/rsu'

    @property
    def rcount(self):
        return self.right + '/rblank/count'

    @property
    def rbanker(self):
        return self.right + '/rbanker'

    @property
    def rreal(self):
        return self.right + '/rreal'

    @property
    def rname(self):
        return self.right + '/rname'

    @property
    def rplate(self):
        return self.right + '/rplate'

    @property
    def ricon(self):
        return self.right + '/ricon'

    @property
    def right(self):
        return self.court + '/right'

    @property
    def lrobot(self):
        return self.licon + '/robot'

    @property
    def lchoice(self):
        return self.left + '/lchoice'

    @property
    def lclock(self):
        return self.left + '/lclock'

    @property
    def l(self):
        return self.left + '/l'

    @property
    def lh(self):
        return self.left + '/lh'

    @property
    def lsup(self):
        return self.left + '/lsup'

    @property
    def lsu(self):
        return self.left + '/lsu'

    @property
    def lcount(self):
        return self.left + '/lblank/count'

    @property
    def lbanker(self):
        return self.left + '/lbanker'

    @property
    def lreal(self):
        return self.left + '/lreal'

    @property
    def lname(self):
        return self.left + '/lname'

    @property
    def lplate(self):
        return self.left + '/lplate'

    @property
    def licon(self):
        return self.left + '/licon'

    @property
    def left(self):
        return self.court + '/left'

    @property
    def mh(self):
        return self.court + '/mh'

    @property
    def turn(self):
        return self.court + '/turn'

    @property
    def plus(self):
        return self.court + '/plus'

    @property
    def gang(self):
        return self.court + '/gang'

    @property
    def court(self):
        return self.room + '/court'

    @property
    def utmost(self):
        return self.tag + '/utmost'

    @property
    def fee(self):
        return self.tag + '/fee'

    @property
    def tag(self):
        return self.room + '/tag'

    @property
    def room(self):
        return self.real + '/room'

    # endregion

    # region flip
    @property
    def cc(self):
        return self.flip + '/c-c'

    @property
    def c(self):
        return self.flip + '/c'

    @property
    def homepage(self):
        return self.flip + '/homepage'

    @property
    def flip(self):
        return self.real + '/flip'

    # endregion

    # region bottom
    @property
    def times(self):
        return self.infobar + '/times'

    @property
    def balance(self):
        return self.infobar + '/balance'

    @property
    def shorty(self):
        return self.infobar + '/shorty'

    @property
    def plate(self):
        return self.infobar + '/plate'

    @property
    def og(self):
        return self.icon + '/og'

    @property
    def icon(self):
        return self.infobar + '/icon'

    @property
    def infobar(self):
        return self.bottom + '/infobar'

    @property
    def toolbar(self):
        return self.bottom + '/toolbar'

    @property
    def bottom(self):
        return self.real + '/bottom'

    # endregion

    # region top
    @property
    def rank(self):
        return self.top + '/rank'

    @property
    def top(self):
        return self.real + '/top'

    # endregion
    # </editor-fold>

    @property
    def real(self):
        return self.prefix + '/4real'

    @real.setter
    def real(self, info):
        self.SetText(self.balance, info['real'])
        self.SetText(self.top + '/real', info['real'])
        self.SetText(self.shorty, COLOR_CODE_MAPPING[0].format(info['name']))
        self.SetText(self.top + '/name', COLOR_CODE_MAPPING[0].format(info['name']))
        self.SetSprite(self.plate, info['rank'])
        self.SetSprite(self.rank, info['rank'])
        self.SetSprite(self.icon, info['icon'])
        self.SetSprite(self.top + '/head/default', info['icon'])
        self.SetSprite(self.top + '/head/hover', info['icon'])
        self.SetSprite(self.top + '/head/pressed', info['icon'])

    @property
    def duel(self):
        return self._duel

    @duel.setter
    def duel(self, args):
        if not self.debut:
            self.debut = True
        if self.duel is args is None:
            self.SetVisible(self.mh, False)
            self.SetVisible(self.court, False)
            self.SetVisible(self.room, False)
            self.SetVisible(self.real, True)
            return
        if self.retreat:
            pass
        if self.duel is None:
            self._duel = Duel(self, *args)
            self.tasks.append(Task(self.sec, 30))
            self.SetVisible(self.room + '/change', False)
            self.SetVisible(self.room + '/match', False)
            self.SetVisible(self.room + '/bot', True)
            self.SetVisible(self.court, True)
        else:
            self.duel.catch_up(*args)

    def __init__(self, *args):
        super(GUI, self).__init__(*args)
        self.debut = False
        self.retreat = False
        self.prefix = (
            '/variables_button_mappings_and_controls'
            '/safezone_screen_matrix'
            '/inner_matrix'
            '/safezone_screen_panel'
            '/root_screen_panel'
        )
        self.clocks = {
            self.clock: None,
            self.mclock: None,
            self.rclock: None,
            self.lclock: None,
        }
        self.tasks = []
        self.selected = set()
        self.last_result = None,
        self.proposals = None
        self.last_proposal = None
        self.origins = None
        self.countdown = None
        self._court = None
        self._duel = None

    def sec(self):
        for clock, sec in self.clocks.iteritems():
            if sec is not None:
                if sec:
                    sec -= 1
                    self.clocks[clock] = sec
                    self.SetText(clock + '/sec', str(sec))

    def standby(self):
        self.SetVisible(self.real, False)

    def classic(self, kws):
        if kws["TouchEvent"] == clientApi.GetMinecraftEnum().TouchEvent.TouchUp:
            self.SetVisible(self.homepage, False)
            self.SetVisible(self.c, True)

    def classical(self, kws):
        if kws["TouchEvent"] == clientApi.GetMinecraftEnum().TouchEvent.TouchUp:
            self.SetVisible(self.c, False)
            self.SetVisible(self.cc, True)

    def rookie(self, kws):
        if kws["TouchEvent"] == clientApi.GetMinecraftEnum().TouchEvent.TouchUp:
            if self.retreat:
                pass
            elif self._court is None:
                self._court = 0
                self.SetText(self.fee, '996')
                self.SetText(self.utmost, '4396万')
                self.SetVisible(self.top, False)
                self.SetVisible(self.flip, False)
                self.SetVisible(self.toolbar, False)
                self.SetVisible(self.infobar, True)
                self.SetVisible(self.room, True)

    def match(self, kws):
        if kws["TouchEvent"] == clientApi.GetMinecraftEnum().TouchEvent.TouchUp:
            if self._court is not None:
                self._cli.NotifyToServer('G_MATCH', {
                    'pid': clientApi.GetLocalPlayerId(),
                    'court': self._court
                })

    def select(self, kws):
        if kws["TouchEvent"] == clientApi.GetMinecraftEnum().TouchEvent.TouchMoveIn:
            if self.duel:
                i = int(kws['ButtonPath'][::-1].split('/', 1)[0][:-1][::-1])
                if i in self.duel.gamblers[self.duel.uid].cards:
                    x, y = self.origins[i]
                    if i in self.selected:
                        self.selected.discard(i)
                        self.SetPosition(kws['ButtonPath'], (x, y))
                    else:
                        self.selected.add(i)
                        self.SetPosition(kws['ButtonPath'], (x, y - 14.0))

    def bot(self, kws):
        if kws["TouchEvent"] == clientApi.GetMinecraftEnum().TouchEvent.TouchUp:
            self._cli.NotifyToServer('G_COURT', {
                'pid': clientApi.GetLocalPlayerId(),
                'name': 'bot',
                'args': [1]
            })

    def resume(self, kws):
        if kws["TouchEvent"] == clientApi.GetMinecraftEnum().TouchEvent.TouchUp:
            self._cli.NotifyToServer('G_COURT', {
                'pid': clientApi.GetLocalPlayerId(),
                'name': 'bot',
                'args': [0]
            })

    def showhand(self, kws):
        if kws["TouchEvent"] == clientApi.GetMinecraftEnum().TouchEvent.TouchUp:
            self._cli.NotifyToServer('G_COURT', {
                'pid': clientApi.GetLocalPlayerId(),
                'name': 'show_hand',
                'args': []
            })

    def fightover(self, kws):
        if kws["TouchEvent"] == clientApi.GetMinecraftEnum().TouchEvent.TouchUp:
            self._cli.NotifyToServer('G_COURT', {
                'pid': clientApi.GetLocalPlayerId(),
                'name': 'choose',
                'args': [1]
            })

    def giveup(self, kws):
        if kws["TouchEvent"] == clientApi.GetMinecraftEnum().TouchEvent.TouchUp:
            self._cli.NotifyToServer('G_COURT', {
                'pid': clientApi.GetLocalPlayerId(),
                'name': 'choose',
                'args': [0]
            })

    def calm(self, kws):
        if kws["TouchEvent"] == clientApi.GetMinecraftEnum().TouchEvent.TouchUp:
            self._cli.NotifyToServer('G_COURT', {
                'pid': clientApi.GetLocalPlayerId(),
                'name': 'times',
                'args': [1]
            })

    def su(self, kws):
        if kws["TouchEvent"] == clientApi.GetMinecraftEnum().TouchEvent.TouchUp:
            self._cli.NotifyToServer('G_COURT', {
                'pid': clientApi.GetLocalPlayerId(),
                'name': 'times',
                'args': [2]
            })

    def sup(self, kws):
        if kws["TouchEvent"] == clientApi.GetMinecraftEnum().TouchEvent.TouchUp:
            self._cli.NotifyToServer('G_COURT', {
                'pid': clientApi.GetLocalPlayerId(),
                'name': 'times',
                'args': [4]
            })

    def skip(self, kws):
        if kws["TouchEvent"] == clientApi.GetMinecraftEnum().TouchEvent.TouchUp:
            self._cli.NotifyToServer('G_COURT', {
                'pid': clientApi.GetLocalPlayerId(),
                'name': 'play',
                'args': [{}]
            })

    def propose(self, kws):
        if kws["TouchEvent"] == clientApi.GetMinecraftEnum().TouchEvent.TouchUp:
            if self.duel and self.duel.chain:
                phase = self.duel.chain.phase
                track = self.duel.chain.track
                if phase.turn == self.duel.uid and phase.name == 'MainPhase':
                    if self.proposals is None:
                        self.last_proposal = None
                        cards = {}
                        for card in self.duel.gamblers[self.duel.uid].cards.itervalues():
                            cards.setdefault(card[0], []).append(card)
                        duo = track[-2:] + [None for _ in xrange(2 - len(track))]
                        if duo == [None, None]:
                            combo = None
                        else:
                            try:
                                duo.remove(None)
                            except ValueError:
                                pass
                            combo = duo[-1]
                        self.proposals = Combo.propose(cards, combo)
                        if not self.proposals:
                            self.SetVisible(self.notice, True)
                    proposals = self.proposals  # type: list
                    if proposals:
                        if len(proposals) != 1 or self.last_proposal != self.selected:
                            self.SetVisible(self.notice, False)
                            proposals.append(proposals.pop(0))
                            proposal = proposals[-1][-1].copy()
                            cards = self.duel.gamblers[self.duel.uid].cards
                            for i in xrange(max(cards), min(cards) - 1, -1):
                                x, y = self.origins[i]
                                h = self.mh + '/m{}'.format(i)
                                if cards[i][0] in proposal:
                                    k = cards[i][0]
                                    proposal[k] -= 1
                                    if not proposal[k]:
                                        del proposal[k]
                                    self.selected.add(i)
                                    self.SetPosition(h, (x, y - 14.0))
                                else:
                                    self.selected.discard(i)
                                    self.SetPosition(h, (x, y))
                            if not self.last_proposal and len(proposals) == 1:
                                self.last_proposal = self.selected.copy()

    def play(self, kws):
        if kws["TouchEvent"] == clientApi.GetMinecraftEnum().TouchEvent.TouchUp:
            if self.duel and self.duel.chain:
                phase = self.duel.chain.phase
                if self.selected and phase.turn == self.duel.uid and phase.name == 'MainPhase':
                    if self.last_result[0] != self.selected:
                        cards = {}
                        gambler = self.duel.gamblers[self.duel.uid]
                        for i in self.selected:
                            card = gambler.cards[i]
                            cards.setdefault(card[0], []).append(card)
                        valid = Combo.fromcards(cards, None)
                        self.last_result = self.selected.copy(), valid and cards
                        if not valid:
                            self.SetVisible(self.notice, True)
                    cards = self.last_result[1]
                    if cards:
                        self._cli.NotifyToServer('G_COURT', {
                            'pid': clientApi.GetLocalPlayerId(),
                            'name': 'play',
                            'args': [cards]
                        })
