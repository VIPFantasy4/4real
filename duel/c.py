# -*- coding: utf-8 -*-

import threading, asyncore, socket, pickle, pprint


class C(asyncore.dispatcher_with_send):
    def __init__(self, host, port):
        asyncore.dispatcher_with_send.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self.in_buffer = ''

    def handle_read(self):
        self.in_buffer += self.recv(8192)
        if '.' in self.in_buffer:
            raw, self.in_buffer = self.in_buffer.split('.')[-2:]
            data = pickle.loads(raw.decode('hex'))
            pprint.pprint(data)


client = C('localhost', 44520)


def req():
    while client:
        print('请输入你想干什么：')
        print('输入 1 加入一局游戏')
        try:
            option = int(raw_input('请输入：'))
        except ValueError:
            print('无效输入')
            continue
        if option == 1:
            client.send(pickle.dumps({
                'name': 'participate',
                'args': (repr(client.socket.getsockname()),)
            }, 2).encode('hex') + '.')
            print('已发起请求')


t = threading.Thread(target=req)
t.setDaemon(True)
t.start()

asyncore.loop()
