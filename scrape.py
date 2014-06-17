import inspect
import logging
import sys
import thread
import types
import traceback
from datetime import datetime

from pymongo import MongoClient

class ScrapeRunner(object):
    def __init__(self, cfg, snames=None,opt=False):
        self.client = MongoClient('localhost:27017')
        self.db = self.client['duckduckmongo']
        self.combined = self.db.combined
        self.scrapelog = self.db.scrapes
        self.cfg = cfg
        self.scrape_id = ""

        cfgs = [k for k in self.cfg.keys() if k[0] != '_']
        self.scrapers = self.cfg_instantiate('scraper', snames or cfgs)

        for s in self.scrapers:
            if s.needs_setup:
                # _setup may take time; let scraping continue while we do setup
                # FIXME: something is wrong with the thread safety here
                if opt:
                    thread.start_new_thread(s.setup, ())
                else:
                    s.setup()

        self.logger = logging.getLogger("ScrapeRunner")
        so = logging.StreamHandler(sys.stdout)
        so.setFormatter(
            logging.Formatter('[%(levelname)s] %(asctime)s %(name)s: %(message)s'))
        self.logger.addHandler(so)
        self.logger.setLevel(cfg['_loglevel'])

    def cfg_instantiate(self, typ, cfgs):
        clss = [self.cfg[c][typ] for c in cfgs]
        accum = []
        for (f, n) in zip(clss, cfgs):
            if self.cfg[n][typ]:
                kwargs = self.cfg[n]
                kwargs['_loglevel'] = self.cfg['_loglevel']
                accum.append(f(n, **kwargs))
        return accum

    def _save(self, document, srcname):
        document['source'] = srcname
        _id = document['_id']
        return self.combined.update(dict(_id=_id), document, True)

    def save(self, document, srcname):
        oid = self._save(self.join(document, self.cfg[srcname]['projector']), srcname)
        self.logger.debug("scraper '%s' saved oid '%s'" % (srcname, document['_id']))

    def log_scrape_start(self, scraper):
        self.logger.info("starting scrape for %s" % scraper.name)
        start = {
            'start': datetime.utcnow(),
            'source': scraper.name,
            'state': 'running'
        }
        self.scrape_id = self.scrapelog.insert(start)

    def log_scrape_finish(self, scraper):
        self.logger.info("ending scrape for %s" % scraper.name)
        end = dict(_id=self.scrape_id)
        upd = {
            '$set': {
                'state': 'complete',
                'end': datetime.utcnow()
            }
        }
        self.scrapelog.update(end, upd)

    def log_scrape_error(self, error):
        scrape = dict(_id=self.scrape_id)
        exc_t, exc_v, exc_tr = sys.exc_info()
        upd = {
            '$set': {
                'state': 'error',
                'error': str(error),
                'trace': traceback.format_exception(exc_t, exc_v, exc_tr)
            }
        }
        self.scrapelog.update(scrape, upd)
        self.scrape_id = None
        
    def join(self, doc, proj):
        ret = {}
        # if no projector is available, just return everything
        if len(proj) > 0:
            for k in proj.keys():
                try:
                    ret[k] = doc[k]
                except KeyError:
                    self.logger.error("Misplaced key in projector: %s" % k)
            return ret
        return doc

    def run(self, s):
        self.logger.info("running scraper: %s" % s.name)
        self.log_scrape_start(s)
        for d in s.documents():
            for d1 in d:
                try:
                    self.save(d1, s.name)
                except Exception as e:
                    self.logger.error("documents exception: " + str(e))
                    self.log_scrape_error(e)
                    return
        self.log_scrape_finish(s)

    def runall(self):
        self.logger.info("running all scrapers: %s" % str([s.name for s in self.scrapers]))
        while len(self.scrapers) > 0:
            s = self.scrapers[0]
            if not s.loading:
                self.run(s)
                self.scrapers.remove(s)
            else:
                self.logger.debug("temporarily skipped %s because it was loading" % s.name)

if __name__ == "__main__":
    import config.duckduckmongo as settings
    if len(sys.argv) == 1:
        runner = ScrapeRunner(settings.CONFIG)
    else:
        names = sys.argv[1:]
        runner = ScrapeRunner(settings.CONFIG, snames=names)
    runner.runall()
