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

class ConfluenceTransformer(BaseTransformer):
    def __init__(self):
        BaseTransformer.__init__(self)

    def transform(self, obj):
        base = BaseTransformer.transform(self, obj)
        base.update({
            'id': obj['_id'],
            'title': obj['title'],
            'snippet': obj['body'],
            'url': obj['url'],
            'space': obj['subsource'],
            'source': 'confluence'
        })
        return base
