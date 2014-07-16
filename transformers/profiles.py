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
from flask import request
import md5

CORP_URL = "https://corp.10gen.com/"
def corp_url():
    if request.referrer and 'mongodb' in request.referrer:
        return CORP_URL.replace('10gen', 'mongodb')
    return CORP_URL

class ProfilesTransformer(BaseTransformer):
    def __init__(self):
        BaseTransformer.__init__(self)

    def transform(self, obj):
        base = BaseTransformer.transform(self, obj)
        base.update({
            'id': obj['crowd_id'],
            'full_name': obj['full_name'],
            'url': corp_url() + 'employees/' + obj['crowd_id'],
            'team': obj['team']['name'],
            'office': obj['office'],
            'email': obj['primary_email'],
            'github': obj['github'],
            'title': obj['title'],
            'md5': md5.new(obj['primary_email'].strip().lower()).hexdigest()
        })
        return base
