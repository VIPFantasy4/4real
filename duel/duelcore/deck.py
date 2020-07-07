# -*- coding: utf-8 -*-

class Deck:
    MAPPING = {
        0: 'JOKER',
        1: '2',
        2: 'A',
        3: 'K',
        4: 'Q',
        5: 'J',
        6: '10',
        7: '9',
        8: '8',
        9: '7',
        10: '6',
        11: '5',
        12: '4',
        13: '3',
    }
    DECK = [(0, 0), (0, 1)] + [(i, j) for i in range(1, 14) for j in range(4)]
