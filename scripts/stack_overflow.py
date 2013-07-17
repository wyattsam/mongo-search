from scrapers import JSONScraper
from time import sleep


class StackOverflowScraper(JSONScraper):
    NAME = 'stack_overflow'
    API_BASE = 'https://api.stackexchange.com/2.1/'
    SEARCH_URL = API_BASE + 'search'
    PAGE_SIZE = 100

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

        while True:
            result = self.get_json(self.SEARCH_URL, params=params)
            items = result.get('items', [])

            for item in items:
                yield self.scrape_question(item)

            if 'has_more' not in result:
                break

            # don't remove this -- back off if you're told to backoff
            if 'backoff' in result:
                sleep(result['backoff'])

            params['page'] += 1

    def scrape(self):
        tags = ['mongodb']
        for tag in tags:
            for question in self.scrape_tag(tag):
                yield question
