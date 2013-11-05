import re
import requests

from HTMLParser import HTMLParser
from scrapers import JSONScraper


class MLStripper(HTMLParser):
    '''Markup language stripper to convert HTML into plain text'''
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


class ConfluenceScraper(JSONScraper):
    NAME = 'confluence'
    SPACES = ['10GEN', 'cs', 'sales', 'Devops', 'KB']
    API_BASE = 'https://wiki.mongodb.com/rest/prototype/1/'

    def __init__(self, credentials=None, skip=[]):
        self.skip = skip
        self.credentials = credentials

    def strip_tags(self, html):
        s = MLStripper()
        s.feed(html)
        return s.get_data()

    def scrape_page(self, page_id, space):
        user = self.credentials['user']
        password = self.credentials['password']

        page_url = ''.join([self.API_BASE, 'content/', page_id, '.json'])
        page_json = requests.get(page_url, auth=(user, password), verify=False).json()

        html_body = page_json['body']['value']
        # Some older documents returned from Confluence contain useful text,
        # but wrapped in tags that our parser does not properly handle.  To
        # deal with this here we look for such documents and extract the
        # useful text before passing it along to strip_tags()
        if "{wiki}" in html_body:
            r = re.compile(r'\{wiki\}(.*)\{wiki\}', re.MULTILINE|re.DOTALL)
            result = r.search(html_body)
            if result:
                html_body = result.group(1)

        text_body = self.strip_tags(html_body)
        doc = {
            '_id': page_json['id'],
            'title': page_json['title'],
            'body': text_body,
            'url':  page_json['link'][0]['href'],
            'subsource': space,
        }
        return doc

    def search_pages(self, space, index):
        space_url = ''.join([self.API_BASE, 'search.json'])
        space_params = {
            'type': 'page',
            'startIndex': str(index),
            'spaceKey': space
        }
        space_json = self.get_json(space_url, space_params, auth=self.credentials)

        result = space_json['result']
        if result:
            return [elem['id'] for elem in result]

    def scrape_pages(self, space):
        index = 0

        while True:
            result = self.search_pages(space, index)
            if result:
                for page_id in result:
                    yield self.scrape_page(page_id, space)
            else:
                break

            index += 50

    def scrape_space(self, space):
        if space not in self.skip:
            print "[SPACE] " + space
            for page in self.scrape_pages(space):
                yield page

    def scrape(self):
        spaces = self.SPACES
        print '[WIKI] %s' % spaces
        for space in spaces:
            for page in self.scrape_space(space):
                yield page
