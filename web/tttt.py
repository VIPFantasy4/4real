#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import inspect
import web

urls = ("/", "testme")

app = web.application(urls, globals())

# Session/debug tweak from http://webpy.org/cookbook/session_with_reloader



# session = web.session.Session(app, web.session.DiskStore('sessions'))


def csrf_token():
    """Should be called from the form page's template:
       <form method=post action="">
         <input type=hidden name=csrf_token value="$csrf_token()">
         ...
       </form>"""

    if 'csrf_token' not in web.config._session:
        from uuid import uuid4
        web.config._session.csrf_token = uuid4().hex
    return web.config._session.csrf_token


def csrf_protected(f):
    """Usage:
       @csrf_protected
       def POST(self):
           ..."""

    def decorated(*args, **kwargs):
        inp = web.input()
        if not ('csrf_token' in inp and inp.csrf_token == web.config._session.csrf_token):
            raise web.HTTPError(
                "400 Bad request",
                {'content-type': 'text/html'},
                'Cross-site request forgery (CSRF) attempt (or stale browser form). <a href="">Back to the form</a>.')

        return f(*args, **kwargs)

    return decorated


# Note: in order to let templates use csrf_token, you need to add it to render's globals
render = web.template.render('templates/', globals={'csrf_token': csrf_token})


class testme:
    def GET(self):
        return render.index({  # I know it's not customary to pass a dict, but it's neater IMHO
            'title': 'WebPy CSRF example',
            'veteran': False,
            'message': web.config._session.get('message')})

    @csrf_protected
    def POST(self):
        web.config._session.message = web.input().message
        web.config._session.status = 'Updated message'
        return render.index({  # I know it's not customary to pass a dict, but it's neater IMHO
            'title': 'Message updated',
            'veteran': True,
            'message': web.config._session.get('message')})


if __name__ == "__main__":
    if web.config.get('_session') is None:
        session = web.session.Session(app, web.session.DiskStore('sessions'))
        web.config._session = session
    else:
        session = web.config._session
    app.run()
