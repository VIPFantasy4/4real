# -*- coding: utf-8 -*-

from collections import OrderedDict
import log
import duelcore
import cfg
import asyncio
import pickle
import kafka


class Duel:
    def __init__(self, _id):
        self._id = _id
        self._status = duelcore.WAITING
        self._writer = None  # type: asyncio.StreamWriter
        self._reader = None  # type: asyncio.StreamReader
        self._retry = 0
        self._consumer = kafka.KafkaConsumer(
            *cfg.KAFKA_TOPICS,
            bootstrap_servers=cfg.KAFKA_SERVERS,
            consumer_timeout_ms=1000
        )
        self._producer = kafka.KafkaProducer(bootstrap_servers=cfg.KAFKA_SERVERS)
        self._gamblers = OrderedDict()
        self._chain = duelcore.chain.Chain(self)
        self._queue = asyncio.PriorityQueue()

    @property
    def queue(self):
        return self._queue

    def view(self):
        return self._id, self._status, self._gamblers

    def validate(self):
        if self._status != duelcore.SERVING or len(self._gamblers) != 3:
            return True
        return False

    async def waiter(self, fut: asyncio.Future):
        try:
            await self.queue.put((duelcore.PRIORITY_LEVEL_LOW, await fut))
        except duelcore.DuelRuntimeError as e:
            log.error('%s: %s', e.__class__.__name__, e)

    async def worker(self):
        while True:
            priority_number, coro = await self.queue.get()
            self.queue.task_done()
            if self._status == duelcore.SERVING:
                try:
                    await coro
                except:
                    pass

    def participate(self, addr):
        if self._status == duelcore.WAITING:
            self._gamblers[addr] = duelcore.Gambler(self, addr)
            if len(self._gamblers) > 2:
                self._status = duelcore.SERVING
                fut = asyncio.get_event_loop().create_future()
                asyncio.create_task(self.waiter(fut))
                asyncio.create_task(self.game_start(fut))
            return True
        else:
            log.info('Full room _id: %s participation refused', self._id)
            return False

    async def game_start(self, fut: asyncio.Future):
        if self.validate():
            log.error('Invalid room%s can not start a game right now', self.view())
            self._gamblers.clear()
            self._status = duelcore.WAITING
            fut.set_exception(duelcore.DuelRuntimeError(duelcore.generate_traceback()))
        else:
            self._chain.start_over()
            try:
                await self._chain.duel_start()
                fut.set_result(self.game_over())
            except duelcore.ChainRuntimeError as e:
                self._gamblers.clear()
                self._status = duelcore.WAITING
                fut.set_exception(duelcore.DuelRuntimeError(repr(e)))

    async def game_over(self):
        pass

    async def send(self, data):
        if self._writer:
            try:
                self._writer.write(pickle.dumps(data))
                await self._writer.drain()
            except Exception as e:
                log.error('Exception occurred in send')
                log.error('%s: %s', e.__class__.__name__, e)
        else:
            pass

    async def recv(self):
        if self._reader:
            try:
                data = pickle.loads(await self._reader.readuntil(b'.'))
            except Exception as e:
                log.error('Exception occurred in recv')
                log.error('%s: %s', e.__class__.__name__, e)
        else:
            pass

    async def establish(self):
        if self._retry > 4:
            log.error('Establish failed over 3 times')
            log.error('Destroy the room%s right now', self.view())
            return
        try:
            log.info('Connecting addr: %s', (cfg.DUEL_PROXY_HOST, cfg.DUEL_PROXY_PORT))
            self._reader, self._writer = await asyncio.open_connection(cfg.DUEL_PROXY_HOST, cfg.DUEL_PROXY_PORT)
            log.info('Established addr: %s', (cfg.DUEL_PROXY_HOST, cfg.DUEL_PROXY_PORT))
            self._retry = 0
        except Exception as e:
            log.error('Exception occurred in establish')
            log.error('%s: %s', e.__class__.__name__, e)
            log.error('Retry after 2 seconds')
            await asyncio.sleep(2)
            self._retry += 1
            await self.queue.put((duelcore.PRIORITY_LEVEL_HIGH, self.establish()))

    async def main(self):
        reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
