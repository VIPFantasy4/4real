# -*- coding: utf-8 -*-

import asyncio


async def tcp_echo_client(message):
    reader, writer = await asyncio.open_connection('127.0.0.1', 12345)

    while True:
        print(f'Send: {message!r}')
        writer.write(message.encode())
        await writer.drain()

        data = await reader.read(100)
        print(f'Received: {data.decode()!r}')


async def loop():
    while True:
        print(1)
        await asyncio.sleep(2)


async def main():
    task = asyncio.create_task(loop())
    asyncio.create_task(tcp_echo_client('Hello World!'))
    await task


asyncio.run(main())
