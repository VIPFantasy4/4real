#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from uuid import uuid4
import web
import db

URLS = (
    '/', 'Index',
)
RENDER = render = web.template.render(
    'templates/', globals={'csrf_token': lambda: web.config._session.setdefault('csrf_token', uuid4().hex)})


class Index:
    def login(self, rows):
        output
        return render.index('All Eyez On Me')

    def GET(self):
        if 'username' in web.config._session:
            return self.login(db.select_all(web.config._session.username))
        return render.index('All Eyez On Me')

    def POST(self):
        _input = web.input()
        if 'csrf_token' not in _input or _input.csrf_token != web.config._session.get('csrf_token'):
            raise web.HTTPError(
                "400 Bad request",
                {'Content-Type': 'text/html'},
                'Cross-site request forgery (CSRF) attempt (or stale browser form).')
        username = _input.username.strip()
        if not username:
            return render.index()
        web.config._session.username = username
        db.select_all(username)


if __name__ == "__main__":
    # web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
    web.config.session_parameters['ignore_change_ip'] = False
    app = web.application(URLS, globals())
    web.config._session = web.session.Session(app, web.session.DiskStore('sessions'))
    app.run()
