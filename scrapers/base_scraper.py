import requests
import logging
import itertools
import sys
import ssl

class BaseScraper(object):
    def __init__(self, name, **kwargs):
        self.name = name
        self.finished = False
        self.log = logging.getLogger(__name__)

        # set up the logger
        so = logging.StreamHandler(sys.stdout)
        so.setFormatter(
            logging.Formatter('[%(levelname)s] %(asctime)s %(name)s: %(message)s'))
        self.log.addHandler(so)
        self.log.setLevel(kwargs['_loglevel'])

        self.params = {}

        self.loading = False
        self.needs_setup = False

        if 'auth' in kwargs:
            auth = kwargs['auth']
            user = auth['user']
            password = auth['password']
            if user and password:
                if 'digest' in kwargs and kwargs['digest']:
                    self.auth = requests.HTTPDigestAuth(user, password)
                else:
                    self.auth = (user, password)
            else:
                self.auth = None
        else:
            self.auth = None

    def documents(self):
        """Produces a generator of all documents desired from the
           API url. _scrape should change the
           value of self.finished at some point, or this method
           never terminates."""
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
            yield self._scrape(response.json(strict=False))

    def _scrape(self, doc):
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
