from base_strategy import BaseStrategy

class SlowStartStrategy(BaseStrategy):
    def __init__(self, sm, scrapes, cwnd_def=60*60*6, wdelta=1200):
        BaseStrategy.__init__(self, sm, scrapes)
        self.cwnd_def = cwnd_def
        self.wdelta = wdelta
        self.ssthresh = int(cwnd_def / 2)

    def init_alg_state(self):
        return {'loss': False}
    
    def build_meta(self, s_name, last_t):
        return {
            '_id': s_name,
            'last_t': last_t,
            'cwnd': self.cwnd_def,
            'ssthresh': self.ssthresh
        }

    def post_metaobj_gen(self, metaobj, s_name, last_t):
        return {
            'loss': metaobj['last_t'] < last_t
        }

    def compute(self, state):
        metaobj = state['metaobj']
        if state['loss']:
            metaobj['cwnd'] = self.cwnd_def
        else:
            print 'ssthresh is', self.ssthresh
            if metaobj['cwnd'] > self.ssthresh:
                metaobj['cwnd'] /= 2
            else:
                metaobj['cwnd'] -= self.wdelta
        state['cwnd'] = metaobj['cwnd']

        return metaobj['cwnd']

    def build_update_dict(self, state, last_t):
        return {
            'last_t': last_t,
            'ssthresh': self.ssthresh,
            'cwnd': state['cwnd']
        }
