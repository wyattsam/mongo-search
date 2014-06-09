import inspect
import logging
import sys
import thread
import types

from pymongo import MongoClient

class ScrapeRunner(object):
    def __init__(self, cfg):
        self.client = MongoClient('localhost:27017')
        self.db = self.client['duckduckmongo']
        self.combined = self.db.combined
        self.cfg = cfg

        scps = [k for k in self.cfg.keys() if k[0] != '_']
        scraper_classes = [self.cfg[c]['cls'] for c in scps]
        self.scrapers = [f(n, **cfg[n]) for (f, n) in zip(scraper_classes, scps) if self.cfg[n]['cls']]

        for s in self.scrapers:
            if s.needs_setup:
                # _setup may take time; let scraping continue while we do setup
                # FIXME: something is wrong with the thread safety here
                #thread.start_new_thread(s._setup, ())
                s.setup()

        self.logger = logging.getLogger("ScrapeRunner")
        so = logging.StreamHandler(sys.stdout)
        so.setFormatter(
            logging.Formatter('[%(levelname)s] %(asctime)s %(name)s: %(message)s'))
        self.logger.addHandler(so)
        self.logger.setLevel(cfg['_loglevel'])

    def save(self, document, srcname):
        document['source'] = srcname
        _id = document['_id']
        return self.combined.update(dict(_id=_id), document, True)

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

    def run(self):
        while len(self.scrapers) > 0:
            s = self.scrapers[0]
            if not s.loading:
                for d in s.documents():
                    if isinstance(d, types.GeneratorType): # FIXME bad news...
                        for d1 in d:
                            try:
                                oid = self.save(self.join(d1, self.cfg[s.name]['projector']), s.name)
                                self.logger.info("scraper '%s' saved oid %s" % (s.name, d1['_id']))
                            except KeyError as e:
                                self.logger.error("documents exception:" + str(e))
                                continue
                    else:
                        try:
                            oid = self.save(self.join(d, self.cfg[s.name]['projector']), s.name)
                            self.logger.info("scraper '%s' saved oid %s" % (s.name, d['_id']))
                        except KeyError as e:
                            self.logger.error("documents exception:" + str(e))
                            continue
                self.scrapers.remove(s)
            else:
                self.logger.debug("temporarily skipped %s because it was loading" % s.name)

if __name__ == "__main__":
    import settings
    runner = ScrapeRunner(settings.CONFIG)
    runner.run()
