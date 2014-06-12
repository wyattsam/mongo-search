from base_scraper import BaseScraper

class ProfilesScraper(BaseScraper):
    def __init__(self, name, **kwargs):
        BaseScraper.__init__(self, name, **kwargs)
        self.apiurl = 'https://corp.mongodb.com/api/employee'
        self.params = {'expand': 'team'}

    def _scrape(self, doc, links=None):
        for d in doc['employees']:
            eid = d['uri'].partition("/api/employee/")[2]
            d['crowd_id'] = eid
            d['_id'] = 'employee-' + eid
            d['full_name'] = " ".join([d['first_name'], d['last_name']])
            yield d
        self.finished = True # one query for everyone; wow!
