import pyparsing
import operator
from search import SOURCES, SUBSOURCES
from pyparsing import Literal, CaselessKeyword, Word, \
    Suppress, ZeroOrMore, Optional, Each

class MongoQuery(object):

    def __init__(self, args):
        self.args = args

        source_selector = CaselessKeyword("source") + \
            Suppress(":") + Word(pyparsing.alphanums).setResultsName('source')

        subsource_selector = reduce(
            operator.or_, (CaselessKeyword(x['name']) for x in SUBSOURCES.values() if x)
        ) + Suppress(":") + Word(pyparsing.alphanums).setResultsName('subsource')

        query_parser = Optional(
            source_selector +
            Optional(subsource_selector)
        ) + pyparsing.restOfLine.setResultsName('query')

        self.parsed = query_parser.parseString(args['query'])

    @property
    def query(self):
        return self.parsed.get('query')

    @property
    def source(self):
        source = self.parsed.get('source') or self.args.get('source')
        if source:
            return source.lower()

    @property
    def sub_source(self):
        arg_sub = None

        for sub_source in (x['name'] for x in SUBSOURCES.values() if x):
            if sub_source in self.args:
                arg_sub = self.args[sub_source]

        return self.parsed.get('subsource') or arg_sub

    @property
    def filter(self):
        filter_doc = {}

        source = self.source
        sub_source = self.sub_source

        if source:
            filter_doc['source'] = source

            if sub_source:
                filter_doc['subsource'] = sub_source

        return filter_doc
