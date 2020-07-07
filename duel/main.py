# -*- coding: utf-8 -*-

import log
import duelcore
import cfg
import asyncio
import kafka


class Duel:
    def __init__(self, _id):
        self._id = _id
        self._status = duelcore.WAITING
        self._consumer = kafka.KafkaConsumer(
            *cfg.KAFKA_TOPICS,
            bootstrap_servers=cfg.KAFKA_SERVERS,
            consumer_timeout_ms=1000
        )
        self._producer = kafka.KafkaProducer(bootstrap_servers=cfg.KAFKA_SERVERS)
        self._gamblers = {}
        self._chain = duelcore.chain.Chain(self)
        self._queue = asyncio.Queue()

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
            await self.queue.put(await fut)
        except duelcore.DuelRuntimeError as e:
            log.error('%s: %s', e.__class__.__name__, e)

    async def worker(self):
        while True:
            coro = await self.queue.get()
            if self._status == duelcore.SERVING:
                try:
                    await coro
                    self.queue.task_done()
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
