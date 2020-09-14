# -*- coding: utf-8 -*-

from collections import OrderedDict
from Queue import Queue, Empty
import apolloCommon.workerPool as workerPool
import lobbyGame.netgameApi as onlineApi
import server.extraServerApi as serverApi
import pickle
import kafka
import cfg

KAFKA_SERVERS = [
    '122.51.140.131:9092',
]


class Phase(object):
    def __init__(self, name, turn):
        self.name = name
        self.turn = turn


class Chain(object):
    def __init__(self, duel, phase, times, three, track):
        self.duel = duel
        self.phase = Phase(*phase)
        self.times = times
        self.three = three
        self.track = track


class Gambler(object):
    def __init__(self, duel, addr, cards, show_hand, role, og, times, bot):
        self.duel = duel
        self.addr = addr
        self.cards = cards
        self.show_hand = show_hand
        self.role = role
        self.og = og
        self.times = times
        self.bot = bot


class Duel(object):
    def regress(self, addr):
        return addr, self._status, [
            gambler.addr == addr and (
                gambler.addr,
                sorted(reduce(lambda x, y: x + y, map(lambda s: tuple(s), gambler.cards.itervalues()))),
                gambler.show_hand, gambler.role, gambler.og, gambler.times, gambler.bot
            ) or (
                gambler.addr, sum(map(lambda s: len(s), gambler.cards.itervalues())),
                gambler.show_hand, gambler.role, gambler.og, gambler.times, gambler.bot
            ) for gambler in self.gamblers.itervalues()
        ], ((self.chain.phase.name, self.chain.phase.turn), self.chain.times, self.chain.three, self.chain.track)

    def __init__(self, _id, status, gamblers, chain):
        self._id = _id
        self._status = status
        od = OrderedDict()
        for args in gamblers:
            gambler = Gambler(self, *args)
            od[gambler.addr] = gambler
        self.gamblers = od
        self.chain = Chain(self, *chain)


class Srv(serverApi.GetServerSystemCls()):
    def Update(self):
        self._update()

    def Destroy(self):
        self.UnListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), 'AddServerPlayerEvent',
                              self, self.connection_made)
        self.UnListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(),
                              'LoadServerAddonScriptsAfter', self, self.serve_forever)
        self.UnListenForEvent(cfg.MOD_NAMESPACE, cfg.MOD_CLI_NAME, 'G_DEBUT', self, self.debut)
        self.UnListenForEvent(cfg.MOD_NAMESPACE, cfg.MOD_CLI_NAME, 'G_MATCH', self, self.match)
        self.UnListenForEvent(cfg.MOD_NAMESPACE, cfg.MOD_CLI_NAME, 'G_COURT', self, self.rcall)

        self._destroy()

    def __init__(self, *args):
        super(Srv, self).__init__(*args)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), 'AddServerPlayerEvent',
                            self, self.connection_made)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(),
                            'LoadServerAddonScriptsAfter', self, self.serve_forever)
        self.ListenForEvent(cfg.MOD_NAMESPACE, cfg.MOD_CLI_NAME, 'G_DEBUT', self, self.debut)
        self.ListenForEvent(cfg.MOD_NAMESPACE, cfg.MOD_CLI_NAME, 'G_MATCH', self, self.match)
        self.ListenForEvent(cfg.MOD_NAMESPACE, cfg.MOD_CLI_NAME, 'G_COURT', self, self.rcall)

        self._mapping = {}
        self._q = Queue()
        self._alive = True
        self._consumer = kafka.KafkaConsumer(
            'duel',
            bootstrap_servers=KAFKA_SERVERS,
            consumer_timeout_ms=1000,
            value_deserializer=pickle.loads
        )
        self._producer = kafka.KafkaProducer(bootstrap_servers=KAFKA_SERVERS, value_serializer=pickle.dumps)

    def _update(self):
        self.process_forever()

    def _destroy(self):
        self._alive = False

    def serve_forever(self, *args):
        pool = workerPool.ForkNewPool(1)
        pool.EmitOrder(self.consume_forever.__name__, self.consume_forever, lambda *args: None)

    def consume_forever(self):
        consumer = self._consumer
        while self._alive:
            try:
                msg = next(consumer)
            except StopIteration:
                continue
            self._q.put(msg.value)

    def process_forever(self):
        if self._alive:
            try:
                data = self._q.get_nowait()
                duel = None
                for args in data[2]:
                    addr = args[0]
                    pid = onlineApi.GetPlayerIdByUid(addr)
                    if pid:
                        if duel is None:
                            duel = Duel(*data)
                        self._mapping[addr] = duel._id
                        self.NotifyToClient(pid, 'G_COURT', {'args': duel.regress(addr)})
            except Empty:
                pass

    def connection_made(self, data):
        uid = onlineApi.GetPlayerUid(data.get('id'))
        if not uid:
            return

    def debut(self, data):
        self.NotifyToClient(data['pid'], 'G_DEBUT', {
            'info': {
                'real': '-996',
                'name': '飞爹',
                'rank': "textures/ui/w3h1",
                'icon': "textures/ui/Steve"
            }
        })

    def match(self, data):
        uid = onlineApi.GetPlayerUid(data['pid'])
        if not uid:
            return
        print data['court']
        producer = self._producer
        producer.send('cli', {
            'name': 'participate',
            'args': (uid,)
        })

    def rcall(self, data):
        uid = onlineApi.GetPlayerUid(data['pid'])
        if not uid:
            return
        if uid in self._mapping:
            _id = self._mapping[uid]
            if data['name'] == 'play':
                cards = data['args'][0]
                if cards:
                    for v in cards.itervalues():
                        for i in xrange(len(v)):
                            v[i] = tuple(v[i])
            args = (_id, {
                'name': data['name'],
                'args': (uid,) + tuple(data['args'])
            })
            producer = self._producer
            producer.send('cli', {
                'name': 'rcall',
                'args': args
            })
