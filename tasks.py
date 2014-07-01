# Copyright 2014 MongoDB Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from celery import Celery
import config.celery as celery_settings
import config.duckduckmongo as search_settings
from scrape import ScrapeRunner

app = Celery('tasks')
app.config_from_object(celery_settings)

cfg = search_settings.CONFIG

sources = [k for k in cfg.keys() if k[0] != '_']

@app.task
def scrape_source(source):
    scraper = ScrapeRunner(cfg, snames=[source])
    scraper.do_setup()
    scraper.runall()

@app.task
def scrape_all():
    for source in sources:
        scrape_source.delay(source)

if __name__ == '__main__':
    scrape_all()
