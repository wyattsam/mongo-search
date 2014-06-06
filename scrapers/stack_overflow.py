from time import sleep
from base_scraper import BaseScraper

class StackOverflowScraper(BaseScraper):
    def __init__(self, name, **kwargs):
        BaseScraper.__init__(self, name, **kwargs)
        self.apiurl = "https://api.stackexchange.com/2.1/search"
        self.tags = kwargs['tags']
        self.tag = 0
        self.params = {
                'site': 'stackoverflow',
                'tagged': self.tags[self.tag],
                'filter': '!*1Klotvkqr2dciMbX*Qdafx4aenCPiyZAdUE1x(1w',
                'sort': 'creation',
                'order': 'asc',
                'page': 1,
                'pagesize': 100
            }
        # TODO I think I messed up the credentials thing maybe

    def _scrape(self, doc):
        self.info('[%s] page %s' % (self.params['tagged'], self.params['page']))
        items = doc.get('items', [])
        accum = [] # FIXME this method should generate instead!!!
        if items:
            for item in items:
                key = self.name + "-" + str(item['question_id'])
                item['_id'] = key
                accum.append(item)

            # this tag is empty
            if not doc['has_more']:
                # check for more tags
                if len(self.tags) > self.tag:
                    self.tag += 1
                    self.params['tagged'] = self.tags[self.tag]
                    self.params['page'] = 1
                # no more tags, bow out
                else:
                    self.finished = True
            # keep going on this tag
            else:
                self.params['page'] += 1
        else:
            self.err("Received unexpected message %s" % doc)
            self.finished = True

        if 'backoff' in doc:
            backoff = doc['backoff']
            self.warn('backing off from stackoverflow for %s seconds' % backoff)
            sleep(backoff)
        return accum
