#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import web

urls = (
    '/', 'Index'
)


class Index:
    def GET(self):
        return 'All Eyez On Me'


if __name__ == "__main__":
    web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
    app = web.application(urls, globals())
    app.run()
