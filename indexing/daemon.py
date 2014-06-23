from flask import Response

import logging
import json

class IndexDaemon(object):
    def __init__(self, hooks):
        self.hooks = hooks

    def handle(self, sourcename, message, headers):
	print "stepped into handle"
	print "sourcename", sourcename
	print "allhooks", self.hooks
        hookcls = self.hooks[sourcename]
	hook = hookcls()
	print "hook is", hook
	print "found a hook"
        if not hook:
            return self.respond(403, status="Unrecognized hook source")
        if hook.needs_auth:
            if not hook.authenticate(message, headers[hook.authtype]):
                return self.respond(401)
        hook.receive(message)
        return self.respond(200)

    def respond(self, code, status=""):
        response = Response(mimetype="text/html")
        response.status_code = code
        if len(status) > 0:
            response.status = status
        return response
