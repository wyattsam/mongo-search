import requests

class BaseScraper(object):
    def __init__(self, name, auth, digest=False):
        self.name = name
        if auth:
            user = auth['user']
            password = auth['password']
            if user and password:
                if digest:
                    self.auth = requests.HTTPDigestAuth(user, password)
                else
                    self.auth = (user, password)
            else:
                self.auth = None

    def documents(self):
        headers = {'accept': 'application/json'}

        response = requests.get(self.apiurl, params=self.params, 
                                auth=self.auth, verify=False,
                                headers=headers)
        return self._scrape(self._filter(response.json(strict=False)))

    def _filter(self, doc):
        return doc
