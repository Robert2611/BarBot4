#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import time
import threading
import json
import urllib
from threading import Thread
from wsgiref.simple_server import make_server
from wsgiref.simple_server import WSGIRequestHandler


class server(Thread):
    def __init__(self, OnRequest, port=5555, ip="localhost"):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.OnRequest = OnRequest

    def app(self, environ, start_response):
        status = '200 OK'
        headers = [
            ('Content-Type', 'text/plain; charset=utf-8'),
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Headers', 'X-Requested-With'),
            ("Access-Control-Allow-Credentials", "true")
        ]
        start_response(status, headers)
        if environ['REQUEST_METHOD'] == 'POST':
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            request_body = environ['wsgi.input'].read(request_body_size)
            d = urllib.parse.parse_qs(request_body.decode(
                "utf-8"))  # turns the qs to a dict
            res = self.processRequest(d)
            #print("-" * 10)
            # print(d)
            # print(res)
            if res == None:
                res = ""
            return [json.dumps(res).encode("utf-8")]
        else:
            return ["".encode("utf-8")]

    def run(self):
        #  Create and open the socket will be listening on
        def app(environ, start_response):
            return self.app(environ, start_response)
        self.httpd = make_server(
            self.ip, self.port, app, handler_class=NoLoggingWSGIRequestHandler)
        self.httpd.serve_forever()

    def processRequest(self, data):
        action = data.get("action")
        if action == None:
            return {"error": "no_action_set"}
        return self.OnRequest(action[0], data)

# custom logging class to prevent output on stdout


class NoLoggingWSGIRequestHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass
