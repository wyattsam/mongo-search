#!/usr/bin/env python
import sys
import settings
from scripts.scrapers import ScrapeRunner
from scripts.jira import JiraScraper
from scripts.github import GitHubScraper
from scripts.stack_overflow import StackOverflowScraper
from scripts.docs import DocumentationScraper, MmsDocumentationScraper
from scripts.google_groups import GoogleGroupsScraper
from scripts.profiles import ProfilesScraper

scraper_name = sys.argv[1]
runner = ScrapeRunner(**settings.MONGO)

scraper = None
if scraper_name == 'jira':
    scraper = JiraScraper(**settings.JIRA)
elif scraper_name == 'github':
    scraper = GitHubScraper(**settings.GITHUB)
elif scraper_name == 'stack_overflow':
    scraper = StackOverflowScraper(**settings.STACK_OVERFLOW)
elif scraper_name == 'google_groups':
    scraper = GoogleGroupsScraper(**settings.GMAIL)
elif scraper_name == 'profiles':
    scraper = ProfilesScraper(**settings.PROFILES)
elif scraper_name == 'docs':
    scraper = DocumentationScraper(**settings.DOCS)
elif scraper_name == 'mms_docs':
    scraper = MmsDocumentationScraper(**settings.MMS_DOCS)

runner.run(scraper)
