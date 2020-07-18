#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import hashlib
import sqlite3


def no_balance():
    path = os.path.join(os.path.dirname(__file__), 'db', 'real.db')
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute('SELECT * FROM real')
    row = c.fetchone()
    conn.close()
    return row[0]


def select_all(username: str):
    path = os.path.join(os.path.dirname(__file__), 'db', f'{hashlib.md5(username.encode()).hexdigest()}.db')
    if os.path.exists(path):
        conn = sqlite3.connect(path)
        c = conn.cursor()
        c.execute("""SELECT * FROM gangsta ORDER BY _wday, _lunch""")
        rows = c.fetchall()
        conn.close()
        return rows
    return ()


def insert_one(mapping: dict):
    username = mapping['_lame']
    path = os.path.join(os.path.dirname(__file__), 'db', f'{hashlib.md5(username.encode()).hexdigest()}.db')
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS gangsta (
            _lame TEXT,
            _order TEXT,
            _wday INTEGER,
            _lunch INTEGER,
            _href TEXT DEFAULT NULL,
            PRIMARY KEY (_wday, _lunch)
        )
    """)
    try:
        c.execute(
            """INSERT INTO gangsta (_lame, _order, _wday, _lunch) VALUES (:_lame, :_order, :_wday, :_lunch)""", mapping)
        conn.commit()
    except:
        conn.rollback()
    conn.close()
