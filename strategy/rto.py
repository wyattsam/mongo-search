from base_strategy import BaseStrategy

class RTOStrategy(BaseStrategy):
    def __init__(self, sm, scrapes):
        BaseStrategy.__init__(self, sm, scrapes)

    def init_alg_state(self):
        return {}

    def build_meta(self, s_name, last_t):
        return {
            '_id': s_name,
            'tbar': last_t,
            'delbar': 0
        }

    def post_metaobj_gen(self, metaobj, s_name, last_t):
        return {
            'last_t': last_t,
            'tbar': metaobj['tbar'],
            'delbar': metaobj['delbar']
        }

    def compute(self, state):
        tbar = state['tbar']
        delbar = state['delbar']
        last_t = state['last_t']

        delta = last_t - tbar
        tbar = (last_t - tbar) * 0.125
        delbar = (abs(delta) - delbar) * 0.25

        state['tbar'] = tbar
        state['delbar'] = delbar
        return max(180.0, abs(tbar + (delbar*4.0)))

    def build_update_dict(self, state, last_t):
       return {
            'tbar': state['tbar'],
            'delbar': state['delbar']
        }
