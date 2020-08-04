#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import log
import cfg
import functools
import concurrent.futures
import asyncio
import pickle
import kafka


class SP:
    def __init__(self, _id):
        self._id = _id
        self._duels = {}
        self._consumer = kafka.KafkaConsumer(
            *cfg.KAFKA_TOPICS,
            bootstrap_servers=cfg.KAFKA_SERVERS,
            consumer_timeout_ms=1000
        )
        self._producer = kafka.KafkaProducer(bootstrap_servers=cfg.KAFKA_SERVERS)
        self._queue = asyncio.PriorityQueue()

    def publish(self, topic, value=None, key=None, headers=None, partition=None, timestamp_ms=None):
        try:
            self._producer.send(topic, value, key, headers, partition, timestamp_ms)
        except Exception as e:
            log.error('Exception occurred in publish')
            log.error('%s: %s', e.__class__.__name__, e)

    async def heartbeat(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        _id = None
        while True:
            try:
                raw = await reader.readuntil(b'.')
                raw = raw[:-1]
            except Exception as e:
                log.error('Exception occurred in heartbeat')
                log.error('%s: %s', e.__class__.__name__, e)
                if _id is not None:
                    cache = self._duels.pop(_id, None)
                    if cache is not None:
                        pass
                writer.close()
                break
            data = pickle.loads(bytes.fromhex(raw.decode()))
            if _id is None:
                _id = data['_id']
            elif _id != data['_id']:
                log.error("Even if it's unlikely")
                _id = data['_id']
            self._duels[_id] = data
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                await loop.run_in_executor(pool, functools.partial(self.publish, 'duel', raw))

    async def main(self):
        server = await asyncio.start_server(self.heartbeat, cfg.DUEL_PROXY_HOST, cfg.DUEL_PROXY_PORT)
        addr = server.sockets[0].getsockname()
        print(f'Serving on {addr}')

        async with server:
            await server.serve_forever()

async def handle_echo(reader, writer):
    data = await reader.read(100)
    message = data.decode()
    addr = writer.get_extra_info('peername')

    print(f"Received {message!r} from {addr!r}")

    print(f"Send: {message!r}")
    writer.write(data)
    await writer.drain()

    # print("Close the connection")
    # writer.close()


async def main():
    server = await asyncio.start_server(self.heartbeat, cfg.DUEL_PROXY_HOST, cfg.DUEL_PROXY_PORT)
    print(server.sockets)
    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()


asyncio.run(main())
