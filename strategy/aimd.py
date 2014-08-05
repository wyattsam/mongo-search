from base_strategy import BaseStrategy

class AIMDStrategy(BaseStrategy):
    def __init__(self, sm, scrapes, cwnd_def=60*60, wdelta=300):
        BaseStrategy.__init__(self, sm, scrapes)
        self.cwnd_def = cwnd_def
        self.wdelta = wdelta

    def init_alg_state(self):
        return {'loss': False}

    def build_meta(self, s_name, last_t):
        return {
            '_id': s_name,
            'last_t': last_t,
            'cwnd': self.cwnd_def
        }

    def post_metaobj_gen(self, metaobj, s_name, last_t):
        return {
            'loss': metaobj['last_t'] < last_t
        }

    def compute(self, state):
        metaobj = state['metaobj']
        if state['loss']:
            metaobj['cwnd'] *= 2
        else:
            metaobj['cwnd'] -= self.wdelta
        state['cwnd'] = metaobj['cwnd']

        return metaobj['cwnd']

    def build_update_dict(self, state, last_t):
        return {
            'last_t': last_t,
            'cwnd': state['cwnd']
        }
