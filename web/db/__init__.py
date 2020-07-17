#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import sqlite3


def select_all(username):
    path = os.path.join(os.path.dirname(__file__), 'db', f'{username}.db')
    if os.path.exists(path):
        conn = sqlite3.connect(path)
        c = conn.cursor()
        c.execute("""SELECT * FROM gangsta""")
        return c.fetchall()


# conn = sqlite3.connect('gang.db')
# c = conn.cursor()
# c.execute("""
#     CREATE TABLE IF NOT EXISTS gang (
#         _gangsta TEXT,
#         _order TEXT,
#         _date TEXT,
#         _noon INTEGER,
#         _href TEXT DEFAULT NULL,
#         PRIMARY KEY (_gangsta, _date, _noon)
#     )
# """)
#
# c.executemany('INSERT INTO gang (_gangsta, _order, _date, _noon) VALUES (?, ?, ?, ?)', [
#     (3, '背景', 'asdas', 1), (3, '背景', 'asdas', 2)])
# sqlite3.IntegrityError
# conn.commit()
# conn.close()
