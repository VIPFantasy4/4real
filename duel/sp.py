#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import log
import cfg
import functools
import concurrent.futures
import asyncio
import pickle
import kafka
import sys


class SP:
    def __init__(self, _id, pool):
        self._id = _id
        self._duels = {}
        self._conns = {}
        self._funcs = {}
        self._consumer = kafka.KafkaConsumer(
            *cfg.KAFKA_TOPICS,
            bootstrap_servers=cfg.KAFKA_SERVERS,
            consumer_timeout_ms=1000
        )
        self._producer = kafka.KafkaProducer(bootstrap_servers=cfg.KAFKA_SERVERS)
        self._pool = pool

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

    async def participate(self, addr):
        pass

    async def heartbeat(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        _id = None
        task = None
        while True:
            try:
                raw = await reader.readuntil(b'.')
                raw = raw[:-1]
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
            data = pickle.loads(bytes.fromhex(raw.decode()))
            if _id is None:
                _id = data['_id']
                self._conns[_id] = (reader, writer)
            elif _id != data['_id']:
                log.error("Even if it's unlikely")
                _id = data['_id']
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
                    try:
                        await func(*data['args'])
                    except Exception as e:
                        log.error(f'Exception occurred in {func}')
                        log.error('%s: %s', e.__class__.__name__, e)

    async def main(self):
        self.funcs[self.participate.__name__] = self.participate
        server = await asyncio.start_server(self.heartbeat, cfg.DUEL_PROXY_HOST, cfg.DUEL_PROXY_PORT)
        addr = server.sockets[0].getsockname()
        print(f'Serving on {addr}')

        async with server:
            asyncio.create_task(self.consume_forever())
            await server.serve_forever()


if __name__ == '__main__':
    _id = sys.argv[1]

    with concurrent.futures.ThreadPoolExecutor() as pool:
        asyncio.run(SP(_id, pool).main())
