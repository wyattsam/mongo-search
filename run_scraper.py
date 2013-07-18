#!/usr/bin/env python
import sys
from scripts.scrapers import ScrapeRunner
from scripts.jira import JiraScraper
from scripts.github import GitHubScraper
from scripts.stack_overflow import StackOverflowScraper
from scripts.docs import DocumentationScraper
from scripts.google_groups import GoogleGroupsScraper

user = 'scraper'
password = 'scr4p3r'

scraper_name = sys.argv[1]
credentials = tuple(sys.argv[2:4])

runner = ScrapeRunner([user, password])

scraper = None
if scraper_name == 'jira':
    scraper = JiraScraper(credentials)
elif scraper_name == 'github':
    scraper = GitHubScraper()
elif scraper_name == 'stack_overflow':
    scraper = StackOverflowScraper()
elif scraper_name == 'docs':
    scraper = DocumentationScraper()
elif scraper_name == 'google_groups':
    scraper = GoogleGroupsScraper(credentials)

runner.run(scraper)
