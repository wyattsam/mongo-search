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

from base_hook import BaseHook
"""
from celery import Celery
from celery.contrib.methods import task_method

celery = Celery('github', broker="mongodb://localhost:27017")
"""

class GithubHook(BaseHook):
    def __init__(self):
        BaseHook.__init__(self)
        #self.needs_auth = True
        self.authtype = 'X-Hub-Signature'

    def authenticate(self, msg, h):
        #TODO implement this
        pass
        """
        token = str(user['auth']) # cannot be unicode
        hasher = HMAC.new(token, digestmod=self.sha1)
        hasher.update(msg)
        return result, (h == hasher.hexdigest()) # secure compare I suppose
        """

    #@celery.task(name="github.handle", filter=task_method)
    def handle(self, msg):
        name = msg['repository']['name']
        org = msg['repository']['owner']['name']
        head_sha = msg['head_commit']['id']
        _id = org + '/' + name + '-' + head_sha
        msg.update({
            '_id': _id,
            'source': 'github',
            'subsource': name
        })
        self.combined.update(dict(_id=_id), msg, True)
