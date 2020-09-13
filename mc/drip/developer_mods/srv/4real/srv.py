# -*- coding: utf-8 -*-

from Queue import Queue, Empty
import apolloCommon.workerPool as workerPool
import lobbyGame.netgameApi as onlineApi
import server.extraServerApi as serverApi
import pickle
import kafka
import cfg

KAFKA_TOPICS = [
    'cli',
]
KAFKA_SERVERS = [
    '122.51.140.131:9092',
]


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
        self.UnListenForEvent(cfg.MOD_NAMESPACE, cfg.MOD_CLI_NAME, 'G_COURT', self, self.catch_up)

        self._destroy()

    def __init__(self, *args):
        super(Srv, self).__init__(*args)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), 'AddServerPlayerEvent',
                            self, self.connection_made)
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(),
                            'LoadServerAddonScriptsAfter', self, self.serve_forever)
        self.ListenForEvent(cfg.MOD_NAMESPACE, cfg.MOD_CLI_NAME, 'G_DEBUT', self, self.debut)
        self.ListenForEvent(cfg.MOD_NAMESPACE, cfg.MOD_CLI_NAME, 'G_MATCH', self, self.match)
        self.ListenForEvent(cfg.MOD_NAMESPACE, cfg.MOD_CLI_NAME, 'G_COURT', self, self.catch_up)

        self._q = Queue()
        self._alive = True
        self._consumer = kafka.KafkaConsumer(
            'duel',
            bootstrap_servers=KAFKA_SERVERS,
            consumer_timeout_ms=1000,
            value_deserializer=pickle.loads
        )

    def _update(self):
        pass

    def _destroy(self):
        self._alive = False

    def serve_forever(self, *args):
        pool = workerPool.ForkNewPool(4)
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
                        self.NotifyToClient(pid, 'G_COURT', {'args': []})
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
