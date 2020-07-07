# -*- coding: utf-8 -*-

import asyncio
import socket

CLIENTS = {}

sock = socket.socket()
sock.bind(('127.0.0.1', 12345))
sock.listen(100)
client = socket.socket()
client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
client.connect(('127.0.0.1', 12345))


async def _recv(conn):
    return conn.recv(1024)

async def recv(conn: socket.socket, addr):
    while True:
        data = await _recv(conn)
        print(f'recv {data} from {addr}')
        conn.send(data)


async def _accept():
    return sock.accept()


async def accept():
    while True:
        conn, addr = await _accept()
        CLIENTS[addr] = conn
        conn.send(b'loop')
        task = asyncio.create_task(recv(conn, addr))
        await task


async def send():
    while True:
        data = await _recv(client)
        print('send', data)
        client.send(data)

async def forever():
    while 1:
        await asyncio.sleep(2)
        print(1)

async def tt():
    await asyncio.sleep(10)

async def main():
    asyncio.open_connection
    task1 = asyncio.create_task(forever())
    print(666666666666666666666666)
    await tt()
    # task2 = asyncio.create_task(send())




asyncio.run(main())
