from base_scraper import BaseScraper
import requests

class DocsScraper(BaseScraper):
    def __init__(self, name, **kwargs):
        BaseScraper.__init__(self, name, **kwargs)
        kinds = kwargs['kinds']
        self.apiurl = "http://docs.mongodb.org/"
        self.kinds = kinds
        self.kind = ''
        self.urlexts = []

        self.needs_setup = True

    def _scrape(self, doc):
        ret = None
        if 'text' in doc:
            pname = doc['current_page_name']
            _id = '-'.join([self.name, self.kind, pname])
            doc['_id'] = _id
            doc['section'] = self.kind
            doc['subsource'] = self.kind
            ret = doc
        else:
            self.err("Received unexpected message %s" % str(doc))
            self.finished = True

        # ensure we advance
        if len(self.urlexts) > 0:
            url = self.urlexts.pop(0)
            self.kind = url[0]
            self.apiurl = url[1]
        else:
            self.finished = True
        return ret

    def _setup(self):
        # TODO: can the self.loading stuff be taken care of with a decorator?
        for k in self.kinds:
            urls = requests.get(self.apiurl + '/' + k + '/json/.file_list').text.split('\n')
            self.urlexts.extend([(k,u) for u in urls])
        # make sure apiurl is updated
        url = self.urlexts.pop(0)
        self.kind = url[0]
        self.apiurl = url[1]
