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

from socket import gethostbyname
from pymongo import MongoClient

class BaseHook(object):
    def __init__(self, hostname):
        self.needs_auth = False
        client = MongoClient('localhost:27017')
        db = client['duckduckmongo']
        self.combined = db['combined']

    def receive(self, msg):
        # TODO should call celery
        # apparently blocked on celery being useless with classes
        self.handle(msg)
