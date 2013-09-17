from scrapers import JSONScraper
from time import sleep


class StackOverflowScraper(JSONScraper):
    NAME = 'stack_overflow'
    API_BASE = 'https://api.stackexchange.com/2.1/'
    SEARCH_URL = API_BASE + 'search'
    PAGE_SIZE = 100

    def __init__(self, tags, credentials=None):
        self.tags = tags
        self.credentials = credentials

    def scrape_question(self, question):
        key = 'SO-' + str(question['question_id'])
        question['_id'] = key
        return question

    def scrape_tag(self, tag):
        print "[TAG] " + tag
        params = {
            'site': 'stackoverflow',
            'tagged': tag,
            'filter': '!*1Klotvkqr2dciMbX*Qdafx4aenCPiyZAdUE1x(1w',
            'sort': 'creation',
            'order': 'asc',
            'page': 1,
            'pagesize': self.PAGE_SIZE,
        }

        if self.credentials:
            params['access_token'] = self.credentials['access_token']
            params['key'] = self.credentials['key']

        while True:
            print '[%s] page %s' % (tag, params['page'])
            result = self.get_json(self.SEARCH_URL, params=params)
            items = result.get('items', [])

            if items:
                for item in items:
                    yield self.scrape_question(item)

                if not result['has_more']:
                    break

                params['page'] += 1

            else:
                print '[ERROR] %s' % result
                break

            # don't remove this -- back off if you're told to backoff
            if 'backoff' in result:
                backoff = result['backoff']
                print '[BACKOFF] backing off for %s seconds' % backoff
                sleep(backoff)


    def scrape(self):
        for tag in self.tags:
            for question in self.scrape_tag(tag):
                yield question