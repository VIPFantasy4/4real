#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import OrderedDict
from kafka.consumer.fetcher import ConsumerRecord
import kafka
import redis
import asyncio
import concurrent.futures
import functools
import pickle
import duel
import sys
import cfg
import log

import sqlite3

conn = sqlite3.connect('test.db')
conn.execute('DROP TABLE IF EXISTS tbl_test')
conn.execute(
    'CREATE TABLE tbl_test (addr TEXT, status INTEGER, service_id TEXT, duel_id TEXT)')
conn.close()


def mark(addresses, service_id, duel_id):
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    c.executemany('INSERT INTO tbl_test VALUES (?, ?, ?, ?)', [(addr, 1, service_id, duel_id) for addr in addresses])
    conn.commit()
    conn.close()


class Real:
    @classmethod
    def restore(cls, snapshot):
        pass

    def __next__(self):
        self._i += 1
        return str(self._i)

    def __init__(self, _id, topic, pool):
        self._i = 0
        self._id = _id
        self._key = f'{topic}:{_id}'
        self._pool = pool
        self._duels = {}
        self._conns = {}
        self._funcs = {}
        self._topic = topic
        self._redis = redis.StrictRedis(cfg.REDIS_HOST, cfg.REDIS_PORT, cfg.REDIS_DB, cfg.REDIS_PASSWD)
        self._consumer = kafka.KafkaConsumer(
            bootstrap_servers=cfg.KAFKA_SERVERS,
            group_id=topic
        )
        self._consumer.assign([kafka.TopicPartition(topic, _id)])
        self._producer = kafka.KafkaProducer(bootstrap_servers=cfg.KAFKA_SERVERS)

        self._od = OrderedDict()
        self._stock = OrderedDict()
        self._work_queue: asyncio.Queue = None
        self._wait_queue: asyncio.Queue = None

    @property
    def funcs(self):
        return self._funcs

    async def worker(self):
        while True:
            coro = await self._work_queue.get()
            self._work_queue.task_done()

            await coro

    async def leave(self, addr):
        if addr in self._od:
            self._od.pop(addr)

    async def participate(self, addr):
        print(addr)
        self._od[addr] = None
        if len(self._od) > 2:
            await self._wait_queue.put(tuple(self._od.popitem(0)[0] for _ in range(3)))

    async def creator(self):
        while True:
            addresses = await self._wait_queue.get()
            self._wait_queue.task_done()
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self._pool, functools.partial(mark, addresses, self._id, '1'))
            writer = await self.arrange()
            writer.write(pickle.dumps({
                'name': 'participate',
                'args': (addresses,)
            }).hex().encode() + b'.')
            await writer.drain()

    async def arrange(self):
        if self._stock:
            _id, writer = self._stock.popitem()
        else:
            _id = next(self)
            fut = asyncio.get_event_loop().create_future()
            self._duels[_id] = fut
            # asyncio.create_task(self.watcher())
            await asyncio.create_subprocess_exec(
                sys.executable, duel.__file__, _id, stdout=sys.stdout, stderr=sys.stderr)
            writer = await fut
        return writer

    async def watcher(self, subprocess):
        await subprocess.wait()

    async def heartbeat(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        _id = None
        while True:
            try:
                raw = await reader.readuntil(b'.')
                raw = bytes.fromhex(raw[:-1].decode())
            except Exception as e:
                log.error('Exception occurred in heartbeat')
                log.error('%s: %s', e.__class__.__name__, e)
                if _id is not None:
                    self._conns.pop(_id, None)
                    cache = self._duels.pop(_id, None)
                    if cache is not None:
                        pass
                writer.close()
                break
            data = pickle.loads(raw)
            print(len(raw), data)
            if _id is None:
                _id = data[0]
                fut = self._duels.get(_id)
                if fut is not None:
                    fut.set_result(writer)
                self._conns[_id] = reader, writer
            elif not data[1]:
                self._stock[_id] = writer
            else:
                self._producer.send('duel', raw)
            self._duels[_id] = data

    async def consume_forever(self):
        await asyncio.sleep(0)
        while True:
            loop = asyncio.get_running_loop()
            msg = await loop.run_in_executor(self._pool, functools.partial(next, self._consumer))
            if isinstance(msg, ConsumerRecord):
                data = pickle.loads(msg.value)
                if isinstance(data, dict) and data.get('name') in self.funcs:
                    func = self.funcs[data['name']]
                    await self._work_queue.put(func(*data['args']))

    async def snapshot(self):
        snapshot = pickle.dumps(self)
        self._redis.set(self._key, snapshot)
        self._redis.hset(self._topic, self._id, )

    async def main(self):
        self.funcs[self.participate.__name__] = self.participate

        self.funcs[self.rcall.__name__] = self.rcall

        self._work_queue = asyncio.Queue()
        self._wait_queue = asyncio.Queue()

        server = await asyncio.start_server(self.heartbeat, cfg.DUEL_PROXY_HOST, cfg.DUEL_PROXY_PORT)
        addr = server.sockets[0].getsockname()
        log.info(f'Serving on {addr}')

        async with server:
            asyncio.create_task(self.worker())
            asyncio.create_task(self.creator())
            asyncio.create_task(self.consume_forever())
            await server.serve_forever()

    async def rcall(self, _id, data):
        if _id in self._conns:
            writer = self._conns[_id][1]
            writer.write(pickle.dumps(data).hex().encode() + b'.')
            await writer.drain()


if __name__ == '__main__':
    _id, topic = sys.argv[1:]

    with concurrent.futures.ThreadPoolExecutor() as pool:
        asyncio.run(Real(int(_id), topic, pool).main())
