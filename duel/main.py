#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import OrderedDict
import log
import cfg
import functools
import concurrent.futures
import asyncio
import pickle
import kafka
import sys

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
    def restore(self):
        pass

    def __init__(self, _id, topic, pool):
        self._id = _id
        self._key = f'{topic}:{_id}'
        self._pool = pool
        self._duels = {}
        self._conns = {}
        self._funcs = {}
        self._consumer = kafka.KafkaConsumer(
            bootstrap_servers=cfg.KAFKA_SERVERS,
            group_id=topic
        )
        self._consumer.assign([kafka.TopicPartition(topic, _id)])
        self._producer = kafka.KafkaProducer(bootstrap_servers=cfg.KAFKA_SERVERS)

        self._od = OrderedDict()
        self._work_queue: asyncio.Queue = None
        self._wait_queue: asyncio.Queue = None

    @property
    def funcs(self):
        return self._funcs

    def publish(self, topic, value=None, key=None, headers=None, partition=None, timestamp_ms=None):
        try:
            self._producer.send(topic, value, key, headers, partition, timestamp_ms)
        except Exception as e:
            log.error('Exception occurred in publish')
            log.error('%s: %s', e.__class__.__name__, e)

    def fetch(self):
        try:
            return next(self._consumer)
        except StopIteration:
            if self._consumer._closed:
                log.error('Met a closed KafkaConsumer while fetching')

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
            writer = self._conns['1'][1]
            writer.write(pickle.dumps({
                'name': 'participate',
                'args': (addresses,)
            }).hex().encode() + b'.')
            await writer.drain()

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
                self._conns[_id] = (reader, writer)
            elif _id != data[0]:
                log.error("Even if it's unlikely")
                _id = data[0]
            self._duels[_id] = data
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self._pool, functools.partial(self.publish, 'duel', raw))

    async def consume_forever(self):
        await asyncio.sleep(0)
        while True:
            loop = asyncio.get_running_loop()
            msg = await loop.run_in_executor(self._pool, self.fetch)
            if msg.__class__.__name__ == 'ConsumerRecord':
                data = pickle.loads(msg.value)
                if isinstance(data, dict) and data.get('name') in self.funcs:
                    func = self.funcs[data['name']]
                    # try:
                    #     await func(*data['args'])
                    # except Exception as e:
                    #     log.error(f'Exception occurred in {func}')
                    #     log.error('%s: %s', e.__class__.__name__, e)
                    await self._work_queue.put(func(*data['args']))

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
        asyncio.run(Real(_id, topic, pool).main())
