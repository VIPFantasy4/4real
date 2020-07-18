#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import Counter
from email.mime.text import MIMEText
import smtplib
import os
import sqlite3

enum = ('周一', '周二', '周三', '周四', '周五')
pair = {1: '午', 2: '晚'}
order_list = []
demand_mapping = {i: Counter() for i in range(5)}

conn = sqlite3.connect('real.db')
c = conn.cursor()
c.execute('SELECT * FROM real')
row = c.fetchone()
balance = row[0]
if balance < 18:
    print(f'只剩下¥{balance}')
    conn.close()
    exit(0)

for filename in os.listdir('.'):
    if filename != 'real.db' and filename.endswith('.db'):
        db = sqlite3.connect(filename)
        c = db.cursor()
        c.execute("""SELECT * FROM gangsta WHERE _href = NULL ORDER BY _wday, _lunch""")
        rows = c.fetchall()
        db.close()
        for _lame, _order, _wday, _lunch, _ in rows:
            order_list.append({
                '_lame': _lame,
                '_order': _order,
                '_wday': _wday,
                '_lunch': _lunch,
                'db_name': filename
            })
            demand_mapping[_wday].update({_lunch: 1})

y = input('是否发送邮件？')
if y.lower() == 'y':
    demand_text = ''
    for i in range(5):
        for j in (1, 2):
            demand_text += f'{enum[i]} —— {pair[j]} —— {demand_mapping[i].get(j, 0)}份\n'
    server = smtplib.SMTP('smtp.163.com', 25)
    server.set_debuglevel(1)
    server.login('www.lkjlkj@163.com', '12345678961028')
    server.sendmail('www.lkjlkj@163.com', ['www.lkjlkj@163.com'], MIMEText(demand_text, _charset='utf-8').as_string())
    server.quit()

used_href_list = []
for order in order_list:
    if balance < 18:
        print(f'只剩下¥{balance}')
        break
    y = input(f"是否跳过 “{order['_lame']}” —— {enum[order['_wday']]} —— {pair[order['_lunch']]} ？")
    if y.lower() == 'y':
        continue
    print('复制链接到此处')
    _href = input('_href: ')
    db = sqlite3.connect(order['db_name'])
    c = db.cursor()
    try:
        c.execute(
            """UPDATE gangsta SET _href = ? WHERE _lame = ? AND _wday = ? AND _lunch = ? AND _href = NULL""",
            (_href, order['_lame'], order['_wday'], order['_lunch'])
        )
        if c.rowcount:
            balance -= 18
            used_href_list.append(_href)
            db.commit()
            c = conn.cursor()
            c.execute('UPDATE real SET thug = thug - 18 WHERE thug >= 18')
            conn.commit()
            print(f'剩余¥{balance}')
    except:
        db.rollback()
        conn.rollback()
    db.close()
print(f'本次发货{len(used_href_list)}单')
if used_href_list:
    y = input('是否发送邮件？')
    if y.lower() == 'y':
        result_text = ''
        for used_href in used_href_list:
            result_text += f'{used_href}\n'
        server = smtplib.SMTP('smtp.163.com', 25)
        server.set_debuglevel(1)
        server.login('www.lkjlkj@163.com', '12345678961028')
        server.sendmail(
            'www.lkjlkj@163.com',
            ['www.lkjlkj@163.com'], MIMEText(result_text, _charset='utf-8').as_string())
        server.quit()

conn.close()
print('Process finished with exit code 0')
