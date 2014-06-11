from celery import Celery
import config.celery as celery_settings
import config.duckduckmongo as search_settings
from scrape import ScrapeRunner

app = Celery('celery')
app.config_from_object(celery_settings)

scraper = ScrapeRunner(search_settings.CONFIG)

@app.task
def scrapeall():
    scraper.runall()
