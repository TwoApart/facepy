#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cgi
import json
import sys
import time

from BaseHTTPServer import (
    HTTPServer,
    BaseHTTPRequestHandler as BaseRequestHandler,
)

from facepy import SubscriptionsAPI


def handle(handler):
    def do_handler(self, **kwargs):
        try:
            http_code, \
            http_content, \
            http_content_type, \
            success, \
            error = handler(self, **kwargs)
        except:
            http_code, \
            http_content, \
            http_content_type, \
            success, \
            error = (500, None, None, None, None)
        finally:
            self.send_response(http_code)

            if http_content:
                if http_content_type:
                    self.send_header("Content-Type", http_content_type)

                self.send_header("Content-Length", len(http_content))
                self.end_headers()
                self.wfile.write(http_content)

            if 'DEBUG' in globals() and DEBUG:
                if not error:
                    error = sys.exc_info()
                if error[0]:
                    raise error[0], error[1], error[2]

    return do_handler


class SubscriptionsCallbackHandler(BaseRequestHandler):
    @handle
    def do_GET(self):
        def on_success(mode, challenge, verify_token):
            pass

        def on_error(mode, challenge, verify_token, exc_info):
            return exc_info

        if self.path.find('?') != -1:
            self.path, self.query_string = self.path.split('?', 1)
        else:
            self.query_string = ''

        qs = dict(cgi.parse_qsl(self.query_string))

        return self.server.subscriptions.handler_get(
            qs['hub.mode'],
            qs['hub.challenge'],
            qs['hub.verify_token'],
            on_success=on_success,
            on_error=on_error
        )

    @handle
    def do_POST(self):
        def on_success(payload, signature):
            pass

        def on_error(payload, signature, exc_info):
            return exc_info

        payload_size = self.headers.get('Content-Length') or 0
        payload = self.rfile.read(int(payload_size))
        signature = self.headers.get('X-Hub-Signature')

        return self.server.subscriptions.handler_post(
            payload,
            signature,
            on_success=on_success,
            on_error=on_error
        )


if __name__ == '__main__':
    DEBUG = True
    HOST_NAME = 'localhost'
    PORT_NUMBER = 12345
    httpd = HTTPServer((HOST_NAME, PORT_NUMBER), SubscriptionsCallbackHandler)

    httpd.subscriptions = SubscriptionsAPI('<fb app id>', '<fb app secret>')

    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)
