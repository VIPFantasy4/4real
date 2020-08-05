# -*- coding: utf-8 -*-

from collections import OrderedDict
import log
import duelcore
import cfg
import asyncio
import pickle


class Duel:
    def __init__(self, _id):
        self._id = _id
        self._status = duelcore.WAITING
        self._reader: asyncio.StreamReader = None
        self._writer: asyncio.StreamWriter = None
        self._retry = 0
        self._queue = asyncio.PriorityQueue()
        self._funcs = {}
        self._chain = duelcore.chain.Chain(self)
        self._gamblers = OrderedDict()

    @property
    def queue(self):
        return self._queue

    def view(self):
        return self._id, self._status, self._gamblers

    def validate(self):
        if self._status == duelcore.SERVING and len(self._gamblers) == 3:
            return True
        return False

    async def heartbeat(self):
        await self.send({
            '_id': self._id,
            'addrs': tuple(self._gamblers.keys()),
            'args': pickle.dumps((self._id, self._status, self._gamblers, self._chain), 2)
        })

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
            self._chain.start_over()
            try:
                await self._chain.duel_start()
                fut.set_result(self.game_over())
            except duelcore.ChainRuntimeError as e:
                self._gamblers.clear()
                self._status = duelcore.WAITING
                fut.set_exception(duelcore.DuelRuntimeError(repr(e)))
        else:
            log.error('Invalid room%s can not start a game right now', self.view())
            self._gamblers.clear()
            self._status = duelcore.WAITING
            fut.set_exception(duelcore.DuelRuntimeError(duelcore.generate_traceback()))

    async def game_over(self):
        pass

    async def send(self, data):
        if self._writer:
            try:
                self._writer.write(pickle.dumps(data, 2).hex().encode() + b'.')
                await self._writer.drain()
            except Exception as e:
                log.error('Exception occurred in send')
                log.error('%s: %s', e.__class__.__name__, e)
        else:
            pass

    async def recv(self):
        if self._reader:
            try:
                data = await self._reader.readuntil(b'.')
            except Exception as e:
                log.error('Exception occurred in recv')
                log.error('%s: %s', e.__class__.__name__, e)
                self._writer.close()
                return
            data = pickle.loads(bytes.fromhex(data[:-1].decode()))
        else:
            pass

    async def establish(self):
        if self._retry > 4:
            log.error('Establish failed over 4 times')
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
