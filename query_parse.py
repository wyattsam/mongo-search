import pyparsing
from search import SOURCES
from pyparsing import Literal, CaselessKeyword, Word, \
    Suppress, ZeroOrMore, Optional, Each

class MongoQuery(object):

    def reset(self):
        self.project_filter = set()
        self.source_filter = set()
        self.full_text_query = None

    def __init__(self):
        self.reset()

        project_selector = CaselessKeyword("project") + \
            Suppress(":") + Word(pyparsing.alphanums) + \
            ZeroOrMore(Suppress(",") + Word(pyparsing.alphanums))

        source_selector = CaselessKeyword("source") + \
            Suppress(":") + Word(pyparsing.alphanums) + \
            ZeroOrMore(Suppress(",") + Word(pyparsing.alphanums))

        project_selector.setParseAction(self.push_to_filter)
        source_selector.setParseAction(self.push_to_filter)

        self.query_parser = Each(Optional(source_selector) + Optional(project_selector)) + \
            pyparsing.restOfLine

    def push_to_filter(self, strg, loc, toks):
        filter_name = toks[0].lower()
        if filter_name not in ["project", "source"]:
            return
        filter_obj = getattr(self, filter_name + "_filter")
        for tok in toks[1:]:
            filter_obj.add(tok)

    def parse(self, query):
        tokens = self.query_parser.parseString(query)
        self.full_text_query = tokens[-1]

    def build_filter(self):
        filter_doc = {}
        bad_sources = filter(lambda x: x not in SOURCES, self.source_filter)
        if bad_sources:
            raise Exception("Unknown sources", bad_sources)
        if len(self.source_filter) != len(SOURCES):
            filter_doc['source'] = {"$in":list(self.source_filter)}
        return filter_doc

    def debug(self):
        print "Searching for:", self.full_text_query
        print "in projects: " + ','.join(self.project_filter)
        print "using sources: " + ','.join(self.source_filter)

#mq = MongoQuery()
#mq.parse(testString)
#ddmq.debug()
