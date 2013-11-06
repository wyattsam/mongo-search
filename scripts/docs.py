import requests
from scrapers import JSONScraper

class DocumentationScraper(JSONScraper):
    NAME = 'docs'
    API_BASE = 'http://docs.mongodb.org/'

    def __init__(self, kinds):
        self.kinds = kinds

    def get_urls(self, kind):
        file_urls_url = self.API_BASE + kind + '/json/.file_list'
        file_urls = requests.get(file_urls_url).text.split('\n')
        return file_urls

    def scrape_file(self, kind, file_url):
        file_json = self.get_json(file_url)
        if 'text' in file_json:
            page_name = file_json['current_page_name']
            _id = "-".join([self.NAME, kind, page_name])
            doc = {
                '_id': _id,
                'title': file_json['title'],
                'body': file_json['text'],
                'url':  file_json['url'],
                'section': kind,
            }
            return doc
        else:
            return

    def scrape_kind(self, kind):
        file_urls = self.get_urls(kind)
        for file_url in file_urls:
            if not file_url:
                return
            try:
                yield self.scrape_file(kind, file_url)
            except ValueError:
                print "Failed to parse json in %s" % file_url
                continue

    def scrape(self):
        for kind in self.kinds:
            print '[DOC] ' + kind
            for doc in self.scrape_kind(kind):
                yield doc

class MmsDocumentationScraper(DocumentationScraper):
    NAME = 'mms'
    API_BASE = 'http://mms.mongodb.com/'
