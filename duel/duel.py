# -*- coding: utf-8 -*-

from collections import OrderedDict
import log
import duelcore
import cfg
import asyncio
import pickle
import sys


class Duel:
    def __init__(self, _id):
        self._id = _id
        self._status = duelcore.WAITING
        self._reader: asyncio.StreamReader = None
        self._writer: asyncio.StreamWriter = None
        self._dirty = False
        self._retry = 0
        self._queue = None
        self._funcs = {}
        self._chain = duelcore.chain.Chain(self)
        self._gamblers = OrderedDict()

    @property
    def queue(self):
        return self._queue

    @property
    def funcs(self):
        return self._funcs

    def view(self):
        return self._id, self._status, self._gamblers

    def validate(self):
        if self._status == duelcore.SERVING and len(self._gamblers) == 3:
            return True
        return False

    async def heartbeat(self):
        await self.send((
            self._id,
            self._status,
            tuple(gambler.regress() for gambler in self._gamblers.values()),
            self._chain.regress()
        ))

    async def waiter(self, fut: asyncio.Future):
        try:
            await self.queue.put((duelcore.PRIORITY_LEVEL_LOW, await fut))
        except duelcore.DuelRuntimeError as e:
            log.error('%s: %s', e.__class__.__name__, e)

    async def worker(self):
        while True:
            priority_number, coro = await self.queue.get()
            self.queue.task_done()

            await coro

    async def participate(self, addresses):
        if self._status == duelcore.WAITING:
            self._gamblers.clear()
            for addr in addresses:
                self._gamblers[addr] = duelcore.Gambler(self, addr)
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
            self._chain.start_over(duelcore.BASE_TIMES)
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
        self._gamblers.clear()
        self._status = duelcore.WAITING

    async def send(self, data):
        try:
            self._writer.write(pickle.dumps(data, 2).hex().encode() + b'.')
            await self._writer.drain()
        except Exception as e:
            log.error('Exception occurred in send')
            log.error('%s: %s', e.__class__.__name__, e)

    async def recv(self):
        await asyncio.sleep(0)
        while True:
            try:
                data = await self._reader.readuntil(b'.')
            except Exception as e:
                log.error('Exception occurred in recv')
                log.error('%s: %s', e.__class__.__name__, e)
                self._writer.close()
                await self.queue.put((duelcore.PRIORITY_LEVEL_HIGH, self.establish()))
                break
            data = pickle.loads(bytes.fromhex(data[:-1].decode()))
            if isinstance(data, dict) and data.get('name') in self.funcs:
                func = self.funcs[data['name']]
                # try:
                #     func(*data['args'])
                # except Exception as e:
                #     log.error(f'Exception occurred in {func}')
                #     log.error('%s: %s', e.__class__.__name__, e)
                await self.queue.put((duelcore.PRIORITY_LEVEL_LOW, func(*data['args'])))

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
            await self.heartbeat()
            asyncio.create_task(self.recv())
        except Exception as e:
            log.error('Exception occurred in establish')
            log.error('%s: %s', e.__class__.__name__, e)
            log.error('Retry after 2 seconds')
            await asyncio.sleep(2)
            self._retry += 1
            await self.queue.put((duelcore.PRIORITY_LEVEL_HIGH, self.establish()))

    async def main(self):
        self.funcs[self.participate.__name__] = self.participate
        self._queue = asyncio.PriorityQueue()
        await self.queue.put((duelcore.PRIORITY_LEVEL_HIGH, self.establish()))
        await self.worker()


if __name__ == '__main__':
    _id = sys.argv[1]

    asyncio.run(Duel(_id).main())
