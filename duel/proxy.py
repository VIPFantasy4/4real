# -*- coding: utf-8 -*-

import cfg
import asyncio
import selectors
import socket
import kafka
import pickle

sel = selectors.DefaultSelector()
consumer = kafka.KafkaConsumer(
    *cfg.KAFKA_TOPICS,
    bootstrap_servers=cfg.KAFKA_SERVERS,
    consumer_timeout_ms=1000,
    value_deserializer=pickle.loads
)
producer = kafka.KafkaProducer(bootstrap_servers=cfg.KAFKA_SERVERS, value_serializer=pickle.dumps)
cli_dict = {}


def accept(sock: socket.socket, mask):
    print('accept', sock, mask)
    conn, addr = sock.accept()  # Should be ready
    print('accepted', conn, 'from', addr)
    try:
        conn.setblocking(False)
        cli_dict[addr] = conn
        sel.register(conn, selectors.EVENT_READ, read)
    except Exception as e:
        print(e.__class__.__name__, e)


def read(conn: socket.socket, mask):
    print('read', sock, mask)
    try:
        data = conn.recv(1024)  # Should be ready
        if data:
            print('echoing', repr(data), 'to', conn)
            addr = conn.getpeername()
            print(addr)
            producer.send('duel', {
                'host': addr[0],
                'port': addr[1],
                'data': data
            })
        else:
            print('closing', conn)
            sel.unregister(conn)
            conn.close()
    except Exception as e:
        print(e.__class__.__name__, e)
        sel.unregister(conn)


async def serve(fut):
    while not fut.done():
        events = sel.select(0)
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)
        await asyncio.sleep(1)


async def consume(fut):
    while not fut.done():
        try:
            msg = next(consumer)
            print(msg)
        except StopIteration:
            await asyncio.sleep(1)


async def main():
    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    tasks = [asyncio.create_task(serve(fut)), asyncio.create_task(consume(fut))]
    await fut
    for task in tasks:
        task.cancel()
        await task


sock = socket.socket()
sock.bind(('localhost', 12345))
sock.listen(100)
sock.setblocking(False)
sel.register(sock, selectors.EVENT_READ, accept)
asyncio.run(main())
