import logging
import os
import requests

from flask import Flask, request
from threading import Thread
from uuid import uuid4 as uuid


class Webserver(object):
    def __init__(self, host, port):
        self.log = logging.getLogger(type(self).__name__)
        template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')
        self.log.debug("Using template path: %s", template_path)
        self.app = Flask(__name__, template_folder=template_path)
        self.host = host
        self.port = port
        self.running = False
        self.shutdown_code = uuid().hex
        self.thread = None

    def start(self):
        self.app.debug = False
        webserver_args = {
            'host': self.host,
            'port': self.port,
            'threaded': True,
        }
        self.thread = Thread(target=self.app.run, kwargs=webserver_args)
        self.thread.start()
        self.running = True

        @self.app.route('/_/shutdown', methods=['POST'])
        def shutdown():
            code = request.form.get('code')
            if code == self.shutdown_code:
                self.log.warn("Shutdown code received.  Stopping webserver...")
                request.environ.get('werkzeug.server.shutdown')()
                self.running = False
            return ''

        @self.app.template_filter()
        def pluralize(val, str, suffix='s'):
            if val != 1:
                str += suffix
            return '%d %s' % (val, str)

    def stop(self):
        if self.running:
            requests.post('http://localhost:%d/_/shutdown' % self.port, data={'code': self.shutdown_code})
            self.thread.join()
