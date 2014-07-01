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

import requests
import logging
import itertools
import sys
import ssl

class BaseScraper(object):
    def __init__(self, name, **kwargs):
        self.name = name
        self.finished = False

        self._loglevel = kwargs['_loglevel']
        self.logging_available = False

        self.params = {}

        self.loading = False
        self.needs_setup = False

        if 'auth' in kwargs:
            auth = kwargs['auth']
            if 'user' in auth and 'password' in auth:
                self._auth(auth, 'user', 'password', kwargs)
            elif 'client_id' in auth and 'client_secret' in auth:
                self._auth(auth, 'client_id', 'client_secret', kwargs)
            else:
                self.auth = None
        else:
            self.auth = None

    def _setup_logger(self, name):
        self.log = logging.getLogger(name)

        # set up the logger
        so = logging.StreamHandler(sys.stdout)
        so.setFormatter(
            logging.Formatter('[%(levelname)s] %(asctime)s %(name)s: %(message)s'))
        self.log.addHandler(so)
        self.log.setLevel(self._loglevel)
        self.logging_available = True

            
    def _auth(self, auth, un, pw, kwargs):
        user = auth[un]
        password = auth[pw]
        if user and password:
            if 'digest' in kwargs and kwargs['digest']:
                self.auth = requests.auth.HTTPDigestAuth(user, password)
            else:
                self.auth = (user, password)
        else:
            self.auth = None

    def documents(self):
        """Produces a generator of all documents desired from the
           API url. _scrape should change the
           value of self.finished at some point, or this method
           never terminates."""
        if not self.logging_available:
            self._setup_logger()
        while not self.finished:
            headers = {'accept': 'application/json'}

            try:
                response = requests.get(self.apiurl, params=self.params, 
                                        auth=self.auth, verify=False,
                                        headers=headers,
                                        timeout=60)
            except requests.exceptions.MissingSchema:
                # TODO is this a reliable terminator?
                return
            # timeouts :(
            except requests.exceptions.SSLError:
                self.warn("Experienced requests.exceptions.SSLError timeout; continuing")
                continue
            except ssl.SSLError:
                self.warn("Experienced ssl.SSLError timeout; continuing")
                continue
            json = response.json(strict=False)
            yield self._scrape(json, response.links)

    def _scrape(self, doc, links=None):
        """Transform a response document into the desired form.
           If the scraper has internal state, it should be
           updated here."""
        return doc

    def setup(self):
        """Front for _setup. Do not override."""
        self.loading = True
        self._setup()
        self.loading = False

    def _setup(self):
        """Any additional setup that's required."""
        pass

    # Logging stuff
    def info(self, msg):
        self.log.info(msg)
    def warn(self, msg):
        self.log.warning(msg)
    def debug(self, msg):
        self.log.debug(msg)
    def err(self, msg):
        self.log.error(msg)
