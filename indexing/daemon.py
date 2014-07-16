# Copyright 2014 MongoDB Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import Response

import logging
import json

class IndexDaemon(object):
    def __init__(self, hooks):
        self.hooks = hooks

    def handle(self, sourcename, message, headers):
        hookcls = self.hooks[sourcename]
        hook = hookcls()
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
