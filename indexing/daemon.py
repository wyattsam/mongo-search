from flask import Response

import logging
import json

class IndexDaemon(object):
    def __init__(self, hooks):
        self.hooks = hooks

    def handle(self, message, headers, env):
        authed = None, False
        if 'REMOTE_ADDR' not in env:
            return self.respond(412, status="a REMOTE_ADDR is required")
        requester = env['REMOTE_ADDR']

        hook = self.get_hook_by_ip(requester)
        if not hook:
            return self.respond(403, status="Unrecognized hook source")
        if hook.needs_auth:
            if not hook.authenticate(message, headers[hook.authtype]):
                return self.respond(401)
        hook.receive(message)
        return self.respond(200)

    def get_hook_by_ip(self, ip):
        for cls in self.hooks:
            inst = cls()
            if inst.ip == ip:
                return inst

    def respond(self, code, status=""):
        response = Response(mimetype="text/html")
        response.status_code = code
        if len(status) > 0:
            response.status = status
        return response
