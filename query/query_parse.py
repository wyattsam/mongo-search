from pyparsing import CaselessKeyword, alphanums, Suppress, OneOrMore, \
                      Forward, Word, Or, Optional, Group

class BasicQuery(object):
    def __init__(self, args, cfg):
        self.args = args
        self._text = args['query']
        SOURCES = [CaselessKeyword(k) for k in cfg.keys() if k[0] != '_']

        ### terms
        ident = Word(alphanums)
        quoted_ident = Suppress('"') + OneOrMore(Word(alphanums)) + Suppress('"')
        conjunction = ident \
            + OneOrMore(Suppress('&' | CaselessKeyword('and')) \
            + ident)

        query_term = Group(OneOrMore(conjunction)).setResultsName('conjunction') \
                | Group(OneOrMore(quoted_ident)).setResultsName('quoted')\
                | Group(OneOrMore(ident)).setResultsName('ident')
        ### aggregators
        source = (Suppress(CaselessKeyword('$from')) \
                 + Or(SOURCES) \
                 + Optional(Suppress('/') + ident)
                 ).setResultsName('source')
        aggregator = source

        ### query
        query = OneOrMore(query_term).setResultsName('terms') \
              + Optional(Suppress('|') \
              + OneOrMore(aggregator)).setResultsName('aggregators')

        self.parsed = query.parseString(self._text)

    @property
    def text(self):
        return self._text

    @property
    def query(self):
        return self.parsed.terms

    @property
    def terms(self):
        tms = []
        # TODO this is wrong :(
        for grp in self.parsed.terms:
            for t in grp:
                tms.append(t)
        return "".join(t)

    @property
    def aggs(self):
        return self.parsed.aggregators

class BasicQueryVisitor(object):
    def __init__(self, query):
        self.query = query
        self.doc = {
            '$text': {
                '$search': ''
            }
        }

    def visit(self):
        """Top level visit, don't edit"""
        self.visit_terms(self.query.parsed.terms)
        #if we have a source/subsource option from the U:, use that
        if 'source' in self.query.args and self.query.args['source']:
            self.doc['source'] = self.query.args['source']
            if 'subsource' in self.query.args and self.query.args['subsource']:
                self.doc['subsource'] = self.query.args['subsource']
        if len(self.query.parsed.aggregators) > 0:
            self.visit_agg(self.query.parsed.aggregators)
        self.doc['$text']['$search'] = self.doc['$text']['$search'].strip()
        return self.doc

    def visit_terms(self, terms):
        for k in self.query.parsed.terms.keys():
            getattr(self, 'visit_'+str(k))(self.query.parsed.terms[k])

    def visit_agg(self, aggs):
        for k in self.query.parsed.aggregators.keys():
            getattr(self, 'visit_'+str(k))(self.query.parsed.aggregators[k])

    ### Term visitors
    def visit_ident(self, ident):
        for i in ident:
            self.doc['$text']['$search'] += i + " "

    def visit_quoted(self, quoted):
        self.doc['$text']['$search'] += '"' + ' '.join(quoted) + '" '

    def visit_conjunction(self, conj):
        self.doc['$text']['$search'] += '"' + ' '.join(conj) + '" '

    ### Aggregator visitors
    def visit_source(self, src):
        self.doc['source'] = src[0]
        if len(src) > 1:
            self.doc['subsource'] = src[1]
