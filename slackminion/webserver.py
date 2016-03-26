from bottle import app
from rocket import Rocket


class Webserver(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.webserver = None

    def start(self):
        interfaces = [(self.host, self.port)]
        self.webserver = Rocket(interfaces=interfaces, app_info={'wsgi_app': app()}, handle_signals=False)
        self.webserver.start(background=True)

    def stop(self):
        if self.webserver is not None:
            self.webserver.stop()
