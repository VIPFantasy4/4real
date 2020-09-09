# -*- coding: utf-8 -*-

from collections import OrderedDict
import weakref
import client.extraClientApi as clientApi
import cfg


class Phase(object):
    def __reduce__(self):
        return tuple, ((self.name, self.turn),)

    def __init__(self, name, turn):
        self.name = name
        self.turn = turn

    def __str__(self):
        return 'Phase(%s, %s)' % (self.name, self.turn)

    __repr__ = __str__


class Chain(object):
    def __reduce__(self):
        return tuple, ((self.phase, self.times, self.three, self.track),)

    def __init__(self, duel, phase, times, three, track):
        self.duel = weakref.proxy(duel)
        self.phase = Phase(*phase)
        self.times = times
        self.three = three
        self.track = track

    def __str__(self):
        return 'Chain(%s, %s, %s, %s)' % (
            self.phase, self.times, self.three, '\n'.join(repr(item) for item in self.track))

    __repr__ = __str__


class Gambler(object):
    def __reduce__(self):
        return tuple, (
            (self.addr, sum(map(lambda s: len(s), self.cards.itervalues())), self.role, self.og, self.times, self.bot),)

    def __init__(self, duel, addr, cards, show_hand, role, og, times, bot):
        self.duel = weakref.proxy(duel)
        self.addr = addr
        self.cards = cards
        self.show_hand = show_hand
        self.role = role
        self.og = og
        self.times = times
        self.bot = bot

    def __str__(self):
        return 'Gambler(%s, %s, %s, %s, %s)' % (self.addr, sum(
            map(lambda s: len(s), self.cards.itervalues())), self.role, self.og, self.bot)

    __repr__ = __str__


class Duel(object):
    def __init__(self, _id, status, gamblers, chain):
        self._id = _id
        self._status = status
        od = OrderedDict()
        for args in gamblers:
            gambler = Gambler(self, *args)
            od[gambler.addr] = gambler
        self.gamblers = od
        self.chain = Chain(self, *chain)

    def __str__(self):
        return 'Duel(\n%s,\n%s,\n%s\n)\n' % (self._id, self.gamblers, self.chain)

    __repr__ = __str__


class Cli(clientApi.GetClientSystemCls()):
    def Update(self):
        self._update()

    def Destroy(self):
        self.UnListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), 'UiInitFinished', self,
                              self.initialize)
        self.UnListenForEvent(cfg.MOD_NAMESPACE, cfg.MOD_SRV_NAME, 'G_DEBUT', self, self.debut)

        self._destroy()

    @property
    def real(self):
        return self._real

    @real.setter
    def real(self, real):
        self._real = real
        if self._g:
            self._g.real = real

    def __init__(self, *args):
        super(Cli, self).__init__(*args)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(), 'UiInitFinished', self,
                            self.initialize)
        self.ListenForEvent(cfg.MOD_NAMESPACE, cfg.MOD_SRV_NAME, 'G_DEBUT', self, self.debut)
        self.ListenForEvent(cfg.MOD_NAMESPACE, cfg.MOD_SRV_NAME, 'G_REAL', self, self.debut)

        self._g = None  # type: GUI
        self._debut = False
        self._real = None

    def _update(self):
        pass

    def _destroy(self):
        pass

    def initialize(self, *args):
        clientApi.RegisterUI(cfg.MOD_NAMESPACE, cfg.UI_NAMESPACE, cfg.UI_CLASS, cfg.UI_MAIN)
        self._g = clientApi.CreateUI(cfg.MOD_NAMESPACE, cfg.UI_NAMESPACE, {"isHud": 0})  # type: GUI
        if self._debut and not self._g.debut:
            self._g.debut = True
            self._g.perform()
        else:
            self._g.standby()

    def debut(self, data):
        real = data['real']
        if self.real != real:
            self.real = real
        data.get('')
        if self._g and not self._g.debut:
            self._g.debut = True
            self._g.perform()
        self._debut = True

    def catch_up(self, data):
        pass


class GUI(clientApi.GetScreenNodeCls()):
    def Create(self):
        print 'create gui'

    @property
    def real(self):
        return self.prefix + '/4real'

    @real.setter
    def real(self, real):
        self.SetText(self, real)

    def __init__(self, *args):
        super(GUI, self).__init__(*args)
        self.debut = False
        self.prefix = (
            '/variables_button_mappings_and_controls'
            '/safezone_screen_matrix'
            '/inner_matrix'
            '/safezone_screen_panel'
            '/root_screen_panel'
        )

    def standby(self):
        self.SetVisible(self.real, False)

    def perform(self):
        pass
