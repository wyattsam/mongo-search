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

class JiraHook(BaseHook):
    def __init__(self):
        BaseHook.__init__(self)

    def handle(self, msg):
        _id = msg['issue']['key']
        event_type = msg['webhookEvent']
        if event_type == 'jira:issue_updated':
            new_msg = {
                'fields': {
                    'description': msg['fields']['description'],
                    'priority': msg['fields']['priority'],
                    'status': msg['fields']['status'],
                    'summary': msg['fields']['summary']
                }
            }
            upd = {
                '$set': new_msg,
                '$push': {'fields.comment.comments': msg['comment']},
                '$inc': {'fields.comment.total': 1}
            }
            self.combined.update(dict(_id=_id), upd, True)
        elif event_type == 'jira:issue_created':
            msg.update({
                '_id': _id,
                'source': 'jira',
                'subsource': _id.split('-')[0]
            })
            self.combined.update(dict(_id=_id), msg, True)
