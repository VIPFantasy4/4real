#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cfg
import asyncio


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
    server = await asyncio.start_server(handle_echo, cfg.DUEL_PROXY_HOST, cfg.DUEL_PROXY_PORT)
    print(server.sockets)
    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()


asyncio.run(main())
