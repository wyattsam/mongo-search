from celery import Celery
import config.celery as celery_settings
import config.duckduckmongo as search_settings
from scrape import ScrapeRunner

app = Celery('tasks')
app.config_from_object(celery_settings)

cfg = search_settings.CONFIG

#sources = [k for k in cfg.keys() if k[0] != '_']
sources = ['docs']

@app.task
def scrape_source(source):
    scraper = ScrapeRunner(cfg, snames=[source])
    scraper.do_setup()
    scraper.runall()
    scrape_source.delay(source)

if __name__ == '__main__':
    for source in sources:
        scrape_source.delay(source)
