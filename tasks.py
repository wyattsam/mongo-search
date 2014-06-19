from celery import Celery
import config.celery as celery_settings
import config.duckduckmongo as search_settings
from scrape import ScrapeRunner

app = Celery('tasks')
app.config_from_object(celery_settings)

cfg = search_settings.CONFIG
scraper = ScrapeRunner(cfg)

sources = [k for k in cfg.keys() if k[0] != '_']

@app.task
def scrape_source(source):
    scraper.run(cfg[source]['scraper'])
    scrape_stackoverflow.delay(source)

if __name__ == '__main__':
    for source in sources:
        scrape_source.delay(source)
