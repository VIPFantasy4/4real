# -*- coding: utf-8 -*-

from collections import OrderedDict
import client.extraClientApi as clientApi
import cfg

POKER = "textures/ui/poker/{}"
M = {
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
        self.track = track

        g = self.duel.g
        if self.three:
            pass
        g.SetText(g.times, str(times))


class Gambler(object):
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
        if phase.name == 'DrawPhase':
            if not self.show_hand:
                g.SetVisible(g.court + '/showhand', True)
        elif phase.name == 'PlusPhase':
            if not self.times:
                g.SetVisible(g.plus, True)
        elif phase.name == 'GangPhase':
            if phase.turn == addr:
                g.SetVisible(g.gang, True)
        elif phase.name == 'MainPhase':
            track = self.duel.chain.track
            if phase.turn == addr:
                if not track:
                    g.SetVisible(g.turn + '/pass', False)
                elif track[-2:] + [None for _ in xrange(2 - len(track))] == [None, None]:
                    g.SetVisible(g.turn + '/pass', False)
                    g.SetVisible(g.turn + '/sh', False)
                else:
                    g.SetVisible(g.turn + '/sh', False)
                g.SetVisible(g.turn, True)
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
        if bot > 0:
            g.SetVisible(g.auto, True)
        r = M[len(cards)]
        count = 0
        for i in xrange(20):
            c = g.mh + '/m{}'.format(i)
            on = i in r
            if on:
                g.SetSprite(c + '', POKER.format(tuple(cards[count])))
                g.SetSprite(c + '', POKER.format(tuple(cards[count])))
                g.SetSprite(c + '', POKER.format(tuple(cards[count])))
                count += 1
            g.SetVisible(c, on)
        g.SetVisible(g.mh, True)


class L(Gambler):
    pass


class R(Gambler):
    pass


class Duel(object):
    def __init__(self, g, uid, status, gamblers, chain):
        self.g = g  # type: GUI
        self.uid = uid
        self._status = status
        self.chain = Chain(self, *chain)
        od = OrderedDict()
        for i, pair in enumerate(zip(((Gambler, R, L), (L, Gambler, R), (R, L, Gambler))[map(
                lambda args: args[0], gamblers).index(uid)], gamblers)):
            cls, args = pair
            gambler = cls(self, i, *args)
            od[gambler.addr] = gambler
        self.gamblers = od

    def catch_up(self):
        pass


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


class GUI(clientApi.GetScreenNodeCls()):
    def Create(self):
        self.AddTouchEventHandler(self.homepage + '/classic', self.classic)  # flip
        self.AddTouchEventHandler(self.c + '/classical', self.classical)  # flip
        self.AddTouchEventHandler(self.cc + '/rookie', self.rookie)  # flip
        self.AddTouchEventHandler(self.room + '/match', self.match)  # room

    # <editor-fold desc="widgets">
    # region room
    @property
    def msec(self):
        return self.mclock + '/msec'

    @property
    def mclock(self):
        return self.court + '/mclock'

    @property
    def sec(self):
        return self.clock + '/sec'

    @property
    def clock(self):
        return self.court + '/clock'

    @property
    def m(self):
        return self.court + '/m'

    @property
    def choice(self):
        return self.court + '/choice'

    @property
    def auto(self):
        return self.court + '/auto'

    @property
    def rchoice(self):
        return self.right + '/rchoice'

    @property
    def rsec(self):
        return self.rclock + '/rsec'

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
    def lchoice(self):
        return self.left + '/lchoice'

    @property
    def lsec(self):
        return self.lclock + '/lsec'

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
    def name(self):
        return self.top + '/name'

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
        self.SetText(self.shorty, info['name'])
        self.SetText(self.name, info['name'])
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
        if self._duel is args is None:
            self.SetVisible(self.court, False)
            self.SetVisible(self.room, False)
            self.SetVisible(self.real, True)
            return
        if self.retreat:
            pass
        if self._duel is None:
            self._duel = Duel(self, *args)
            self.SetVisible(self.court, True)

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
        self._selected = None
        self._duel = None

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
            elif self._selected is None:
                self._selected = 0
                self.SetVisible(self.top, False)
                self.SetVisible(self.flip, False)
                self.SetVisible(self.toolbar, False)
                self.SetVisible(self.infobar, True)
                self.SetVisible(self.room, True)

    def match(self, kws):
        if kws["TouchEvent"] == clientApi.GetMinecraftEnum().TouchEvent.TouchUp:
            if self._selected is not None:
                self._cli.NotifyToServer('G_MATCH', {
                    'pid': clientApi.GetLocalPlayerId(),
                    'court': self._selected
                })
