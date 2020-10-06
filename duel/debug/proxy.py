# -*- coding: utf-8 -*-

from collections import OrderedDict
import cfg
import threading
import asyncore
import socket
import kafka
import pickle
import weakref
import pprint


class Phase(object):
    def __reduce__(self):
        return tuple, ((self.name, self.turn),)

    def __init__(self, name, turn):
        self.name = name
        self.turn = turn

    def __str__(self):
        return 'Phase(%s, %s)' % (self.name, self.turn)

    __repr__ = __str__


class Chain(object):
    def __reduce__(self):
        return tuple, ((self.phase, self.times, self.three, self.track),)

    def __init__(self, duel, phase, times, three, track):
        self.duel = weakref.proxy(duel)
        self.phase = Phase(*phase)
        self.times = times
        self.three = three
        self.track = track

    def __str__(self):
        return 'Chain(%s, %s, %s, %s)' % (self.phase, self.times, self.three, '\n'.join(repr(item) for item in self.track))

    __repr__ = __str__


class Gambler(object):
    def __reduce__(self):
        return tuple, ((self.addr, sum(map(lambda s: len(s), self.cards.itervalues())), self.role, self.og, self.times, self.bot),)

    def __init__(self, duel, addr, cards, show_hand, role, og, times, bot):
        self.duel = weakref.proxy(duel)
        self.addr = addr
        self.cards = cards
        self.show_hand = show_hand
        self.role = role
        self.og = og
        self.times = times
        self.bot = bot

    def __str__(self):
        return 'Gambler(%s, %s, %s, %s, %s)' % (self.addr, sum(
            map(lambda s: len(s), self.cards.itervalues())), self.role, self.og, self.bot)

    __repr__ = __str__


class Duel(object):
    def __init__(self, _id, status, gamblers, chain):
        self._id = _id
        self._status = status
        od = OrderedDict()
        for args in gamblers:
            gambler = Gambler(self, *args)
            od[gambler.addr] = gambler
        self.gamblers = od
        self.chain = Chain(self, *chain)

    def __str__(self):
        return 'Duel(\n%s,\n%s,\n%s\n)\n' % (self._id, self.gamblers, self.chain)

    __repr__ = __str__


duels = {}
conns = {}
consumer = kafka.KafkaConsumer(
    'duel',
    bootstrap_servers=cfg.KAFKA_SERVERS,
    consumer_timeout_ms=1000,
    value_deserializer=pickle.loads
)
producer = kafka.KafkaProducer(bootstrap_servers=cfg.KAFKA_SERVERS, value_serializer=pickle.dumps)


def consume_forever():
    while True:
        try:
            msg = next(consumer)
        except StopIteration:
            continue
        data = msg.value
        duel = None
        for args in data[2]:
            addr = args[0]
            if addr in conns:
                if duel is None:
                    duel = Duel(*data)
                    pprint.pprint(duel)
                    duels[duel._id] = duel
                    data = {
                        'args': pickle.dumps((duel._id, duel.gamblers, duel.chain), 2)
                    }
                data['cards'] = duel.gamblers[addr].cards
                conns[addr].send(pickle.dumps(data, 2).encode('hex') + '.')


t = threading.Thread(target=consume_forever)
t.setDaemon(True)
t.start()


class ConnHandler(asyncore.dispatcher_with_send):
    def __init__(self, *args):
        asyncore.dispatcher_with_send.__init__(self, *args)
        self.in_buffer = ''

    def handle_read(self):
        self.in_buffer += self.recv(8192)
        if '.' in self.in_buffer:
            raw, self.in_buffer = self.in_buffer.split('.')[-2:]
            data = pickle.loads(raw.decode('hex'))
            if 'name' in data and 'args' in data:
                producer.send('rookie0', data)

    def handle_close(self):
        print('conn from %s lost' % repr(self.addr))
        conns.pop(repr(self.addr), None)
        asyncore.dispatcher_with_send.handle_close(self)


class CP(asyncore.dispatcher):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(100)

    def handle_accept(self):
        pair = self.accept()
        if pair:
            sock, addr = pair
            print('Incoming connection from %s' % repr(addr))
            handler = ConnHandler(sock)
            conns[repr(addr)] = handler


server = CP('localhost', 44520)
asyncore.loop()
