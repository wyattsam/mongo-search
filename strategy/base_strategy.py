from datetime import timedelta

class BaseStrategy(object):
    def __init__(self, sm, scrapes):
        self.scrapemeta = sm
        self.scrapes = scrapes

    def launch(self, s_name, last_t, job):
        last_t = last_t.total_seconds()

        metaobj = self.scrapemeta.find_one(dict(_id=s_name))
        alg_state = self.init_alg_state()
        if not metaobj:
            d = self.scrapes.find({
                'source': s_name,
                'state': 'complete'
                }).sort([('end', -1)])[0]
            last_time = (d['end'] - d['start']).total_seconds()
            metaobj = self.build_meta(s_name, last_t)
            self.scrapemeta.insert(metaobj)
            alg_state['metaobj'] = metaobj
        else:
            alg_state.update(self.post_metaobj_gen(metaobj, s_name, last_t))
            alg_state['metaobj'] = metaobj

        rtt = self.compute(alg_state)
        updict = self.build_update_dict(alg_state, last_t)
        self.scrapemeta.update(dict(_id=s_name),
                {'$set': updict},
                True)
        td = timedelta(seconds=rtt)

        return td

    def init_alg_state(self):
        pass

    def build_meta(self, s_name, last_t):
        pass

    def post_metaobj_gen(self, metaobj, s_name, last_t):
        pass

    def compute(self, state):
        pass

    def build_update_dict(self, state, last_t):
        pass

