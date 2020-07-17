#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from uuid import uuid4
import web
import db

web.config.debug = False
URLS = (
    '/', 'Index',
)
RENDER = render = web.template.render(
    'templates/', globals={'csrf_token': lambda: web.config._session.setdefault('csrf_token', uuid4().hex)})


class Index:
    def GET(self):
        if 'username' in web.config._session:
            return render.index(db.select_all(web.config._session.username))
        return render.index(None)

    def POST(self):
        _input = web.input()
        if 'csrf_token' not in _input or _input.csrf_token != web.config._session.get('csrf_token'):
            raise web.HTTPError(
                "400 Bad request",
                {'Content-Type': 'text/html'},
                'Cross-site request forgery (CSRF) attempt (or stale browser form).')
        if 'order' in _input:
            try:
                username = web.config._session.username
            except:
                return render.index(None)
            try:
                db.insert_one({
                    'username': username,
                    '_order': '牛肉粉',
                    '_wday': int(_input._wday),
                    '_lunch': int(_input._lunch)
                })
            except:
                pass
            return render.index(db.select_all(username))
        else:
            username = _input.username.strip()
            if not username:
                return render.index(None)
            web.config._session.username = username
            return render.index(db.select_all(username))


if __name__ == "__main__":
    # web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
    web.config.session_parameters['ignore_change_ip'] = False
    app = web.application(URLS, globals())
    web.config._session = web.session.Session(app, web.session.DiskStore('sessions'))
    app.run()
