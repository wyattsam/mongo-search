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

from base_transformer import BaseTransformer

class GithubTransformer(BaseTransformer):
    def __init__(self):
        BaseTransformer.__init__(self)

    def transform(self, obj):
        base = BaseTransformer.transform(self, obj)
        committer = obj['commit']['committer']
        commit_msg_header = obj['commit']['message']
        commit_msg_body = None
        newline_pos = commit_msg_header.find('\n')
        if newline_pos >= 0:
            commit_msg_body = commit_msg_header[newline_pos:].strip()
            commit_msg_header = commit_msg_header[0:newline_pos].strip()
        base.update({
            'url': obj['html_url'],
            'committer': obj['commit']['committer']['name'],
            'avatar': committer.get('avatar_url', ''),
            'date': obj['commit']['committer']['date'],
            'commit_msg': commit_msg_header,
            'commit_body': commit_msg_body,
            'repo_name': obj['repo']['full_name']
        })
        return base
