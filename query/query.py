import pyparsing as pp
import ast
from werkzeug.datastructures import ImmutableMultiDict

SELECTORS = ['source']

def make_IdentTerm(s, loc, toks):
    return ast.IdentTerm(toks[0])

def make_QuotedTerm(s, loc, toks):
    print toks
    return ast.QuotedTerm(toks[1:len(toks)-1])

def make_Query(s, loc, toks):
    terms = []
    selectors = []
    for t in toks:
        if isinstance(t, ast.Selector):
            selectors.append(t)
        else:
            terms.append(t)
    return ast.Query(terms, selectors)

def make_NotSelector(s, loc, toks):
    tokstrs = map(str, toks)
    neg_idx = tokstrs.index('!')
    toks.pop(neg_idx)
    sel = toks[0]
    maker = make_GenericSelector
    if sel in SELECTORS:
        maker = globals()['make_'+sel]
    return ast.NegativeSelector(maker(s, loc, toks))

def make_ListSelector(s, loc, toks):
    sel = toks[0]
    tokstrs = map(str, toks)
    start_idx, end_idx = tokstrs.index('[')+1, tokstrs.index(']')
    opts = toks[start_idx:end_idx]
    maker = make_GenericSelector
    if sel in SELECTORS:
        maker = globals()['make_'+sel]
    sels = []
    for o in opts:
        sels.append(maker(s, loc, [sel, toks[1], o]))
    return ast.ListSelector(sels)


def make_GenericSelector(s, loc, toks):
    return ast.GenericSelector(toks[0], toks[2])

def make_source(s, loc, toks):
    if len(toks) == 5: #ugly, but this is an accurate condition
        return ast.SourceSelector('source', toks[2], toks[4])
    return ast.SourceSelector('source', toks[2], None)

class BasicQuery(object):
    def __init__(self, args, ss):
        self.args = args
        if isinstance(args, ImmutableMultiDict):
            self.args = args.to_dict()
        text = args['query']
        self.query = text

        self.subsources = ss
        self.ast = self._query()[0]

    def _query(self):
        ## Utility
        ident = pp.Word(pp.srange("[a-zA-Z0-9_.+-]"))

        ## Terms
        ident_term = pp.Word(pp.srange("[a-zA-Z0-9_.+-]")).setParseAction(
                make_IdentTerm)
        quoted_term = ('"' + pp.OneOrMore(ident_term) + '"').setParseAction(
                make_QuotedTerm)
        term = quoted_term | ident_term

        ## Selector base
        selector = pp.Forward()
        selector_start = ident + ':'

        ## Selector bodies only
        selector_body = pp.Forward()
        not_selector_body = '!' + selector_body
        list_selector_body = '[' + pp.delimitedList(selector_body, ',') + ']'
        source_selector_body = ident + pp.Optional('/' + ident)
        generic_selector_body = ident
        selector_body << (
                  not_selector_body
                | list_selector_body
                | source_selector_body
                | generic_selector_body)

        ## Full selectors
        not_selector = selector_start + not_selector_body
        list_selector =  selector_start + list_selector_body
        source_selector = pp.CaselessKeyword('source') + ':' + source_selector_body
        generic_selector = selector_start + generic_selector_body
        selector << (
                   not_selector.setParseAction(make_NotSelector) \
                 | list_selector.setParseAction(make_ListSelector) \
                 | source_selector.setParseAction(make_source) \
                 | generic_selector.setParseAction(make_GenericSelector))
        query = pp.ZeroOrMore(selector | term).setParseAction(
                make_Query)
        return query.parseString(self.query)

    @property
    def terms(self):
        return " ".join([str(s) for s in self.ast.terms]).strip()

    @property
    def selectors(self):
        return self.ast.selectors

    @property
    def constraints(self):
        return " ".join([str(s) for s in self.ast.selectors]).strip()

class BasicQueryVisitor(object):
    def __init__(self, query):
        self.query = query
        self.doc = {
            '$text': {
                '$search': ''
            }
        }

    def visit_all(self):
        return self.query.ast.accept(self)
